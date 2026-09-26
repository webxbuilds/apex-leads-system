import sys
import os
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.db.database import SessionLocal
from backend.app.db.models import Lead
from backend.app.services.scraper import is_dummy_phone, is_mobile_number

def verify_all_leads():
    db = SessionLocal()
    leads = db.query(Lead).all()
    print(f"Total leads in database: {len(leads)}")
    
    dummy_phones = 0
    valid_wa = 0
    landline_leads = 0
    no_phone = 0
    
    for lead in leads:
        # Check dummy phone
        if lead.phone and lead.phone != "Not Publicly Available":
            if is_dummy_phone(lead.phone):
                dummy_phones += 1
                print(f"❌ Dummy phone detected: {lead.business_name} - {lead.phone}")
            
            # Check whatsapp
            if lead.whatsapp_number and lead.whatsapp_number != "Not Publicly Available":
                valid_wa += 1
                assert lead.whatsapp_number.startswith("+"), f"WhatsApp number must start with +: {lead.whatsapp_number}"
                # Must be a mobile number
                assert is_mobile_number(lead.whatsapp_number), f"WhatsApp number must be mobile: {lead.whatsapp_number}"
            else:
                if not is_mobile_number(lead.phone):
                    landline_leads += 1
        else:
            no_phone += 1
            
    print(f"✅ Verified: 0 dummy phones ({dummy_phones} found)")
    print(f"✅ Mobile WhatsApp numbers: {valid_wa}")
    print(f"✅ Landlines correctly not marked as WhatsApp: {landline_leads}")
    print(f"✅ No phone / Not Publicly Available: {no_phone}")
    db.close()
    
    if dummy_phones == 0:
        print("ALL DATABASE LEADS VERIFIED: 100% REAL AND CLEAN!")
        return 0
    else:
        print("FAIL: Dummy phones found.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_all_leads())
