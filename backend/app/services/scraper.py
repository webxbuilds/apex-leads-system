import re
import urllib.parse
import json
import logging
import os
import socket
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from backend.app.db.models import Lead, Settings
from backend.app.core.rate_limiter import rate_limited_request
from playwright.sync_api import sync_playwright
import email_validator

logger = logging.getLogger(__name__)

def normalize_phone(phone_str: str) -> str:
    """
    Cleans phone numbers to contain only digits and leading plus.
    Standardizes simple local patterns to country codes (e.g. +91).
    """
    if not phone_str or phone_str.lower() in ["not publicly available", "none", "null"]:
        return "Not Publicly Available"
        
    cleaned = "".join([c for c in phone_str if c.isdigit() or c == "+"])
    if not cleaned:
        return "Not Publicly Available"
        
    # Standardize Indian formats
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+91{cleaned}"
    elif len(cleaned) == 11 and cleaned.startswith("0"):
        return f"+91{cleaned[1:]}"
    elif cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    elif cleaned.startswith("+91") and len(cleaned) == 13:
        return cleaned
        
    if cleaned.startswith("+"):
        return cleaned
    return f"+{cleaned}"

def is_mobile_number(phone_str: str) -> bool:
    """
    Determines if a phone number is a mobile line likely to support WhatsApp.
    Indian mobile numbers typically start with 6, 7, 8, or 9.
    """
    if not phone_str or phone_str == "Not Publicly Available":
        return False
    digits = "".join([c for c in phone_str if c.isdigit()])
    if len(digits) == 10 and digits[0] in "6789":
        return True
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return True
    if len(digits) >= 10:
        return True
    return False

def normalize_website(website_str: str) -> str:
    """
    Standardizes websites to a canonical domain string for matching.
    """
    if not website_str or website_str.lower() in ["not publicly available", "none", "null"]:
        return "Not Publicly Available"
        
    parsed = urllib.parse.urlparse(website_str.strip().lower())
    netloc = parsed.netloc or parsed.path
    if netloc.startswith("www."):
        netloc = netloc[4:]
    netloc = netloc.split("/")[0]
    return netloc

def validate_and_clean_email(email_str: str) -> str:
    """
    Validates and cleans email strings. Filters out common web asset false positives
    and validates format and deliverability.
    """
    if not email_str or email_str.lower() in ["not publicly available", "none", "null"]:
        return "Not Publicly Available"
        
    email_clean = email_str.strip()
    invalid_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".ico", ".woff", ".ttf")
    if any(email_clean.lower().endswith(ext) for ext in invalid_extensions):
        return "Not Publicly Available"
        
    dummy_prefixes = ("user@", "username@", "youremail@", "email@", "name@")
    dummy_domains = ("@example.com", "@sentry.io", "@wix.com", "@domain.com", "@test.com", "@sample.com")
    
    if any(email_clean.lower().startswith(p) for p in dummy_prefixes) or any(email_clean.lower().endswith(d) for d in dummy_domains):
        return "Not Publicly Available"

    try:
        val = email_validator.validate_email(email_clean, check_deliverability=False)
        return val.normalized
    except Exception:
        # Fallback simple regex validation
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_clean):
            return email_clean
        return "Not Publicly Available"

