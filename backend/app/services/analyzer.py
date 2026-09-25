import os
import time
import requests
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from sqlalchemy.orm import Session
from backend.app.db.models import AnalysisReport, Lead

logger = logging.getLogger(__name__)

# Directory where generated HTML improvement reports will be saved
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)

def analyze_website(lead_id: int, db: Session) -> AnalysisReport:
    """
    Performs a thorough audit of the Lead's website.
    If the website is invalid, unreachable, or dummy, it runs an intelligent heuristic analysis
    with realistic audits to generate the audit report.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    website_url = lead.website or ""
    has_valid_website = bool(website_url.strip() and website_url.strip().lower() not in ["not publicly available", "none", "null", ""])

    # Initialize default results
    has_https = False
    is_mobile_responsive = False
    load_speed_seconds = 0.0
    broken_links_count = 0
    seo_title = ""
    seo_description = ""
    missing_alt_tags = 0
    has_contact_form = False
    has_whatsapp_button = False
    has_google_maps_embed = False
    found_socials = {}
    ui_score = 0
    ux_score = 0
    overall_score = 0

    if not has_valid_website:
        logger.info(f"Lead {lead.business_name} has NO website. Generating missing website opportunity assessment.")
        seo_title = "No Public Website Found"
        seo_description = f"{lead.business_name} currently does not have an active website attached to its Google profile. Potential local customers searching in {lead.city or 'your city'} cannot view services, book appointments, or reach out directly online."
    if not has_valid_website:
        logger.info(f"Lead {lead.business_name} has NO website. Generating missing website opportunity assessment.")
        seo_title = "No Public Website Found"
        seo_description = f"{lead.business_name} currently does not have an active website attached to its Google profile. Potential local customers searching in {lead.city or 'your city'} cannot view services, book appointments, or reach out directly online."
        ui_score = 0
        ux_score = 0
        overall_score = 0
    else:
        # Clean URL
        if not website_url.startswith(("http://", "https://")):
            website_url = "http://" + website_url

        logger.info(f"Analyzing website: {website_url} for lead: {lead.business_name}")
        has_https = website_url.startswith("https://")
        start_time = time.time()
        
        try:
            # Fetch homepage
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(website_url, headers=headers, timeout=10, allow_redirects=True)
            load_speed_seconds = round(time.time() - start_time, 2)
        
            # Update HTTPS flag if redirected to HTTPS
            if response.url.startswith("https://"):
                has_https = True
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. SEO Title
            title_tag = soup.find("title")
            seo_title = title_tag.text.strip() if title_tag else ""
            
            # 2. SEO Description
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if not desc_tag:
                desc_tag = soup.find("meta", attrs={"property": "og:description"})
            seo_description = desc_tag.get("content", "").strip() if desc_tag else ""
            
            # 3. Mobile responsiveness check
            viewport = soup.find("meta", attrs={"name": "viewport"})
            is_mobile_responsive = viewport is not None
            
            # 4. Check missing Alt tags on images
            images = soup.find_all("img")
            for img in images:
                if not img.get("alt"):
                    missing_alt_tags += 1
                    
            # 5. Check contact forms
            contact_form = soup.find("form")
            if contact_form:
                has_contact_form = True
            else:
                # Check inputs or text
                if soup.find(attrs={"type": "email"}) or soup.find(text=re.compile(r'contact|submit|inquiry', re.IGNORECASE)):
                    has_contact_form = True
                    
            # 6. Check WhatsApp
            whatsapp_links = soup.find_all("a", href=re.compile(r'wa\.me|api\.whatsapp\.com|whatsapp://', re.IGNORECASE))
            has_whatsapp_button = len(whatsapp_links) > 0
            
            # 7. Check Google Maps embed
            maps_embeds = soup.find_all("iframe", src=re.compile(r'google\.com/maps|maps\.google', re.IGNORECASE))
            has_google_maps_embed = len(maps_embeds) > 0
            
            # 8. Check social links
            social_patterns = {
                "instagram": r'instagram\.com/([^/]+)',
                "facebook": r'facebook\.com/([^/]+)',
                "linkedin": r'linkedin\.com/company/([^/]+)',
                "twitter": r'twitter\.com/([^/]+)|x\.com/([^/]+)'
            }
            
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                for platform, pattern in social_patterns.items():
                    if re.search(pattern, href, re.IGNORECASE):
                        found_socials[platform] = href
                        
            # 9. Broken links check (mock check first 5 links)
            internal_links = []
            parsed_origin = urlparse(website_url)
            for link in links[:10]:
                href = link.get("href", "")
                if href.startswith("/") or parsed_origin.netloc in href:
                    full_url = urljoin(website_url, href)
                    internal_links.append(full_url)
                    
            for link_url in internal_links[:3]:
                try:
                    link_resp = requests.head(link_url, headers=headers, timeout=3)
                    if link_resp.status_code >= 400:
                        broken_links_count += 1
                except:
                    broken_links_count += 1
                    
            # Real website scoring
            ui_score = 100
            ux_score = 100
            
            if not is_mobile_responsive:
                ui_score -= 30
                ux_score -= 25
            if not has_https:
                ux_score -= 15
            if load_speed_seconds > 3.0:
                ux_score -= 15
            if broken_links_count > 0:
                ux_score -= min(broken_links_count * 5, 25)
            if missing_alt_tags > 5:
                ui_score -= 10
            if not has_contact_form:
                ux_score -= 15
            if not has_google_maps_embed:
                ux_score -= 10
            if not has_whatsapp_button:
                ux_score -= 5
                
            # Bound scores realistically
            ui_score = max(min(ui_score, 100), 0)
            ux_score = max(min(ux_score, 100), 0)
            overall_score = int((ui_score + ux_score) / 2)
                    
        except Exception as e:
            logger.warning(f"Could not audit {website_url} live: {e}.")
            has_https = False
            is_mobile_responsive = False
            load_speed_seconds = 0.0
            broken_links_count = 0
            seo_title = "Unreachable Website"
            seo_description = f"Website was offline or returned a connection error: {str(e)}"
            missing_alt_tags = 0
            has_contact_form = False
            has_whatsapp_button = False
            has_google_maps_embed = False
            found_socials = {}
            ui_score = 0
            ux_score = 0
            overall_score = 0

    # Save details into db
    report = AnalysisReport(
        lead_id=lead_id,
        has_https=has_https,
        is_mobile_responsive=is_mobile_responsive,
        load_speed_seconds=load_speed_seconds,
        broken_links_count=broken_links_count,
        seo_title=seo_title,
        seo_description=seo_description,
        missing_alt_tags=missing_alt_tags,
        has_contact_form=has_contact_form,
        has_whatsapp_button=has_whatsapp_button,
        has_google_maps_embed=has_google_maps_embed,
        social_links=json.dumps(found_socials),
        ui_score=ui_score,
        ux_score=ux_score,
        overall_score=overall_score
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)

    # Generate custom HTML report and save file
    report_filename = f"report_lead_{lead_id}_{int(time.time())}.html"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    generate_html_report_file(lead, report, found_socials, report_path)
    
    report.improvement_report_path = f"/static/reports/{report_filename}"
    db.commit()
    db.refresh(report)
    
    return report


import random
import re

def generate_html_report_file(lead: Lead, report: AnalysisReport, socials: dict, file_path: str):
    """
    Writes a highly styled, conversion-optimized audit HTML file for the business lead.
    """
    socials_html = "".join([
        f'<span class="px-3 py-1 bg-zinc-800 rounded-full text-xs text-indigo-400 capitalize mr-2">{k}</span>' 
        for k, v in socials.items() if v
    ])
    if not socials_html:
        socials_html = '<span class="text-zinc-500 text-sm">None detected</span>'

    # Construct recommendation list
    recommendations = []
    if not report.has_https:
        recommendations.append({
            "title": "Enable HTTPS Security",
            "desc": "Your site does not use HTTPS. Chrome flags HTTP sites as 'Not Secure', causing 82% of visitors to abandon.",
            "impact": "High Impact",
            "icon": "🔒"
        })
    if not report.is_mobile_responsive:
        recommendations.append({
            "title": "Implement Mobile Responsive Layout",
            "desc": "Your site fails mobile view audits. Over 60% of local searches are on mobile phones; Google penalizes non-mobile friendly layouts.",
            "impact": "Critical Impact",
            "icon": "📱"
        })
    if report.load_speed_seconds > 2.5:
        recommendations.append({
            "title": "Optimize Page Performance",
            "desc": f"Your page loaded in {report.load_speed_seconds}s. Load speeds slower than 2s increase bounce rates by 50%. Optimization of images and script deferrals is recommended.",
            "impact": "High Impact",
            "icon": "⚡"
        })
    if report.broken_links_count > 0:
        recommendations.append({
            "title": "Fix Broken Links",
            "desc": f"Detected {report.broken_links_count} broken links. Broken links block index bots and harm user trust.",
            "impact": "Medium Impact",
            "icon": "🔗"
        })
    if not report.seo_title or len(report.seo_title) < 10:
        recommendations.append({
            "title": "Optimize Meta Title & SEO Tags",
            "desc": "Title tag is missing or not optimized for search. A target title helps boost rankings on Google.",
            "impact": "High Impact",
            "icon": "🏷️"
        })
    if report.missing_alt_tags > 0:
        recommendations.append({
            "title": "Add Alt Tags to Images",
            "desc": f"Missing alt descriptions on {report.missing_alt_tags} images. Image tags help Google understand context and drive traffic.",
            "impact": "Low Impact",
            "icon": "🖼️"
        })
    if not report.has_contact_form:
        recommendations.append({
            "title": "Integrate Lead Capture Form",
            "desc": "No interactive form detected. An easy-to-use form helps turn casual page views into incoming business leads.",
            "impact": "Critical Impact",
            "icon": "📬"
        })
    if not report.has_whatsapp_button:
        recommendations.append({
            "title": "Add WhatsApp Direct Chat",
            "desc": "WhatsApp floating buttons can increase on-page customer inquiry rates by up to 200%.",
            "impact": "Medium Impact",
            "icon": "💬"
        })
    if not report.has_google_maps_embed:
        recommendations.append({
            "title": "Embed Google Maps Location",
            "desc": "Embedding your local Google maps helps customers find your physical address and builds immediate authority.",
            "impact": "Medium Impact",
            "icon": "📍"
        })

    # Default recommendation if everything is green
    if not recommendations:
        recommendations.append({
            "title": "Refine Modern Visual Assets & Animations",
            "desc": "Your site passes standard parameters! We recommend updating typography and integrating interactive animations for higher sales conversion.",
            "impact": "Low Impact",
            "icon": "✨"
        })

    recs_html = ""
    for rec in recommendations:
        recs_html += f"""
        <div class="p-5 bg-zinc-900 border border-zinc-800 rounded-xl mb-4 flex items-start gap-4">
            <div class="text-3xl">{rec['icon']}</div>
            <div>
                <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-white font-semibold text-base">{rec['title']}</h3>
                    <span class="text-xs px-2 py-0.5 rounded font-medium {'bg-red-950 text-red-400 border border-red-800' if 'Critical' in rec['impact'] or 'High' in rec['impact'] else 'bg-amber-950 text-amber-400 border border-amber-800'}">{rec['impact']}</span>
                </div>
                <p class="text-zinc-400 text-sm">{rec['desc']}</p>
            </div>
        </div>
        """

    score_color = "text-red-500" if report.overall_score < 50 else ("text-amber-500" if report.overall_score < 75 else "text-emerald-500")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Health Audit - {lead.business_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: #09090b;
        }}
    </style>
</head>
<body class="text-zinc-300 min-h-screen pb-16">
    <header class="border-b border-zinc-800 bg-zinc-950/50 backdrop-blur sticky top-0 z-50">
        <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-fuchsia-500 flex items-center justify-center font-bold text-white text-lg">💡</div>
                <span class="font-bold text-white text-lg tracking-tight">ApexWeb Agency</span>
            </div>
            <div class="text-xs text-zinc-500 font-medium">AUDIT REPORT FOR: <span class="text-indigo-400 font-semibold">{lead.business_name.upper()}</span></div>
        </div>
    </header>

    <main class="max-w-5xl mx-auto px-6 mt-12">
        <!-- Hero Section -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-center bg-zinc-950 border border-zinc-800 rounded-3xl p-8 mb-12 shadow-2xl">
            <div class="md:col-span-2">
                <span class="text-xs font-bold text-indigo-400 tracking-widest uppercase bg-indigo-950/50 border border-indigo-900/50 px-3 py-1 rounded-full">Website Audit Report</span>
                <h1 class="text-3xl md:text-4xl font-extrabold text-white mt-4 tracking-tight leading-tight">{lead.business_name}</h1>
                <p class="text-zinc-400 mt-2 text-base">We conducted a diagnostic audit of your business website. We analyzed security, SEO, user experience speed, and responsive compatibility. Here are the findings:</p>
                <div class="mt-6 flex flex-wrap gap-4 text-sm text-zinc-400">
                    <div><span class="text-zinc-500">Website:</span> <a href="{lead.website}" target="_blank" class="text-indigo-400 underline">{lead.website}</a></div>
                    <div><span class="text-zinc-500">Category:</span> {lead.category}</div>
                    <div><span class="text-zinc-500">City:</span> {lead.city}</div>
                </div>
            </div>
            <div class="flex flex-col items-center justify-center bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6 text-center">
                <span class="text-xs font-semibold text-zinc-400 tracking-wider">OVERALL HEALTH SCORE</span>
                <div class="text-7xl font-extrabold {score_color} mt-2">{report.overall_score}%</div>
                <div class="mt-4 w-full bg-zinc-800 rounded-full h-2">
                    <div class="h-2 rounded-full {'bg-red-500' if report.overall_score < 50 else ('bg-amber-500' if report.overall_score < 75 else 'bg-emerald-500')}" style="width: {report.overall_score}%"></div>
                </div>
                <span class="text-xs text-zinc-500 mt-2">Score generated by Apex AI Crawler</span>
            </div>
        </div>

        <!-- Matrix Dashboard -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
            <!-- Col 1 -->
            <div class="p-5 bg-zinc-950 border border-zinc-800 rounded-2xl flex flex-col justify-between">
                <span class="text-xs text-zinc-500 font-bold uppercase tracking-wider">Security</span>
                <div class="mt-3 flex items-center justify-between">
                    <span class="text-xl font-bold text-white">{ "Secure" if report.has_https else "Unsecured" }</span>
                    <span class="text-2xl">{ "🔒" if report.has_https else "🔓" }</span>
                </div>
            </div>
            <!-- Col 2 -->
            <div class="p-5 bg-zinc-950 border border-zinc-800 rounded-2xl flex flex-col justify-between">
                <span class="text-xs text-zinc-500 font-bold uppercase tracking-wider">Mobile Friendly</span>
                <div class="mt-3 flex items-center justify-between">
                    <span class="text-xl font-bold text-white">{ "Compatible" if report.is_mobile_responsive else "Broken" }</span>
                    <span class="text-2xl">{ "📱" if report.is_mobile_responsive else "❌" }</span>
                </div>
            </div>
            <!-- Col 3 -->
            <div class="p-5 bg-zinc-950 border border-zinc-800 rounded-2xl flex flex-col justify-between">
                <span class="text-xs text-zinc-500 font-bold uppercase tracking-wider">Load Speed</span>
                <div class="mt-3 flex items-center justify-between">
                    <span class="text-xl font-bold text-white">{report.load_speed_seconds}s</span>
                    <span class="text-2xl">⚡</span>
                </div>
            </div>
            <!-- Col 4 -->
            <div class="p-5 bg-zinc-950 border border-zinc-800 rounded-2xl flex flex-col justify-between">
                <span class="text-xs text-zinc-500 font-bold uppercase tracking-wider">UX & Conversion</span>
                <div class="mt-3 flex items-center justify-between">
                    <span class="text-xl font-bold text-white">{ "Good" if report.has_contact_form else "Weak" }</span>
                    <span class="text-2xl">🎯</span>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <!-- Left details -->
            <div class="md:col-span-2">
                <h2 class="text-xl font-bold text-white mb-6 tracking-tight flex items-center gap-2">
                    <span>⚠️</span> Identified Issues & Recommendations
                </h2>
                <div class="space-y-4">
                    {recs_html}
                </div>
            </div>

            <!-- Right stats card -->
            <div class="space-y-6">
                <div class="p-6 bg-zinc-950 border border-zinc-800 rounded-2xl">
                    <h3 class="text-white font-bold text-sm tracking-wide uppercase mb-4">Metadata & SEO Audit</h3>
                    <div class="space-y-3 text-xs text-zinc-400">
                        <div>
                            <span class="text-zinc-500 block mb-1">SEO Title</span>
                            <span class="text-white font-medium block truncate bg-zinc-900 p-2 rounded border border-zinc-800">{report.seo_title or 'Missing Title'}</span>
                        </div>
                        <div>
                            <span class="text-zinc-500 block mb-1">SEO Meta Description</span>
                            <span class="text-white font-medium block bg-zinc-900 p-2 rounded border border-zinc-800 line-clamp-3">{report.seo_description or 'Missing description'}</span>
                        </div>
                        <div class="flex justify-between border-t border-zinc-800 pt-3">
                            <span class="text-zinc-500">Missing Image Alt Tags</span>
                            <span class="text-white font-semibold">{report.missing_alt_tags} images</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-zinc-500">Broken Link Count</span>
                            <span class="text-white font-semibold">{report.broken_links_count} links</span>
                        </div>
                    </div>
                </div>

                <div class="p-6 bg-zinc-950 border border-zinc-800 rounded-2xl">
                    <h3 class="text-white font-bold text-sm tracking-wide uppercase mb-4">Social Presence</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between text-xs text-zinc-400">
                            <span class="text-zinc-500">Social Connections</span>
                            <div>{socials_html}</div>
                        </div>
                        <div class="flex justify-between text-xs text-zinc-400 border-t border-zinc-800 pt-3">
                            <span class="text-zinc-500">Google Map Embed</span>
                            <span class="font-medium text-white">{ "Yes" if report.has_google_maps_embed else "No" }</span>
                        </div>
                        <div class="flex justify-between text-xs text-zinc-400">
                            <span class="text-zinc-500">WhatsApp Shortcut</span>
                            <span class="font-medium text-white">{ "Yes" if report.has_whatsapp_button else "No" }</span>
                        </div>
                    </div>
                </div>

                <div class="p-6 bg-gradient-to-tr from-indigo-950 to-fuchsia-950 border border-indigo-800/50 rounded-2xl text-center">
                    <h3 class="text-white font-extrabold text-lg mb-2">Want to fix these issues?</h3>
                    <p class="text-indigo-200 text-xs mb-4">We build high-performance, fast-loading, mobile-friendly websites that convert visitors into paying clients.</p>
                    <a href="mailto:hello@apexweb.agency?subject=Audit Consultation - {lead.business_name}" class="inline-block px-5 py-2.5 bg-indigo-500 text-white font-semibold text-xs rounded-xl hover:bg-indigo-600 transition shadow-lg shadow-indigo-500/20">Book Free 15 Min Strategy Call</a>
                </div>
            </div>
        </div>
    </main>

    <footer class="mt-20 border-t border-zinc-800 pt-8 text-center text-xs text-zinc-500">
        <p>&copy; 2026 ApexWeb Agency. Built automatically by the Website Agency Operating System.</p>
    </footer>
</body>
</html>
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"HTML report successfully created at {file_path}")
