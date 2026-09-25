import sys
import os
import pytest
from bs4 import BeautifulSoup

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.scraper import (
    normalize_phone,
    normalize_website,
    validate_and_clean_email,
    is_mobile_number,
    extract_schema_and_metadata,
    extract_owner_from_text,
    generate_lead_opportunity_tags,
    merge_and_save_lead
)
from backend.app.db.database import SessionLocal, Base, engine
from backend.app.db.models import Lead

def test_normalization():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("079 2654 3210") == "+917926543210"
    assert normalize_phone(None) == "Not Publicly Available"
    assert normalize_website("https://www.mygym.com/about") == "mygym.com"

def test_mobile_detection():
    assert is_mobile_number("+919876543210") is True
    assert is_mobile_number("+918876543210") is True
    assert is_mobile_number("+917876543210") is True
    assert is_mobile_number("+916876543210") is True
    assert is_mobile_number("Not Publicly Available") is False

def test_email_validation():
    assert validate_and_clean_email("hello@example.com") == "Not Publicly Available"
    assert validate_and_clean_email("contact@realbusiness.in") == "contact@realbusiness.in"
    assert validate_and_clean_email("banner@2x.png") == "Not Publicly Available"
    assert validate_and_clean_email("script.min.js") == "Not Publicly Available"

def test_schema_metadata_extraction():
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Apex Gym Ahmedabad",
            "telephone": "+91 98765 11111",
            "email": "info@apexgym.com",
            "founder": {
                "@type": "Person",
                "name": "Vikram Shah"
            },
            "sameAs": [
                "https://instagram.com/apexgym",
                "https://facebook.com/apexgym"
            ]
        }
        </script>
    </head>
    <body>
        <p>Managing Director: Vikram Shah</p>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    schema = extract_schema_and_metadata(soup)
    assert schema["owner_name"] == "Vikram Shah"
    assert schema["email"] == "info@apexgym.com"
    assert schema["socials"]["instagram"] == "https://instagram.com/apexgym"

    owner = extract_owner_from_text(soup)
    assert "Vikram Shah" in owner

def test_opportunity_tags():
    tags = generate_lead_opportunity_tags({
        "website": "Not Publicly Available",
        "reviews_count": 45,
        "google_rating": 4.8,
        "phone": "+919876543210"
    })
    assert "MISSING_WEBSITE" in tags
    assert "HIGH_REVIEW_PROSPECT" in tags
    assert "WHATSAPP_READY" in tags

def test_lead_merge_preserves_data():
    db = SessionLocal()
    try:
        # Create initial lead
        lead_data_1 = {
            "business_name": "Test Fitness Studio",
            "city": "Ahmedabad",
            "phone": "9876543210",
            "website": "http://testfitness.com",
            "google_rating": 4.2,
            "reviews_count": 15
        }
        lead = merge_and_save_lead(db, lead_data_1)
        lead_id = lead.id
        assert lead_id is not None
        
        # Add custom note and tag
        lead.notes = "Spoke with front desk. Follow up next week."
        db.commit()

        # Update via scraper with enriched data
        lead_data_2 = {
            "business_name": "Test Fitness Studio",
            "city": "Ahmedabad",
            "phone": "9876543210",
            "owner_name": "Rohan Mehta",
            "email": "contact@testfitness.com",
            "reviews_count": 28,
            "google_rating": 4.6
        }
        updated_lead = merge_and_save_lead(db, lead_data_2)
        
        assert updated_lead.id == lead_id
        assert updated_lead.owner_name == "Rohan Mehta"
        assert updated_lead.email == "contact@testfitness.com"
        assert updated_lead.notes == "Spoke with front desk. Follow up next week." # Preserved!
        assert updated_lead.reviews_count == 28
        
        # Cleanup test lead
        db.delete(updated_lead)
        db.commit()
    finally:
        db.close()
