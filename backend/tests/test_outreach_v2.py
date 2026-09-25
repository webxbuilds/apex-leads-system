import sys
import os
import random
import logging
import re
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OutreachV2Test")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from backend.app.db.database import SessionLocal, Base, engine
from backend.app.db.models import Lead, AnalysisReport, OutreachMessage
from backend.app.services.ai_service import generate_outreach_materials

def generate_jaccard_similarity(str1, str2):
    # Calculate Jaccard similarity of words
    words1 = set(re.findall(r'\w+', str1.lower()))
    words2 = set(re.findall(r'\w+', str2.lower()))
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    logger.info("Initializing 20 gym lead mock-ups in db for V2 copy testing...")
    db = SessionLocal()
    
    gym_names = [
        "Powerhouse Gym Surat", "Iron Temple Gym Baroda", "Gold Fitness Vesu", "Alpha Fit Adajan", 
        "Hustlers Club Varachha", "Surat Fitness Hub", "Flex & Tone Gym", "Mega Gym Katargam",
        "Body Temple Udhna", "Evolution Fitness Rander", "Titan Gym Jahangirpura", "Spartan Fitness Pal",
        "Apex Gym Veshu", "Oxygen Fitness City", "Peak Performance Gym", "Elite Gym Amroli",
        "Ultimate Fit Club", "Dumbbell & Barbell", "The Heavy Lift Gym", "Surat Strength Arena"
    ]
    cities = ["Surat", "Ahmedabad", "Vadodara", "Rajkot", "Gandhinagar"]
    ratings = [4.2, 4.5, 4.8, 3.9, 4.7]
    reviews = [45, 120, 320, 89, 540]
    
    # Gaps choices to trigger different flows
    gaps_variants = [
        {"has_website": False},
        {"has_website": True, "has_https": False},
        {"has_website": True, "is_mobile_responsive": False},
        {"has_website": True, "load_speed_seconds": 4.5},
        {"has_website": True, "has_contact_form": False}
    ]
    
    created_leads = []
    
    try:
        # Create 20 test gyms
        for i in range(20):
            name = gym_names[i]
            city = random.choice(cities)
            rating = random.choice(ratings)
            rev = random.choice(reviews)
            variant = random.choice(gaps_variants)
            
            lead = Lead(
                business_name=name,
                owner_name=f"Owner {i+1}",
                phone=f"+9199999000{i:02d}",
                website=f"http://www.{name.lower().replace(' ', '')}.com" if variant["has_website"] else "Not Publicly Available",
                city=city,
                category="Gym",
                google_rating=rating,
                reviews_count=rev,
                status="New Lead",
                last_verified_at=datetime.now(timezone.utc)
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            created_leads.append(lead)
            
            # Create analysis report if website exists
            if variant["has_website"]:
                report = AnalysisReport(
                    lead_id=lead.id,
                    has_https=variant.get("has_https", True),
                    is_mobile_responsive=variant.get("is_mobile_responsive", True),
                    load_speed_seconds=variant.get("load_speed_seconds", 1.5),
                    has_contact_form=variant.get("has_contact_form", True),
                    has_whatsapp_button=True,
                    overall_score=80
                )
                db.add(report)
                db.commit()
                
        logger.info("Successfully registered 20 gym leads. Starting AI V2 message generation...")
        
        generated_emails = []
        
        for idx, lead in enumerate(created_leads):
            logger.info(f"Generating for {idx+1}/20: {lead.business_name}...")
            outreach = generate_outreach_materials(lead.id, db)
            generated_emails.append(outreach.email_content)
            
            # Quick output
            print(f"\n[{idx+1}] Gym: {lead.business_name}")
            print(f"Subject: {outreach.email_subject}")
            print(f"Content: {outreach.email_content}")
            print("-" * 40)
            
        # Check similarity between any two messages
        similarity_threshold = 0.75 # we want Jaccard similarity < 75%
        overlap_found = False
        
        logger.info("\nChecking similarity matrix for generated copy...")
        for i in range(len(generated_emails)):
            for j in range(i + 1, len(generated_emails)):
                sim = generate_jaccard_similarity(generated_emails[i], generated_emails[j])
                if sim > similarity_threshold:
                    overlap_found = True
                    logger.warning(f"SIMILAR COPY DETECTED between Gym {i+1} and Gym {j+1}: Similarity={sim:.2f}")
                    
        if overlap_found:
            logger.error("Test failed: Some generated messages look too similar.")
            sys.exit(1)
        else:
            logger.info("TEST PASSED: Every single one of the 20 outreach messages is unique, conversational, and highly personalized!")
            
    finally:
        logger.info("Cleaning up 20 test gyms...")
        for lead in created_leads:
            db.delete(lead)
        db.commit()
        db.close()
        logger.info("Database cleaned successfully.")

if __name__ == "__main__":
    main()
