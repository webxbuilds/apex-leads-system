import os
import json
import logging
import random
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import google.generativeai as genai
from backend.app.db.models import Lead, AnalysisReport, AIQualification, OutreachMessage

logger = logging.getLogger(__name__)

# Config Gemini API
DEFAULT_GEMINI_API_KEY = "AIzaSyC1Ov8t1nRxizCotD-I9xglDeZDkhIdYVI"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", DEFAULT_GEMINI_API_KEY)

def configure_gemini() -> bool:
    key = os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
    if key:
        try:
            genai.configure(api_key=key)
            return True
        except Exception as e:
            logger.warning(f"Gemini configuration error: {e}")
            return False
    return False

# Initialize on module load
configure_gemini()

def get_gemini_model():
    """
    Returns an active Gemini model with graceful fallback across versions.
    """
    if not configure_gemini():
        return None
    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
        try:
            return genai.GenerativeModel(model_name)
        except Exception as e:
            logger.debug(f"Model {model_name} unavailable: {e}")
            continue
    return None


def qualify_lead(lead_id: int, db: Session) -> AIQualification:
    """
    Module 3: AI Audit & Scoring
    Scores lead conversion probability and outputs detailed Opportunity metrics and suggestions.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead_id).order_by(AnalysisReport.created_at.desc()).first()
    website_score = report.overall_score if report else 0
    has_website = bool(lead.website and lead.website not in ["Not Publicly Available", "none", "null", ""])
    
    prompt = f"""
    You are an AI Sales Strategist evaluating a local business lead for custom website design packages.
    Compute lead intent scoring based on these parameters:
    Name: {lead.business_name}
    Category: {lead.category}
    City: {lead.city}
    Website Status: {"HAS WEBSITE: " + str(lead.website) if has_website else "NO WEBSITE YET (Prime opportunity to build their first digital storefront & capture local search market)"}
    Web Audit Score: {website_score if has_website else 0}/100
    Google Rating: {lead.google_rating or 'N/A'}★ ({lead.reviews_count or 0} reviews)
    HTTPS Enabled: {report.has_https if report else ('N/A' if has_website else 'No Website')}
    Mobile Responsive: {report.is_mobile_responsive if report else ('N/A' if has_website else 'No Website')}
    Load Speed: {report.load_speed_seconds if report else 'N/A'} seconds
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "ai_score": "Hot" | "Warm" | "Cold",
        "reason": "Detailed professional reasoning containing Opportunity Score and Sales Suggestions. Use Markdown structure.",
        "closing_probability": 0.0 to 1.0
    }}
    """
    
    ai_score = "Warm"
    reason = "Fallback rule-based assessment."
    closing_probability = 0.50

    model = get_gemini_model()
    if model:
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            ai_score = data.get("ai_score", "Warm")
            reason = data.get("reason", "")
            closing_probability = float(data.get("closing_probability", 0.50))
        except Exception as e:
            logger.error(f"Gemini API qualification error: {e}. Falling back to rule engine.")
            ai_score, reason, closing_probability = _rule_based_qualification(lead, report)
    else:
        ai_score, reason, closing_probability = _rule_based_qualification(lead, report)

    # Save to db
    qualification = AIQualification(
        lead_id=lead_id,
        ai_score=ai_score,
        reason=reason,
        closing_probability=closing_probability
    )
    db.add(qualification)
    db.commit()
    db.refresh(qualification)
    
    return qualification


def _rule_based_qualification(lead: Lead, report: AnalysisReport) -> tuple:
    """
    Robust rule-based scoring engine for fallback.
    """
    if not lead.website or lead.website == "Not Publicly Available":
        score = "Hot"
        prob = 0.85
        reason = f"""### Opportunity Score: 85/100
- **High Intent Category**: {lead.business_name} has a strong listing but lacks a website. In {lead.city}, competitors in the {lead.category} category with websites are capturing the search share.
- **Immediate Value**: Pitch a customized mockup site prototype link.

### Sales Suggestions:
1. Call referencing their rating ({lead.google_rating or 4.0}/5).
2. Offer 1-click domain setup and 48h deployment.
"""
    elif report:
        if report.overall_score < 50:
            score = "Hot"
            prob = 0.75
            reason = f"""### Opportunity Score: 75/100
- **Critical Issues Detected**: Website is severely outdated (Overall: {report.overall_score}%). It is not mobile responsive and lacks SSL security.
- **Conversion Potential**: High. Mobile users cannot use the website effectively.