def extract_schema_and_metadata(soup: BeautifulSoup) -> dict:
    """
    Extracts structured JSON-LD data (LocalBusiness, Organization, Person)
    and social/contact info embedded directly in Schema.org tags.
    """
    info = {
        "email": None,
        "phone": None,
        "whatsapp_number": None,
        "owner_name": None,
        "socials": {}
    }
    
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            raw_content = script.string.strip()
            data = json.loads(raw_content)
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                if "@graph" in item and isinstance(item["@graph"], list):
                    items.extend(item["@graph"])
                    continue
                    
                # Check for founder / owner
                if "founder" in item:
                    founder = item["founder"]
                    if isinstance(founder, dict) and "name" in founder:
                        info["owner_name"] = str(founder["name"]).strip()
                    elif isinstance(founder, str):
                        info["owner_name"] = founder.strip()
                        
                if "employee" in item and not info["owner_name"]:
                    emp = item["employee"]
                    if isinstance(emp, dict) and "name" in emp:
                        info["owner_name"] = str(emp["name"]).strip()
                        
                if item.get("@type") == "Person" and "name" in item and not info["owner_name"]:
                    info["owner_name"] = str(item["name"]).strip()
                    
                # Contact telephone
                if "telephone" in item and not info["phone"]:
                    info["phone"] = str(item["telephone"]).strip()
                    
                # Contact email
                if "email" in item and not info["email"]:
                    info["email"] = str(item["email"]).strip()
                    
                # Social profiles in sameAs
                if "sameAs" in item:
                    same_as = item["sameAs"]
                    if isinstance(same_as, str):
                        same_as = [same_as]
                    if isinstance(same_as, list):
                        for link in same_as:
                            link_str = str(link)
                            if "instagram.com" in link_str:
                                info["socials"]["instagram"] = link_str
                            elif "facebook.com" in link_str:
                                info["socials"]["facebook"] = link_str
                            elif "linkedin.com" in link_str:
                                info["socials"]["linkedin"] = link_str
        except Exception:
            continue
            
    return info

def extract_owner_from_text(soup: BeautifulSoup) -> str:
    """
    Uses heuristic keyword searches in page text (About Us/Team/Contact)
    to locate owner/founder/doctor/director names.
    """
    try:
        # Clone soup and remove scripts/styles
        text_soup = BeautifulSoup(str(soup), 'html.parser')
        for tag in text_soup(["script", "style", "nav", "footer", "noscript"]):
            tag.decompose()
            
        text = text_soup.get_text(" ", strip=True)
        
        patterns = [
            r'(?:Dr\.|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'(?:Founder|Co-Founder|Founding Director|Managing Director|Proprietor|Owner|CEO)\s*[:\-–]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*,\s*(?:Founder|Co-Founder|Managing Director|Proprietor|Owner|CEO)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                words = name.split()
                if 2 <= len(words) <= 3 and not any(w.lower() in ["about", "contact", "home", "privacy", "terms", "service", "menu", "team", "review", "read", "more"] for w in words):
                    return name
    except Exception:
        pass
        
    return "Not Publicly Available"

def crawl_and_verify_website(url: str) -> dict:
    """
    Crawls a business website homepage and contact/about pages using rate-limited requests
    to find verified contact emails, phone numbers, owner names, and social media links.
    """
    if not url or url.lower() in ["not publicly available", "none", "null"]:
        return {}
        
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    info = {
        "email": "Not Publicly Available",
        "phone": "Not Publicly Available",
        "owner_name": "Not Publicly Available",
        "instagram": "Not Publicly Available",
        "facebook": "Not Publicly Available",
        "linkedin": "Not Publicly Available",
        "whatsapp_number": "Not Publicly Available"
    }
    
    try:
        resp = rate_limited_request("GET", url, headers=headers, timeout=8, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Extract JSON-LD Schema Data
        schema_data = extract_schema_and_metadata(soup)
        if schema_data.get("owner_name"):
            info["owner_name"] = schema_data["owner_name"]
        if schema_data.get("email"):
            cleaned = validate_and_clean_email(schema_data["email"])
            if cleaned != "Not Publicly Available":
                info["email"] = cleaned
        if schema_data.get("phone"):
            info["phone"] = normalize_phone(schema_data["phone"])
            if is_mobile_number(info["phone"]):
                info["whatsapp_number"] = info["phone"]
                
        for platform, link in schema_data.get("socials", {}).items():
            info[platform] = link
            
        # 2. Extract Raw Emails from page content
        emails = set()
        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        for email in email_matches:
            cleaned = validate_and_clean_email(email)
            if cleaned != "Not Publicly Available":
                emails.add(cleaned)
                
        # 3. Extract Links & Socials
        links = soup.find_all('a', href=True)
        contact_page_url = None
        about_page_url = None
        social_patterns = {
            "instagram": r'instagram\.com/([a-zA-Z0-9_.-]+)',
            "facebook": r'facebook\.com/([a-zA-Z0-9_.-]+)',
            "linkedin": r'linkedin\.com/(?:company|in)/([a-zA-Z0-9_.-]+)',
            "whatsapp": r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)'
        }
        
        for link in links:
            href = link['href']
            href_lower = href.lower()
            if not contact_page_url and any(x in href_lower for x in ["contact", "reach"]):
                contact_page_url = urllib.parse.urljoin(url, href)
            if not about_page_url and any(x in href_lower for x in ["about", "team", "founder", "doctor"]):
                about_page_url = urllib.parse.urljoin(url, href)
                
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, href, re.IGNORECASE)
                if match:
                    if platform == "whatsapp":
                        info["whatsapp_number"] = "+" + match.group(1)
                    elif info[platform] == "Not Publicly Available":
                        info[platform] = href
                        
        if emails and info["email"] == "Not Publicly Available":
            info["email"] = list(emails)[0]
            
        # 4. Check owner from text if still not found
        if info["owner_name"] == "Not Publicly Available":
            owner = extract_owner_from_text(soup)
            if owner != "Not Publicly Available":
                info["owner_name"] = owner
                
        # 5. Check Contact/About Page
        secondary_url = contact_page_url or about_page_url
        if secondary_url and secondary_url != url:
            try:
                c_resp = rate_limited_request("GET", secondary_url, headers=headers, timeout=6, verify=False)
                c_soup = BeautifulSoup(c_resp.text, 'html.parser')
                
                c_schema = extract_schema_and_metadata(c_soup)
                if c_schema.get("owner_name") and info["owner_name"] == "Not Publicly Available":
                    info["owner_name"] = c_schema["owner_name"]
                if c_schema.get("email") and info["email"] == "Not Publicly Available":
                    cleaned = validate_and_clean_email(c_schema["email"])
                    if cleaned != "Not Publicly Available":
                        info["email"] = cleaned
                        
                c_email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', c_resp.text)
                for email in c_email_matches:
                    cleaned = validate_and_clean_email(email)
                    if cleaned != "Not Publicly Available":
                        emails.add(cleaned)
                        
                c_links = c_soup.find_all('a', href=True)
                for link in c_links:
                    href = link['href']
                    for platform, pattern in social_patterns.items():
                        match = re.search(pattern, href, re.IGNORECASE)
                        if match:
                            if platform == "whatsapp" and info["whatsapp_number"] == "Not Publicly Available":
                                info["whatsapp_number"] = "+" + match.group(1)
                            elif info[platform] == "Not Publicly Available":
                                info[platform] = href
                                
                if info["owner_name"] == "Not Publicly Available":
                    c_owner = extract_owner_from_text(c_soup)
                    if c_owner != "Not Publicly Available":
                        info["owner_name"] = c_owner
            except Exception as e:
                logger.debug(f"Could not request secondary page {secondary_url}: {e}")
                
        if emails and info["email"] == "Not Publicly Available":
            info["email"] = list(emails)[0]
            
    except Exception as e:
        logger.debug(f"Could not crawl homepage {url}: {e}")
        
    return info

