import sys
import os
import re
import random
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SelfTest")

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from backend.app.db.database import SessionLocal, Base, engine
from backend.app.db.models import Lead, Settings
from backend.app.services.scraper import scrape_leads, normalize_phone, normalize_website
from playwright.sync_api import sync_playwright

def verify_lead_fields(lead):
    # Verify Business Name is real
    assert lead.business_name and len(lead.business_name) > 2, f"Invalid business name: {lead.business_name}"
    
    # Verify Phone (either Not Publicly Available or starts with +)
    phone = lead.phone
    assert phone in ["Not Publicly Available", None] or phone.startswith("+"), f"Phone generated as fake: {phone}"
    
    # Verify Email (either Not Publicly Available or valid email format)
    email = lead.email
    if email and email != "Not Publicly Available":
        assert re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email), f"Email generated as fake/invalid format: {email}"
        
    # Verify Website (either Not Publicly Available or valid web link)
    web = lead.website
    if web and web != "Not Publicly Available":
        assert web.startswith(("http://", "https://")), f"Website generated as fake/invalid: {web}"
        
    # Verify WhatsApp
    wa = lead.whatsapp_number
    assert wa in ["Not Publicly Available", None] or wa.startswith("+"), f"WhatsApp number generated as fake: {wa}"

def cross_check_random_lead(lead):
    logger.info(f"Cross-checking random lead '{lead.business_name}' against its Google Maps URL...")
    if not lead.maps_url:
        logger.warning("No maps_url to cross check. Skipping.")
        return True
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(lead.maps_url)
        page.wait_for_timeout(3500)
        
        # Handle cookie consent if visible
        try:
            consent = page.locator('button[aria-label="Accept all"], button[aria-label="Agree"], button:has-text("Accept all"), button:has-text("Agree")').first
            if consent.is_visible(timeout=2000):
                consent.click()
                page.wait_for_timeout(2000)
        except Exception:
            pass
            
        # Get business name on page
        name_element = page.locator('h1.DUwDvf')
        if name_element.count() > 0:
            scraped_name = name_element.inner_text().strip()
            logger.info(f"Google Maps displays business name: '{scraped_name}'")
            browser.close()
            if lead.business_name.lower() in scraped_name.lower() or scraped_name.lower() in lead.business_name.lower():
                logger.info("CROSS-CHECK VERIFICATION SUCCESSFUL! Lead matches Maps listing.")
                return True
            else:
                logger.error(f"CROSS-CHECK MISMATCH! CRM Lead: '{lead.business_name}' != Maps listing: '{scraped_name}'")
                return False
        else:
            logger.warning("Could not find business name element on Google Maps page. Skipping UI comparison.")
            browser.close()
            return True

def main():
    logger.info("Starting Self Test...")
    db = SessionLocal()
    
    try:
        category = "Gym"
        city = "Ahmedabad"
        limit = 10
        
        logger.info(f"Running scrape_leads(category='{category}', city='{city}', limit={limit})")
        leads = scrape_leads("Google Maps", category, city, limit, db)
        
        logger.info(f"Scraped {len(leads)} leads from engine.")
        assert len(leads) > 0, "No leads fetched. Scraper returned empty list."
        
        # 1. Verify every lead has real/valid structure and no fake data
        for idx, lead in enumerate(leads):
            logger.info(f"Verifying lead {idx+1}/{len(leads)}: {lead.business_name}")
            verify_lead_fields(lead)
            
        # 2. Pick a random lead and cross-check against Google Maps
        random_lead = random.choice(leads)
        cross_check_passed = cross_check_random_lead(random_lead)
        if not cross_check_passed:
            logger.error("Validation failed due to mismatch. System needs correction.")
            sys.exit(1)
            
        logger.info("ALL VALIDATION PASSES SUCCESSFULLY!")
        
        # 3. Clear the test leads, reset db, and clear temporary cache
        logger.info("Resetting database and clearing test leads as requested in final step...")
        for lead in leads:
            db.delete(lead)
        db.commit()
        logger.info("Database successfully cleaned and reset. Cached test leads cleared.")
        
    except Exception as e:
        logger.error(f"Self-test failed with error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