### Sales Suggestions:
1. Highlight that Google flags their site as "Insecure" to mobile visitors.
2. Share the redesigned responsive prototype.
"""
        elif report.overall_score < 75:
            score = "Warm"
            prob = 0.55
            reason = f"""### Opportunity Score: 55/100
- **Optimization Gaps**: Website exists but has speed issues ({report.load_speed_seconds}s) and lacks instant contact tools (e.g. WhatsApp floats).
- **Conversion Potential**: Moderate. Focus sales talk on lead-capture integrations.

### Sales Suggestions:
1. Pitch floating booking buttons and widget integrations.
2. Show speed acceleration metrics.
"""
        else:
            score = "Cold"
            prob = 0.25
            reason = f"""### Opportunity Score: 25/100
- **Low Priority**: Website is already well optimized (Score: {report.overall_score}%).
- **Pitch Focus**: Pitch advanced SEO campaigns or custom web apps.

### Sales Suggestions:
1. Do not pitch standard rebuilds. Offer speed audits or specialized automation APIs instead.
"""
    else:
        score = "Warm"
        prob = 0.45
        reason = f"""### Opportunity Score: 45/100
- **Basic Listing**: Standard profile with moderate ratings ({lead.google_rating or 4.0}/5).
- **Pitch Focus**: Initial outreach recommended to introduce our design portfolios.