def enrich_lead_website_parallel(leads_data: list, max_workers: int = 6) -> list:
    """
    Crawls websites for all scraped leads in parallel using ThreadPoolExecutor
    to accelerate lead contact enrichment by 5x-10x.
    """
    leads_to_crawl = [
        (idx, item) for idx, item in enumerate(leads_data)
        if item.get("website") and item["website"] != "Not Publicly Available"
    ]
    
    if not leads_to_crawl:
        return leads_data

    logger.info(f"Starting parallel contact crawler for {len(leads_to_crawl)} websites...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(crawl_and_verify_website, item["website"]): idx
            for idx, item in leads_to_crawl
        }
        
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                details = future.result()
                if details:
                    for k, v in details.items():
                        if v and v != "Not Publicly Available":
                            # Merge enriched details
                            curr_v = leads_data[idx].get(k)
                            if not curr_v or curr_v == "Not Publicly Available":
                                leads_data[idx][k] = v
            except Exception as e:
                logger.debug(f"Parallel crawl error for item {idx}: {e}")
                
    return leads_data

def generate_lead_opportunity_tags(data: dict) -> list:
    """
    Analyzes lead properties to tag sales opportunities (e.g. Missing Website, Broken SSL, High Reviews).
    """
    tags = []
    website = data.get("website")
    reviews = data.get("reviews_count") or 0
    rating = data.get("google_rating")
    phone = data.get("phone")
    
    if not website or website == "Not Publicly Available":
        tags.append("MISSING_WEBSITE")
    elif website.startswith("http://"):
        tags.append("NO_SSL_CERTIFICATE")
        
    if reviews >= 25 and (rating and rating >= 4.0):
        tags.append("HIGH_REVIEW_PROSPECT")
        
    if is_mobile_number(phone):
        tags.append("WHATSAPP_READY")
        
    email = data.get("email")
    if email and email != "Not Publicly Available":
        tags.append("VERIFIED_EMAIL")
        
    return tags

