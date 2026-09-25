import os
import sys
import json
from datetime import datetime, timedelta, timezone

# Add parent directory to path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from backend.app.db.database import SessionLocal, engine, Base
from backend.app.db.models import User, Lead, AnalysisReport, AIQualification, OutreachLog, Proposal, Task, Settings
from backend.app.core.security import hash_password

def seed_database():
    print("Re-building database tables...")
    # Safely clear old tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding Users and Settings...")
        # 1. Users
        admin = User(
            email="admin@apex.com",
            hashed_password=hash_password("admin123"),
            full_name="Default Admin",
            role="Admin"
        )
        sales = User(
            email="sales@apex.com",
            hashed_password=hash_password("sales123"),
            full_name="Sales Manager",
            role="Sales"
        )
        db.add(admin)
        db.add(sales)
        db.commit()
        db.refresh(admin)
        db.refresh(sales)

        # 2. Settings (ID=1)
        setting = Settings(
            id=1,
            company_name="Apex Website Agency Ltd",
            company_email="hello@apexweb.agency",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            branding_color="#6366f1"
        )
        db.add(setting)
        db.commit()

        # 3. Lead Profiles
        leads_data = [
            {
                "business_name": "Tuscany Garden Bistro",
                "owner_name": "Giovanni Rossi",
                "phone": "+91 98765 00001",
                "email": "contact@tuscanybistro.com",
                "website": "http://www.tuscanybistro.com",
                "address": "Block C, Sector 15, Noida",
                "google_rating": 4.6,
                "reviews_count": 240,
                "category": "Restaurant",
                "city": "Noida",
                "status": "Won",
                "tags": json.dumps(["restaurant", "won", "noida"]),
                "notes": "Met owner at the local food fest. They want to integrate online ordering tools.",
                "assigned_to_id": admin.id
            },
            {
                "business_name": "Apex Iron Fitness",
                "owner_name": "Vikram Malhotra",
                "phone": "+91 98765 00002",
                "email": "info@apexironfitness.com",
                "website": "http://www.apexironfitness.com",
                "address": "Basement Block E, Sector 62, Noida",
                "google_rating": 4.1,
                "reviews_count": 85,
                "category": "Gym",
                "city": "Noida",
                "status": "Proposal Sent",
                "tags": json.dumps(["gym", "unoptimized"]),
                "notes": "Shared proposal. Waiting for review post-weekend.",
                "assigned_to_id": sales.id
            },
            {
                "business_name": "Glow Premium Spa & Salon",
                "owner_name": "Neha Sharma",
                "phone": "+91 98765 00003",
                "email": "appointments@glowsalon.com",
                "website": "http://www.glowsalon.com",
                "address": "Market Complex C, Sector 50, Noida",
                "google_rating": 3.8,
                "reviews_count": 48,
                "category": "Salon",
                "city": "Noida",
                "status": "Interested",
                "tags": json.dumps(["salon", "priority"]),
                "notes": "Owner dislikes current designer, wants fresh mockup templates.",
                "assigned_to_id": sales.id
            },
            {
                "business_name": "Smile Align Dental Care",
                "owner_name": "Dr. Amit Verma",
                "phone": "+91 98765 00004",
                "email": "clinic@smilealign.com",
                "website": "http://www.smilealign.com",
                "address": "Shop 12, Sector 18, Noida",
                "google_rating": 4.9,
                "reviews_count": 180,
                "category": "Dentist",
                "city": "Noida",
                "status": "Meeting",
                "tags": json.dumps(["clinic", "whatsapp"]),
                "notes": "Scheduled clinical consultation strategy session.",
                "assigned_to_id": admin.id
            },
            {
                "business_name": "Heights Properties Realty",
                "owner_name": "Sanjay Mehta",
                "phone": "+91 98765 00005",
                "email": "sales@heightsproperties.com",
                "website": "http://www.heightsproperties.com",
                "address": "402, Trade Tower, Sector 62, Noida",
                "google_rating": 3.4,
                "reviews_count": 22,
                "category": "Real Estate",
                "city": "Noida",
                "status": "New Lead",
                "tags": json.dumps(["realty", "cold"]),
                "notes": "Cold scrape lead. Need to generate customized real estate template link.",
                "assigned_to_id": sales.id
            }
        ]
        
        leads = []
        for l_data in leads_data:
            lead = Lead(**l_data)
            db.add(lead)
            leads.append(lead)
        db.commit()
        
        for lead in leads:
            db.refresh(lead)

        print("Seeding Audit Reports and Qualifications...")
        # 4. Reports
        reports_data = {
            "Tuscany Garden Bistro": {"has_https": True, "is_mobile_responsive": True, "load_speed_seconds": 1.4, "broken_links_count": 0, "seo_title": "Tuscany Garden Bistro - Authentic Italian Cuisine Noida", "seo_description": "Best Italian bistro in Noida. Enjoy fresh woodfired pizzas and handmade pasta.", "missing_alt_tags": 2, "has_contact_form": True, "has_whatsapp_button": True, "has_google_maps_embed": True, "ui_score": 90, "ux_score": 92, "overall_score": 91},
            "Apex Iron Fitness": {"has_https": True, "is_mobile_responsive": False, "load_speed_seconds": 3.5, "broken_links_count": 4, "seo_title": "Apex Iron Fitness Noida - Best Gym", "seo_description": "", "missing_alt_tags": 12, "has_contact_form": False, "has_whatsapp_button": False, "has_google_maps_embed": True, "ui_score": 52, "ux_score": 48, "overall_score": 50},
            "Glow Premium Spa & Salon": {"has_https": False, "is_mobile_responsive": False, "load_speed_seconds": 4.8, "broken_links_count": 8, "seo_title": "Glow Spa", "seo_description": "Salon services in Noida.", "missing_alt_tags": 18, "has_contact_form": False, "has_whatsapp_button": True, "has_google_maps_embed": False, "ui_score": 45, "ux_score": 38, "overall_score": 41},
            "Smile Align Dental Care": {"has_https": True, "is_mobile_responsive": True, "load_speed_seconds": 2.8, "broken_links_count": 2, "seo_title": "Smile Align Dental Care | Dr. Amit Verma Dentist Noida", "seo_description": "Advanced dental clinic in Noida. Book dental checkups, root canal treatments and teeth aligners.", "missing_alt_tags": 5, "has_contact_form": True, "has_whatsapp_button": False, "has_google_maps_embed": True, "ui_score": 74, "ux_score": 68, "overall_score": 71},
            "Heights Properties Realty": {"has_https": False, "is_mobile_responsive": False, "load_speed_seconds": 5.4, "broken_links_count": 12, "seo_title": "Heights Properties", "seo_description": "", "missing_alt_tags": 24, "has_contact_form": False, "has_whatsapp_button": False, "has_google_maps_embed": False, "ui_score": 38, "ux_score": 34, "overall_score": 36}
        }

        for lead in leads:
            r_data = reports_data.get(lead.business_name)
            if r_data:
                report = AnalysisReport(
                    lead_id=lead.id,
                    has_https=r_data["has_https"],
                    is_mobile_responsive=r_data["is_mobile_responsive"],
                    load_speed_seconds=r_data["load_speed_seconds"],
                    broken_links_count=r_data["broken_links_count"],
                    seo_title=r_data["seo_title"],
                    seo_description=r_data["seo_description"],
                    missing_alt_tags=r_data["missing_alt_tags"],
                    has_contact_form=r_data["has_contact_form"],
                    has_whatsapp_button=r_data["has_whatsapp_button"],
                    has_google_maps_embed=r_data["has_google_maps_embed"],
                    social_links=json.dumps({"instagram": f"https://instagram.com/{lead.business_name.lower().replace(' ', '')}"}),
                    ui_score=r_data["ui_score"],
                    ux_score=r_data["ux_score"],
                    overall_score=r_data["overall_score"],
                    improvement_report_path=f"/static/reports/report_lead_{lead.id}_demo.html"
                )
                db.add(report)

        # 5. Qualifications
        qualifications_data = {
            "Tuscany Garden Bistro": {"score": "Cold", "reason": "Already optimized website (Overall: 91%). Excellent speed and mobile responsiveness. Low conversion potential for rebuild package, pitch advanced digital ads.", "prob": 0.20},
            "Apex Iron Fitness": {"score": "Hot", "reason": "High traffic category (Gym) with non-mobile friendly site (Overall: 50%). Loading times are slow. Rebuild prototype layout will immediately show massive value.", "prob": 0.78},
            "Glow Premium Spa & Salon": {"score": "Hot", "reason": "Site is insecure (HTTP) and lacks mobile viewports (Overall: 41%). Missing lead capture forms. Client needs SSL and responsive layout urgently.", "prob": 0.85},
            "Smile Align Dental Care": {"score": "Warm", "reason": "Modern website setup with minor performance gaps. Good ratings and high intent niche. Focus pitch on WhatsApp triggers and SEO metadata adjustments.", "prob": 0.58},
            "Heights Properties Realty": {"score": "Hot", "reason": "Extremely weak online presence (Score: 36%) with 12 broken links and missing map embeds. High probability of closure if customized real estate template is shared.", "prob": 0.82}
        }

        for lead in leads:
            q_data = qualifications_data.get(lead.business_name)
            if q_data:
                qual = AIQualification(
                    lead_id=lead.id,
                    ai_score=q_data["score"],
                    reason=q_data["reason"],
                    closing_probability=q_data["prob"]
                )
                db.add(qual)

        # 6. Proposals
        for lead in leads:
            if lead.status == "Won":
                proposal = Proposal(
                    lead_id=lead.id,
                    proposal_type="CONTRACT",
                    title="Design & Development Service SLA",
                    status="Accepted",
                    file_path=f"/static/proposals/contract_lead_{lead.id}_demo.html"
                )
                db.add(proposal)
            elif lead.status == "Proposal Sent":
                proposal = Proposal(
                    lead_id=lead.id,
                    proposal_type="PROPOSAL",
                    title="Website Optimization Proposal",
                    status="Sent",
                    file_path=f"/static/proposals/proposal_lead_{lead.id}_demo.html"
                )
                db.add(proposal)

        # 7. Outreach Logs
        logs_data = [
            {"lead_name": "Tuscany Garden Bistro", "channel": "Email", "status": "Replied", "offset": 4},
            {"lead_name": "Apex Iron Fitness", "channel": "WhatsApp", "status": "Opened", "offset": 2},
            {"lead_name": "Glow Premium Spa & Salon", "channel": "Email", "status": "Sent", "offset": 1},
            {"lead_name": "Smile Align Dental Care", "channel": "Email", "status": "Opened", "offset": 3}
        ]

        for log in logs_data:
            target_lead = next((l for l in leads if l.business_name == log["lead_name"]), None)
            if target_lead:
                out_log = OutreachLog(
                    lead_id=target_lead.id,
                    channel=log["channel"],
                    status=log["status"],
                    sent_at=datetime.now(timezone.utc) - timedelta(days=log["offset"]),
                    replied_at=datetime.now(timezone.utc) - timedelta(days=log["offset"] - 1) if log["status"] == "Replied" else None
                )
                db.add(out_log)

        print("Seeding Tasks & CRM Calendar Events...")
        # 8. Tasks
        tasks_data = [
            {"title": "Follow up on Pizza Menu design", "desc": "Call Giovanni to confirm menu pricing alignments.", "due_offset": 1, "lead_name": "Tuscany Garden Bistro", "user": admin},
            {"title": "Review Mobile Mockup with Vikram", "desc": "Present fast-loading mobile viewport demo.", "due_offset": 2, "lead_name": "Apex Iron Fitness", "user": sales},
            {"title": "Send Spa Pricing Quotation", "desc": "Draft quotation document including SSL cost.", "due_offset": 3, "lead_name": "Glow Premium Spa & Salon", "user": sales},
            {"title": "Clinical strategy discussion", "desc": "Zoom call alignment session.", "due_offset": -1, "lead_name": "Smile Align Dental Care", "user": admin}
        ]

        for t_data in tasks_data:
            target_lead = next((l for l in leads if l.business_name == t_data["lead_name"]), None)
            due_date = datetime.now(timezone.utc) + timedelta(days=t_data["due_offset"])
            task = Task(
                title=t_data["title"],
                description=t_data["desc"],
                due_date=due_date,
                status="Completed" if t_data["due_offset"] < 0 else "Pending",
                lead_id=target_lead.id if target_lead else None,
                assigned_to_id=t_data["user"].id
            )
            db.add(task)

        db.commit()
        print("Database expanded and seeded successfully with CRM elements!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