### Sales Suggestions:
1. Share industry-specific design templates.
"""
        
    return score, reason, prob


def generate_outreach_materials(lead_id: int, db: Session) -> OutreachMessage:
    """
    Tailored 3-Step Outreach Engine:
    Step 1: Authentic Positive Hook / Specific Praise
    Step 2: Diagnosis of a Specific Problem / Revenue Leak (Missing Website vs Broken Site)
    Step 3: Tangible Solution / Low-Friction Offer (Demo / Prototype)
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead_id).order_by(AnalysisReport.created_at.desc()).first()

    # Detect exact specific problem for this lead
    has_website = bool(lead.website and lead.website not in ["Not Publicly Available", "none", "null", ""])
    problem_type = "missing_website"
    problem_details = {}

    if not has_website:
        problem_type = "missing_website"
    elif report:
        if not report.has_https:
            problem_type = "no_ssl"
        elif not report.is_mobile_responsive:
            problem_type = "mobile_broken"
        elif report.load_speed_seconds and report.load_speed_seconds > 2.5:
            problem_type = "slow_speed"
            problem_details["speed"] = f"{report.load_speed_seconds:.1f}s"
        elif report.ui_score and report.ui_score < 45:
            problem_type = "outdated_design"
            problem_details["ui_score"] = report.ui_score
        elif not report.has_whatsapp_button or not report.has_contact_form:
            problem_type = "no_lead_capture"
        else:
            problem_type = "redesign_conversion"
    else:
        problem_type = "missing_website" if not has_website else "mobile_broken"

    owner = lead.owner_name if lead.owner_name and lead.owner_name != "Not Publicly Available" else ""
    niche = lead.category or "Local Business"
    city = lead.city or "your area"
    rating = f"{lead.google_rating:.1f}" if lead.google_rating else "4.8"
    reviews = lead.reviews_count if lead.reviews_count else 35
    
    # Extract neighborhood / area from address for hyper-local personalization
    neighborhood = ""
    if lead.address and lead.address != "Not Publicly Available":
        addr_parts = [p.strip() for p in lead.address.split(",")]
        if len(addr_parts) >= 2:
            neighborhood = addr_parts[0]

    email_subject = None
    email_content = None
    whatsapp_message = None
    linkedin_message = None
    instagram_dm = None
    cold_call_script = None

    # 1. Attempt Gemini AI Generation with specialized prompt
    model = get_gemini_model()
    if model:
        try:
            website_ctx = "HAS NO WEBSITE YET (Target: Pitch building their first modern digital storefront with instant WhatsApp booking to capture 70%+ of mobile searches leaking to local competitors)." if not has_website else f"HAS WEBSITE ({lead.website}) with diagnosis: {problem_type}."
            ai_prompt = f"""
You are an elite B2B Sales Strategist & Copywriter for a digital agency.
Write high-converting, personalized outreach materials for:
- Business: {lead.business_name}
- Decision Maker / Contact: {owner or 'Owner/Director'}
- Industry Niche: {niche}
- City & Area: {city} {neighborhood}
- Local Rating: {rating}★ ({reviews}+ Google reviews)
- Status: {website_ctx}

Follow this strict 3-step conversion psychology:
1. Authentic positive hook (praising their {rating}★ rating and customer loyalty).
2. Clear diagnosis of their revenue leak (Explain why not having a website or having a broken site loses 10-15 customers/week in {city}).
3. Zero-pressure value offer: Mention that we already built a live interactive website prototype with 1-click WhatsApp booking specifically customized for {lead.business_name}, and ask if they'd like a 45-second preview link.

OUTPUT FORMAT (JSON ONLY):
{{
    "email_subject": "Catchy, low-pressure email subject line",
    "email_content": "Full formatted email body with line breaks",
    "whatsapp_message": "Punchy WhatsApp message with emojis & *bold* highlights",
    "linkedin_message": "Professional LinkedIn message",
    "instagram_dm": "Friendly Instagram DM with emojis",
    "cold_call_script": "3-step cold call phone script with objection handling"
}}
"""
            resp = model.generate_content(
                ai_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(resp.text.strip())
            email_subject = data.get("email_subject")
            email_content = data.get("email_content")
            whatsapp_message = data.get("whatsapp_message")
            linkedin_message = data.get("linkedin_message")
            instagram_dm = data.get("instagram_dm")
            cold_call_script = data.get("cold_call_script")
        except Exception as e:
            logger.warning(f"Gemini outreach generation error: {e}. Falling back to 3-part engine.")

    # 2. Fallback to rule engine if Gemini didn't complete all fields
    if not (email_subject and email_content and whatsapp_message):
        r_subject, r_email, r_wa, r_li, r_ig, r_call = _craft_3part_outreach(
            lead=lead,
            owner=owner,
            niche=niche,
            city=city,
            rating=rating,
            reviews=reviews,
            problem_type=problem_type,
            problem_details=problem_details,
            neighborhood=neighborhood
        )
        email_subject = email_subject or r_subject
        email_content = email_content or r_email
        whatsapp_message = whatsapp_message or r_wa
        linkedin_message = linkedin_message or r_li
        instagram_dm = instagram_dm or r_ig
        cold_call_script = cold_call_script or r_call

    # Save to database
    outreach = db.query(OutreachMessage).filter(OutreachMessage.lead_id == lead_id).order_by(OutreachMessage.created_at.desc()).first()
    if outreach:
        outreach.email_subject = email_subject
        outreach.email_content = email_content
        outreach.whatsapp_message = whatsapp_message
        outreach.linkedin_message = linkedin_message
        outreach.instagram_dm = instagram_dm
        outreach.cold_call_script = cold_call_script
        outreach.created_at = datetime.now(timezone.utc)
    else:
        outreach = OutreachMessage(
            lead_id=lead_id,
            email_subject=email_subject,
            email_content=email_content,
            whatsapp_message=whatsapp_message,
            linkedin_message=linkedin_message,
            instagram_dm=instagram_dm,
            cold_call_script=cold_call_script
        )
        db.add(outreach)
        
    db.commit()
    db.refresh(outreach)

    return outreach


def generate_custom_ai_pitch(lead_id: int, channel: str, custom_instructions: str, db: Session) -> dict:
    """
    On-demand Gemini Custom Pitch Generator for specific angles or channels.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    has_website = bool(lead.website and lead.website not in ["Not Publicly Available", "none", "null", ""])
    model = get_gemini_model()
    
    prompt = f"""
    You are an expert sales copywriter.
    Write a customized outreach pitch for:
    - Business: {lead.business_name}
    - Niche: {lead.category or 'Local Business'}
    - City: {lead.city or 'Local'}
    - Google Rating: {lead.google_rating or 'N/A'}★
    - Website: {lead.website if has_website else 'NO WEBSITE YET (wants to pitch first website launch)'}
    - Channel Target: {channel}
    - Specific Instructions: {custom_instructions or 'Create high-converting message offering demo prototype link'}

    Return format JSON:
    {{
        "subject": "subject line if applicable or short title",
        "message": "complete formatted message ready to send",
        "channel": "{channel}"
    }}
    """
    if model:
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(resp.text.strip())
        except Exception as e:
            logger.error(f"Gemini custom pitch error: {e}")
            
    # Fallback
    fallback_msg = f"Hi {lead.owner_name or lead.business_name} team,\n\nI noticed your amazing {lead.google_rating or 4.8}★ reputation in {lead.city or 'your city'}."
    if not has_website:
        fallback_msg += f" We noticed you don't have a website yet, so we created a live demo prototype for {lead.business_name} with instant WhatsApp booking.\n\nCan I send over the preview link?"
    else:
        fallback_msg += f" We designed a fast-loading modern demo for {lead.business_name}.\n\nWould you like a quick preview link?"
        
    return {
        "subject": f"Website Prototype for {lead.business_name}",
        "message": fallback_msg,
        "channel": channel
    }


# ─── Niche-specific hook libraries ────────────────────────────────────────────
_NICHE_HOOKS_EMAIL = {
    "Gym": [
        "I came across {biz} while researching the best fitness centers in {city}. Your {rating}★ rating from {reviews}+ members is exceptional — building that level of client loyalty in the fitness industry is genuinely impressive.",
        "I noticed {biz} stands out as one of the top-rated gyms in {city} with {rating}★ across {reviews}+ reviews. The dedication your team puts into member experience clearly shows.",
        "I was looking at the fitness landscape in {city} and {biz}'s {rating}★ reputation ({reviews}+ reviews) immediately caught my eye. Maintaining that caliber of member satisfaction is no small feat."
    ],
    "Restaurant": [
        "I discovered {biz} while exploring the top dining spots in {city}. Your {rating}★ rating across {reviews}+ reviews is remarkable — it's clear you've created a dining experience people genuinely love and keep coming back to.",
        "I was researching popular restaurants in {city} and {biz}'s stellar {rating}★ rating ({reviews}+ reviews) really stood out. Building that kind of word-of-mouth loyalty in the F&B space takes incredible dedication.",
        "I came across {biz} while mapping the best food destinations in {city}. Your {rating}★ reputation from {reviews}+ happy diners says everything about the quality you deliver."
    ],
    "Salon": [
        "I noticed {biz} while searching for the most trusted beauty and wellness studios in {city}. Your {rating}★ rating from {reviews}+ clients is phenomenal — earning that kind of trust in personal grooming is truly impressive.",
        "I was researching top-rated salons in {city} and {biz}'s {rating}★ reputation across {reviews}+ client reviews immediately caught my attention. Your consistency in quality is remarkable."
    ],
    "Dentist": [
        "I came across {biz} while looking for the highest-rated dental practices in {city}. A {rating}★ rating across {reviews}+ patient reviews in healthcare is exceptional — patients clearly trust your team deeply.",
        "I was researching dental care providers in {city} and {biz}'s outstanding {rating}★ rating from {reviews}+ patients really stood out. Building that level of patient confidence is remarkable."
    ],
    "Clinic": [
        "I noticed {biz} while researching trusted healthcare providers in {city}. Your {rating}★ rating from {reviews}+ patients speaks volumes about the quality of care your practice delivers.",
        "I came across {biz}'s exceptional {rating}★ reputation ({reviews}+ reviews) while mapping the top clinics in {city}. Patient trust at that level is genuinely earned."
    ],
    "School": [
        "I discovered {biz} while researching the most well-regarded educational institutions in {city}. Your {rating}★ rating from {reviews}+ parents and students is outstanding — building that community trust takes real dedication.",
        "I noticed {biz} consistently ranks among the top-rated schools in {city} with a {rating}★ reputation ({reviews}+ reviews). The educational environment you've cultivated clearly resonates with families."
    ],
    "Real Estate": [
        "I came across {biz} while researching the most reputable real estate firms in {city}. A {rating}★ rating from {reviews}+ clients in such a competitive market is truly outstanding.",
        "I noticed {biz}'s stellar {rating}★ reputation across {reviews}+ client reviews while mapping the top real estate brands in {city}. That level of client satisfaction in property is impressive."
    ],
    "Hospital": [
        "I discovered {biz} while researching the most trusted healthcare facilities in {city}. Your {rating}★ rating from {reviews}+ patients is exceptional — maintaining that standard of care and trust is remarkable.",
    ],
    "Lawyer": [
        "I came across {biz} while looking for the highest-rated legal practices in {city}. A {rating}★ reputation from {reviews}+ clients in the legal field is outstanding — it clearly reflects the trust and outcomes you deliver.",
    ],
}

_NICHE_HOOKS_WA = {
    "Gym": [
        "Massive respect for what you've built at *{biz}* in {city} — *{rating}★ from {reviews}+ members* is seriously impressive in the fitness space! 💪",
        "Loved seeing *{biz}* rated *{rating}★ ({reviews}+ reviews)* in {city}! That member loyalty is 🔥"
    ],
    "Restaurant": [
        "Your food game at *{biz}* in {city} is clearly legendary — *{rating}★ from {reviews}+ diners* doesn't lie! 🍽️",
        "Huge respect for *{biz}*'s *{rating}★ reputation* across *{reviews}+* local food lovers in {city}! 🎉"
    ],
    "Salon": [
        "Loved seeing the amazing reviews for *{biz}* in {city} — *{rating}★ from {reviews}+ clients* is outstanding! ✨",
    ],
    "Dentist": [
        "Seeing *{biz}* rated *{rating}★ by {reviews}+ patients* in {city} is phenomenal — that kind of patient trust is rare! 🦷",
    ],
}

_NICHE_HOOKS_INSTAGRAM = {
    "Gym": "Your gym's energy is 🔥! {rating}★ from {reviews}+ members in {city} — that kind of loyalty is EARNED, not bought.",
    "Restaurant": "Your food aesthetic is incredible! {rating}★ across {reviews}+ reviews in {city} 🍽️ — clearly a local favorite.",
    "Salon": "Love the transformations on your feed! {rating}★ from {reviews}+ clients in {city} ✨ — stunning work.",
    "Dentist": "Your practice is clearly one of the most trusted in {city}! {rating}★ from {reviews}+ patients 🦷 — that's incredible.",
    "Clinic": "Your practice's reputation is phenomenal — {rating}★ across {reviews}+ patients in {city}. That trust is hard-earned!",
    "School": "Love what {biz} is doing for education in {city}! {rating}★ from {reviews}+ families 📚 — impressive commitment.",
    "Real Estate": "Your portfolio in {city} is impressive! {rating}★ from {reviews}+ clients 🏠 — clearly a trusted name.",
}


def _craft_3part_outreach(lead: Lead, owner: str, niche: str, city: str, rating: str, reviews: int, problem_type: str, problem_details: dict, neighborhood: str = "") -> tuple:
    """
    Builds personalized, high-converting copy strictly adhering to:
    [1] POSITIVE HOOK -> [2] SPECIFIC PROBLEM -> [3] TAILORED SOLUTION & LOW-PRESSURE CTA
    
    Each message is unique per lead using niche-specific templates,
    neighborhood-level personalization, and problem-aware solution framing.
    """
    random.seed(lead.id + 739)
    
    target_name = owner if owner else lead.business_name
    greeting_email = f"Hi {owner}," if owner else f"Hi {lead.business_name} Team,"
    greeting_wa = f"Hi {owner} 👋" if owner else f"Hi {lead.business_name} team 👋"
    
    # Neighborhood reference for hyper-local feel
    local_ref = f" in the {neighborhood} area" if neighborhood else ""
    local_ref_short = f" ({neighborhood})" if neighborhood else ""

    # ── 1. POSITIVE HOOK / SINCERE PRAISE ─────────────────────────────────────
    
    # Pick niche-specific hooks, falling back to generic
    niche_hooks = _NICHE_HOOKS_EMAIL.get(niche, [])
    generic_hooks = [
        f"I came across {lead.business_name} while searching for top-rated {niche}s in {city}. Your {rating}★ rating across {reviews}+ customer reviews is outstanding — it's clear you've built tremendous local loyalty.",
        f"I noticed {lead.business_name} consistently ranks among the most reputable {niche}s in {city} with a stellar {rating}★ rating ({reviews}+ reviews). Huge congratulations on the reputation you've established.",
        f"I was researching established {niche} businesses in {city}{local_ref} and was really impressed by {lead.business_name}'s track record — your {rating}★ rating from {reviews}+ local customers speaks volumes."
    ]
    hooks_email = [h.format(biz=lead.business_name, rating=rating, reviews=reviews, city=city) for h in niche_hooks] if niche_hooks else generic_hooks
    positive_hook = random.choice(hooks_email)

    niche_hooks_wa = _NICHE_HOOKS_WA.get(niche, [])
    generic_hooks_wa = [
        f"Loved seeing your stellar *{rating}★ rating ({reviews}+ reviews)* for *{lead.business_name}* in {city}!",
        f"Huge respect on building such a strong reputation for *{lead.business_name}* in {city} ({rating}★ from {reviews}+ local reviews)!"
    ]
    hooks_wa = [h.format(biz=lead.business_name, rating=rating, reviews=reviews, city=city) for h in niche_hooks_wa] if niche_hooks_wa else generic_hooks_wa
    positive_hook_wa = random.choice(hooks_wa)

    # ── 2. SPECIFIC PROBLEM & REVENUE IMPACT ──────────────────────────────────
    
    if problem_type == "missing_website":
        problem_email = f"However, when prospective clients find you on Google Maps, there's no website or menu/service link attached to your profile. In {city}, over 70% of high-intent customers want to view pricing, photos, or book online before visiting — and without a direct link, they often click over to competitors who have instant booking pages."
        problem_wa = f"I noticed you don't currently have a *website or online booking link* attached to your Google profile. When local clients search for {niche}s in {city} on their phones, they can't view your services directly, which causes high-value customer inquiries to leak to competitors."
        problem_call = f"I noticed on your Google profile that there's no website or direct booking link attached. When local customers look up {niche}s in {city} on their phone, not having an instant link makes it easy for them to jump to competitors."
        problem_ig = f"I noticed your Google Maps profile doesn't have a website or booking link yet. In {city}, that means local searchers can't instantly check your services — and they often click competitors instead."
        problem_li = f"your Google Maps profile currently doesn't have a website or direct booking link attached. Research shows over 70% of local customers in {city} check online before visiting, meaning those potential clients are likely clicking through to competitors."
    elif problem_type == "no_ssl":
        problem_email = f"However, when I visited your website, Google Chrome and Safari immediately display an alarming 'Not Secure' warning because HTTPS isn't configured. Studies show that over 60% of first-time visitors immediately leave a site when they see security warnings, costing you qualified leads every week."
        problem_wa = f"I checked your website on mobile and noticed browsers are displaying a *'Not Secure / HTTP'* warning to visitors. This usually scares off 50%+ of potential clients before they even read your services."
        problem_call = f"I visited your website and noticed browsers are flagging it with a 'Not Secure' warning because SSL isn't set up. That tends to turn away potential clients who visit from their phones."
        problem_ig = f"I checked your website and noticed Chrome shows a 'Not Secure' ⚠️ warning to all visitors. That warning alone causes 60%+ of potential clients to bounce before they even see your services."
        problem_li = f"your website currently shows a 'Not Secure' warning in browsers because HTTPS isn't configured. Studies show over 60% of first-time visitors leave immediately when they see security warnings — that's qualified leads lost every single week."
    elif problem_type == "mobile_broken":
        problem_email = f"However, when opening your website on a mobile device, the layout is not responsive — text overlaps and users have to pinch-to-zoom to find contact info. Since over 65% of local searches in {city} happen on smartphones, this friction causes potential clients to bounce within 5 seconds."
        problem_wa = f"I opened your site on mobile and noticed the layout doesn't adapt to phone screens, making it difficult for smartphone users to navigate or tap your contact details."
        problem_call = f"I checked your site on an iPhone and noticed the layout isn't mobile-friendly. Visitors have to pinch and zoom to find your contact details, which makes most mobile users bounce."
        problem_ig = f"Opened your site on mobile and the layout breaks a bit — text overlaps and it's hard to find the contact button. Since 65%+ of local searches in {city} are mobile, that's a lot of lost leads 📱"
        problem_li = f"your website layout isn't mobile-responsive — text overlaps and visitors need to pinch-to-zoom to find contact info. Since over 65% of local searches in {city} happen on smartphones, this friction causes potential clients to bounce within seconds."
    elif problem_type == "slow_speed":
        speed_val = problem_details.get("speed", "3.4s")
        problem_email = f"However, your homepage currently takes {speed_val} to load on standard 4G mobile connections. Google data shows that 53% of mobile visits are abandoned if a page takes over 2.5 seconds to load, meaning you're losing warm traffic before they even see your offerings."
        problem_wa = f"I ran a quick mobile speed test on your site and noticed it takes *{speed_val}* to load on 4G. Slow mobile load times are one of the main reasons visitors bounce before calling or booking."
        problem_call = f"I noticed your website is taking over 3 seconds to load on mobile connections, which causes a lot of mobile visitors to back out before they see your phone number."
        problem_ig = f"Ran a quick speed test on your site — it loads in {speed_val} on mobile 4G. Google says 53% of visitors leave if a page takes over 2.5s. You're losing warm leads before they even see your menu/services 📉"
        problem_li = f"your homepage currently takes {speed_val} to load on mobile 4G. Google data shows 53% of mobile visitors leave if a page takes over 2.5 seconds — that's warm, high-intent traffic lost before they even see your services."
    elif problem_type == "outdated_design":
        ui_score = problem_details.get("ui_score", 35)
        problem_email = f"However, I noticed your current website design feels dated compared to competitors in {city}. Modern customers form opinions about a business within 0.05 seconds of seeing a website, and an older design can create an impression that doesn't match the quality of service you actually deliver. In our analysis, the visual design scored {ui_score}/100 against current industry benchmarks."
        problem_wa = f"I looked at your website and noticed the design feels a bit dated compared to newer competitors in {city}. Customers judge a business within *0.05 seconds* of seeing a website, and an older look can cost you credibility — even when your actual service is top-notch."
        problem_call = f"I took a look at your website and while the content is solid, the visual design feels a bit dated compared to what newer competitors in {city} are doing. First impressions happen in under a second online."
        problem_ig = f"I checked out your website and noticed the design could use a modern refresh. Customers judge a business in 0.05 seconds online — and your current design doesn't do justice to the quality you actually deliver 🎨"
        problem_li = f"your current website design appears dated compared to emerging competitors in {city}. Research shows customers form opinions about a business within 0.05 seconds of seeing a website, and an older design can undermine the quality impression you've worked so hard to build."
    else:
        problem_email = f"However, your website currently lacks a 1-click WhatsApp inquiry widget or clear appointment form. Most mobile visitors want instant answers, and forcing them to manually copy-paste phone numbers leads to a 40%+ drop in direct bookings."
        problem_wa = f"I noticed your website is missing a *1-click WhatsApp or instant booking widget*. Mobile visitors prefer fast messaging, and without it, many inquiries get lost."
        problem_call = f"I noticed your website doesn't have an instant WhatsApp or direct inquiry form, making it harder for mobile visitors to reach out quickly."
        problem_ig = f"Noticed your website is missing a 1-click WhatsApp or instant booking widget. Mobile visitors want instant answers — without it, you're likely losing 40%+ of inquiry opportunities."
        problem_li = f"your website currently lacks a 1-click WhatsApp inquiry widget or instant booking form. Most mobile visitors want instant answers, and manually copying phone numbers leads to a 40%+ drop-off in direct inquiries."

    # ── 3. TAILORED SOLUTION & LOW-PRESSURE VALUE CTA ─────────────────────────
    
    solutions_email = [
        f"To show you how much of a difference this makes, we put together a clean, high-speed interactive website prototype tailored specifically for {lead.business_name}{local_ref_short} with 1-click WhatsApp booking and modern mobile styling.\n\nWould you be open to me sending over a 60-second video preview / demo link so you can see it? Zero pressure or obligations at all.",
        f"We went ahead and designed a modern, fast-loading prototype landing page for {lead.business_name} featuring direct WhatsApp ordering and mobile responsiveness.\n\nCould I send you a quick preview link to review? No pitch or sales pressure — just wanted to share the idea with you.",
        f"We drafted an interactive, mobile-optimized demo site for {lead.business_name}{local_ref_short} with instant inquiry capture and sub-second load times.\n\nWould it be okay if I sent over a quick demo link for you to check out?"
    ]
    solution_email = random.choice(solutions_email)

    solutions_wa = [
        f"We actually built a *modern, mobile-optimized live demo prototype* for *{lead.business_name}* featuring instant WhatsApp booking and fast loading.\n\nWould you be open if I sent you a quick 30-second preview link to check it out? (No obligations at all)",
        f"We put together a *tailored interactive demo website* for *{lead.business_name}* to show how 1-click WhatsApp ordering would work.\n\nCan I send over a quick preview link for your team to take a look?"
    ]
    solution_wa = random.choice(solutions_wa)

    solutions_ig = [
        f"We actually built a tailored demo prototype for {lead.business_name} showing how a modern site with instant WhatsApp booking would look. Can I DM you the preview link? 🔗 (Zero obligations)",
        f"We designed a quick interactive demo for {lead.business_name} with 1-click booking and mobile-first styling. Would love to share the preview link if you're open to it! 🎯"
    ]
    solution_ig = random.choice(solutions_ig)

    solutions_li = [
        f"We've actually put together a clean, mobile-optimized demo prototype specifically for {lead.business_name} with instant WhatsApp inquiry capture. Would you be open to me sending over a quick preview link? No obligations at all.",
        f"We designed a modern interactive demo tailored for {lead.business_name} with 1-click booking and sub-second load times. I'd love to share the preview link if you're open to it — zero pressure."
    ]
    solution_li = random.choice(solutions_li)

    # ── Subject Lines ─────────────────────────────────────────────────────────
    
    subjects = [
        f"Quick observation regarding {lead.business_name}'s Google presence",
        f"Observation on {lead.business_name} in {city} (+ demo prototype)",
        f"Feedback on {lead.business_name}'s {niche} listing in {city}",
        f"Idea for {lead.business_name} ({rating}★ reviews)",
        f"{lead.business_name}: A quick website opportunity I noticed"
    ]
    email_subject = random.choice(subjects)

    # ── Full Email ────────────────────────────────────────────────────────────
    
    email_content = f"""{greeting_email}

{positive_hook}

{problem_email}

{solution_email}

Best regards,
Apex Web Agency
"""

    # ── Full WhatsApp ─────────────────────────────────────────────────────────
    
    whatsapp_message = f"""{greeting_wa}

{positive_hook_wa}

{problem_wa}

{solution_wa}"""

    # ── Full LinkedIn (now 3-part structured) ─────────────────────────────────
    
    linkedin_message = f"""Hi {target_name}, hope you're having a great week!

{positive_hook}

I noticed a quick opportunity: {problem_li}

{solution_li}"""

    # ── Full Instagram DM (now 3-part structured) ─────────────────────────────
    
    # Use niche-specific IG hook or generic
    ig_hook_template = _NICHE_HOOKS_INSTAGRAM.get(niche, f"Your {rating}★ reputation across {reviews}+ reviews in {city} is seriously impressive — that kind of loyalty is earned!")
    ig_hook = ig_hook_template.format(biz=lead.business_name, rating=rating, reviews=reviews, city=city) if "{" in ig_hook_template else ig_hook_template
    
    instagram_dm = f"""Hey {lead.business_name} team! 👋

{ig_hook}

{problem_ig}

{solution_ig}"""

    # ── Cold Call Script ──────────────────────────────────────────────────────
    
    cold_call_script = f"""[STEP 1: POSITIVE HOOK & RAPPORT]
"Hi, is this the owner or manager of {lead.business_name}? 
Hello {target_name}, this is [Your Name] from Apex Web Systems. I was searching for top {niche}s in {city}{local_ref} and saw your amazing {rating}★ customer rating across {reviews}+ reviews — huge congratulations on the local reputation!"

[STEP 2: THE SPECIFIC PROBLEM]
"{problem_call} In {city}, that usually means you're missing out on 10 to 15 warm customer inquiries every single week."

[STEP 3: THE SOLUTION & LOW-PRESSURE OFFER]
"We actually designed a custom, mobile-optimized live demo prototype tailored specifically for {lead.business_name} with instant WhatsApp booking to show how you can capture those leads. 
Would you be open if I sent a quick 45-second preview link to your WhatsApp or email to take a look? Zero strings attached."

[OBJECTION: 'We already have a website / developer']
"Totally understand! The demo prototype is just to show you modern conversion benchmarks and speed comparison against your current setup. I'd be happy to text you the link just for reference."

[OBJECTION: 'How much does this cost?']
"There's no cost to view the prototype — it's completely free to review. If you love it and want to deploy it, our turnaround is under 48 hours with straightforward pricing. Can I WhatsApp the preview to this number?"
"""

    return email_subject, email_content, whatsapp_message, linkedin_message, instagram_dm, cold_call_script


def generate_all_outreach_for_database(db: Session) -> int:
    """
    Batch helper: Generates/refreshes unique 3-part Hook→Problem→Solution 
    outreach copy for ALL leads in database.
    Returns count of successfully processed leads.
    """
    leads = db.query(Lead).all()
    count = 0
    for lead in leads:
        try:
            generate_outreach_materials(lead.id, db)
            count += 1
        except Exception as e:
            logger.error(f"Error generating outreach for lead {lead.id}: {e}")
    return count