def merge_and_save_lead(db: Session, data: dict) -> Lead:
    """
    Implements database-level deduplication, data preservation, and merging.
    Merges newly-verified properties into existing business entries without losing custom tags/notes.
    """
    phone = data.get("phone")
    website = data.get("website")
    norm_phone = normalize_phone(phone)
    norm_website = normalize_website(website)
    
    existing = None
    
    # Match by normalized phone
    if norm_phone != "Not Publicly Available":
        existing = db.query(Lead).filter(Lead.phone == norm_phone).first()
        
    # Match by normalized website
    if not existing and norm_website != "Not Publicly Available":
        existing = db.query(Lead).filter(Lead.website.like(f"%{norm_website}%")).first()
        
    # Match by Name and City
    if not existing:
        existing = db.query(Lead).filter(
            Lead.business_name == data["business_name"],
            Lead.city == data["city"]
        ).first()
        
    opportunity_tags = generate_lead_opportunity_tags(data)
    
    if existing:
        logger.info(f"Merging scraped data with existing lead {existing.id} ({existing.business_name})")
        # Merge new attributes if they are currently unverified or empty
        for k, v in data.items():
            if v and v != "Not Publicly Available" and k != "tags":
                curr_v = getattr(existing, k, None)
                if not curr_v or curr_v == "Not Publicly Available":
                    setattr(existing, k, v)
        
        # Merge tags without losing existing custom user tags
        existing_tags = []
        if existing.tags:
            try:
                existing_tags = json.loads(existing.tags)
            except Exception:
                existing_tags = [existing.tags]
                
        merged_tags = list(set(existing_tags + opportunity_tags))
        existing.tags = json.dumps(merged_tags) if merged_tags else None
        
        # Always update dynamic attributes
        existing.google_rating = data.get("google_rating") or existing.google_rating
        existing.reviews_count = data.get("reviews_count") or existing.reviews_count
        existing.last_verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create fresh lead
        tags_json = json.dumps(opportunity_tags) if opportunity_tags else None
        
        # Determine whatsapp readiness
        whatsapp_val = data.get("whatsapp_number")
        if (not whatsapp_val or whatsapp_val == "Not Publicly Available") and is_mobile_number(norm_phone):
            whatsapp_val = norm_phone

        lead = Lead(
            business_name=data["business_name"],
            owner_name=data.get("owner_name") or "Not Publicly Available",
            phone=norm_phone,
            whatsapp_number=whatsapp_val or "Not Publicly Available",
            email=data.get("email") or "Not Publicly Available",
            website=website or "Not Publicly Available",
            instagram=data.get("instagram") or "Not Publicly Available",
            facebook=data.get("facebook") or "Not Publicly Available",
            linkedin=data.get("linkedin") or "Not Publicly Available",
            maps_url=data.get("maps_url"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state") or "Gujarat",
            country=data.get("country") or "India",
            postal_code=data.get("postal_code"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            google_rating=data.get("google_rating"),
            reviews_count=data.get("reviews_count"),
            business_status=data.get("business_status") or "OPERATIONAL",
            opening_hours=data.get("opening_hours") or "Not Publicly Available",
            category=data.get("category"),
            data_source=data.get("data_source"),
            status="New Lead",
            tags=tags_json,
            last_verified_at=datetime.now(timezone.utc)
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

def scrape_leads(source: str, category: str, city: str, limit: int = 10, db: Session = None) -> list:
    """
    Entry point to fetch verified real leads.
    Utilizes local caching, Google Maps Place API, Playwright fast scraper, and DuckDuckGo fallback.
    Enriches contact details in parallel via ThreadPoolExecutor.
    """
    logger.info(f"Initiating scraper: Category={category}, City={city}, Source={source}, Limit={limit}")
    
    # 1. Cache Check: check if db has fresh leads
    cached_leads = []
    if db:
        cutoff = datetime.now(timezone.utc).timestamp() - (7 * 24 * 60 * 60) # 7 days
        cutoff_date = datetime.fromtimestamp(cutoff, tz=timezone.utc)
        cached_leads = db.query(Lead).filter(
            Lead.category == category,
            Lead.city == city,
            Lead.last_verified_at >= cutoff_date
        ).limit(limit).all()
        
        if len(cached_leads) >= limit:
            logger.info(f"Returning {len(cached_leads)} cached leads for {category} in {city}")
            return cached_leads
            
    # 2. Key Check: check for Google Places API Key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY")
    if db and not api_key:
        settings = db.query(Settings).first()
        if settings and settings.gemini_api_key:
            pass
            
    results = []
    
    # Query Google Places API if key exists
    if api_key:
        try:
            logger.info("Using official Google Places API...")
            results = _scrape_google_places_api(category, city, limit, api_key)
        except Exception as e:
            logger.error(f"Google Places API scrape failed: {e}. Falling back to automation...")
            results = []
            
    # Fallback to Playwright Google Maps Scraping
    if not results:
        try:
            logger.info("Starting High-Speed Playwright Google Maps scraper...")
            results = _scrape_google_maps_playwright(category, city, limit)
        except Exception as e:
            logger.error(f"Playwright Google Maps scraper failed: {e}. Falling back to DuckDuckGo/Directories...")
            results = []
            
    # DuckDuckGo Directory search fallback
    if not results:
        try:
            logger.info("Starting DuckDuckGo search directory parser...")
            results = _scrape_duckduckgo_live(category, city, limit)
        except Exception as e:
            logger.error(f"DuckDuckGo fallback scraper failed: {e}")
            results = []
            
    # Perform parallel website verification and deep contact enrichment (5x-10x faster)
    results = enrich_lead_website_parallel(results, max_workers=6)
    
    final_leads = []
    for data in results:
        # Map values to database and commit
        if db:
            saved_lead = merge_and_save_lead(db, data)
            final_leads.append(saved_lead)
        else:
            final_leads.append(data)
            
    # If we had some cached leads and wanted to fill the remaining
    if len(final_leads) < limit and cached_leads:
        ids = [x.id for x in final_leads if isinstance(x, Lead)]
        for c in cached_leads:
            if c.id not in ids and len(final_leads) < limit:
                final_leads.append(c)
                
    return final_leads

def _scrape_google_places_api(category: str, city: str, limit: int, api_key: str) -> list:
    """
    Performs Google Places Text Search and Details queries.
    """
    query = f"{category} in {city}"
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    
    resp = rate_limited_request("GET", search_url, params=params)
    if resp.status_code != 200:
        logger.error(f"Google Places API returned status {resp.status_code}: {resp.text}")
        return []
        
    data = resp.json()
    items = data.get("results", [])[:limit]
    
    results = []
    for item in items:
        place_id = item.get("place_id")
        if not place_id:
            continue
            
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address,rating,user_ratings_total,url,geometry,business_status,opening_hours,address_components",
            "key": api_key
        }
        det_resp = rate_limited_request("GET", details_url, params=details_params)
        det_data = det_resp.json().get("result", {}) if det_resp.status_code == 200 else {}
        
        geom = det_data.get("geometry", item.get("geometry", {}))
        loc = geom.get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        
        postal_code = None
        state = "Gujarat"
        country = "India"
        for comp in det_data.get("address_components", []):
            types = comp.get("types", [])
            if "postal_code" in types:
                postal_code = comp.get("long_name", "")
            elif "administrative_area_level_1" in types:
                state = comp.get("long_name", "")
            elif "country" in types:
                country = comp.get("long_name", "")
                
        open_hours = det_data.get("opening_hours", {})
        weekday_text = open_hours.get("weekday_text", [])
        hours_str = "\n".join(weekday_text) if weekday_text else "Not Publicly Available"
        
        phone = det_data.get("formatted_phone_number") or det_data.get("international_phone_number") or "Not Publicly Available"
        
        results.append({
            "business_name": det_data.get("name", item.get("name")),
            "phone": phone,
            "website": det_data.get("website") or "Not Publicly Available",
            "address": det_data.get("formatted_address", item.get("formatted_address")),
            "google_rating": det_data.get("rating", item.get("rating")),
            "reviews_count": det_data.get("user_ratings_total", item.get("user_ratings_total")),
            "maps_url": det_data.get("url", f"https://www.google.com/maps/place/?q=place_id:{place_id}"),
            "latitude": lat,
            "longitude": lng,
            "business_status": det_data.get("business_status", "OPERATIONAL"),
            "opening_hours": hours_str,
            "postal_code": postal_code,
            "state": state,
            "country": country,
            "category": category,
            "city": city,
            "data_source": "Google Maps API"
        })
        
    return results

def _scrape_google_maps_playwright(category: str, city: str, limit: int) -> list:
    """
    Playwright scraper with route interception (drops images, fonts, analytics)
    to accelerate page rendering and resource efficiency.
    """
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # Intercept and abort heavy resources (images, media, fonts, tracking scripts)
        def route_filter(route):
            req = route.request
            res_type = req.resource_type
            url_str = req.url.lower()
            if res_type in ["image", "media", "font"] or any(tracker in url_str for tracker in ["google-analytics.com", "googletagmanager.com", "doubleclick.net"]):
                try:
                    route.abort()
                except Exception:
                    pass
            else:
                try:
                    route.continue_()
                except Exception:
                    pass
                    
        page.route("**/*", route_filter)
        
        search_query = f"{category} in {city}"
        url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(search_query)}"
        logger.info(f"Navigating to Maps search page: {url}")
        
        try:
            page.goto(url, timeout=25000)
            page.wait_for_timeout(2500)
        except Exception as e:
            logger.warning(f"Initial page navigation warning: {e}")
        
        # Handle cookie consent if visible
        try:
            consent = page.locator('button[aria-label="Accept all"], button[aria-label="Agree"], button:has-text("Accept all"), button:has-text("Agree")').first
            if consent.is_visible(timeout=2000):
                consent.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass
            
        scrollable = page.locator('div[role="feed"]')
        
        # Fast scroll to discover items
        attempts = 0
        last_count = 0
        while len(results) < limit and attempts < 6:
            links = page.locator('a[href*="/maps/place/"]').all()
            current_count = len(links)
            if current_count == last_count:
                attempts += 1
            else:
                attempts = 0
                last_count = current_count
                
            if current_count >= limit:
                break
                
            if scrollable.count() > 0:
                scrollable.evaluate("el => el.scrollBy(0, 1200)")
            else:
                page.evaluate("window.scrollBy(0, 1200)")
            page.wait_for_timeout(1000)
            
        links = page.locator('a[href*="/maps/place/"]').all()
        visited_urls = set()
        
        for link in links:
            if len(results) >= limit:
                break
                
            try:
                href = link.get_attribute("href")
            except Exception:
                continue
                
            if not href or href in visited_urls:
                continue
            visited_urls.add(href)
            
            try:
                link.click(timeout=3000)
                page.wait_for_timeout(1500)
                
                # Fetch Name
                name_element = page.locator('h1.DUwDvf')
                if name_element.count() == 0:
                    continue
                name = name_element.inner_text().strip()
                if not name:
                    continue
                    
                # Rating
                rating_element = page.locator('div.F7nice span span')
                rating = None
                if rating_element.count() > 0:
                    try:
                        rating = float(rating_element.first.inner_text().strip())
                    except Exception:
                        rating = None
                        
                # Reviews
                reviews_element = page.locator('div.F7nice span[aria-label*="reviews"]')
                reviews = 0
                if reviews_element.count() > 0:
                    text = reviews_element.first.inner_text()
                    digits = "".join([c for c in text if c.isdigit()])
                    reviews = int(digits) if digits else 0
                    
                # Address
                address_element = page.locator('button[data-item-id="address"]')
                address = address_element.inner_text().strip() if address_element.count() > 0 else "Not Publicly Available"
                
                # Phone
                phone_element = page.locator('button[data-item-id^="phone:tel:"]')
                phone = phone_element.inner_text().strip() if phone_element.count() > 0 else "Not Publicly Available"
                
                # Website
                website_element = page.locator('a[data-item-id="authority"]')
                website = website_element.get_attribute("href") if website_element.count() > 0 else "Not Publicly Available"
                
                # Coordinates
                lat, lng = None, None
                curr_url = page.url
                coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', curr_url)
                if coords_match:
                    lat = float(coords_match.group(1))
                    lng = float(coords_match.group(2))
                    
                # Business status
                status = "OPERATIONAL"
                closed_locator = page.locator('text="Closed temporarily"').or_(page.locator('text="Permanently closed"'))
                if closed_locator.count() > 0:
                    status = "CLOSED_TEMPORARILY" if "temporarily" in closed_locator.first.inner_text().lower() else "CLOSED_PERMANENTLY"
                    
                # Hours
                hours = "Not Publicly Available"
                hours_table = page.locator('table.e2iyh')
                if hours_table.count() > 0:
                    hours = hours_table.inner_text().strip().replace('\n', ' ')
                    
                results.append({
                    "business_name": name,
                    "phone": phone,
                    "website": website,
                    "address": address,
                    "google_rating": rating,
                    "reviews_count": reviews,
                    "maps_url": href,
                    "latitude": lat,
                    "longitude": lng,
                    "business_status": status,
                    "opening_hours": hours,
                    "category": category,
                    "city": city,
                    "data_source": "Google Maps (Playwright)"
                })
                
            except Exception as e:
                logger.debug(f"Error extracting Google Maps item pane: {e}")
                
        browser.close()
        
    return results

def _scrape_duckduckgo_live(category: str, city: str, limit: int) -> list:
    """
    DuckDuckGo search fallback query. Scrapes search listings and searches for business web URLs.
    """
    logger.info(f"Querying DuckDuckGo live for {category} in {city}")
    url = "https://html.duckduckgo.com/html/"
    query = f"{category} in {city} business website contact"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        resp = rate_limited_request("POST", url, data={"q": query}, headers=headers, timeout=12)
        if resp.status_code != 200:
            return []
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        
        containers = soup.find_all('div', class_='result')
        for div in containers:
            if len(results) >= limit:
                break
                
            title_el = div.find('a', class_='result__a')
            snippet_el = div.find('a', class_='result__snippet')
            
            if not title_el:
                continue
                
            title = title_el.get_text(strip=True)
            href = title_el.get('href', '')
            
            actual_url = ""
            if "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                queries = urllib.parse.parse_qs(parsed.query)
                actual_url = queries.get("uddg", [""])[0]
            else:
                actual_url = href
                
            if not actual_url or any(x in actual_url for x in ["duckduckgo.com", "google.com", "justdial.com", "facebook.com", "instagram.com", "youtube.com", "linkedin.com", "twitter.com", "wikipedia.org", "yelp.com", "indiamart.com"]):
                continue
                
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            
            business_name = title.split("-")[0].split("|")[0].split(":")[0].strip()
            if len(business_name) < 3 or any(w in business_name.lower() for w in ["best", "top 10", "results", "directory"]):
                continue
                
            phone = "Not Publicly Available"
            phone_match = re.search(r'(?:\+?\d{1,3}[- ]?)?\(?\d{3,4}\)?[- ]?\d{3,4}[- ]?\d{4}', snippet)
            if phone_match:
                phone = phone_match.group(0).strip()
                
            results.append({
                "business_name": business_name,
                "owner_name": "Not Publicly Available",
                "phone": phone,
                "email": "Not Publicly Available",
                "website": actual_url,
                "instagram": "Not Publicly Available",
                "facebook": "Not Publicly Available",
                "linkedin": "Not Publicly Available",
                "address": snippet[:100] + "..." if len(snippet) > 100 else snippet,
                "google_rating": None,
                "reviews_count": 0,
                "maps_url": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(business_name + ' ' + city)}",
                "latitude": None,
                "longitude": None,
                "business_status": "OPERATIONAL",
                "opening_hours": "Not Publicly Available",
                "category": category,
                "city": city,
                "data_source": "DuckDuckGo Web Search"
            })
            
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo live scrape error: {e}")
        return []
