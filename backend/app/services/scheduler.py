import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from backend.app.db.database import SessionLocal
from backend.app.db.models import Lead, AnalysisReport, AIQualification
from backend.app.services.scraper import scrape_leads
from backend.app.services.analyzer import analyze_website
from backend.app.services.ai_service import qualify_lead, generate_outreach_materials

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_auto_nurture_pipeline():
    """
    Scans the database for new leads, automatically runs the website audit,
    AI qualifications, and outreach generation pipeline.
    """
    logger.info("Running automatic background lead nurturing pipeline...")
    db: Session = SessionLocal()
    try:
        # Find leads with no audit report
        new_leads = db.query(Lead).all()
        nurtured_count = 0
        
        for lead in new_leads:
            # Check if this lead already has an analysis report
            report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead.id).first()
            if not report and lead.website:
                try:
                    logger.info(f"Background nurturing for lead: {lead.business_name}")
                    # 1. Audit website
                    analyze_website(lead.id, db)
                    # 2. Qualify lead
                    qualify_lead(lead.id, db)
                    # 3. Generate outreach materials
                    generate_outreach_materials(lead.id, db)
                    nurtured_count += 1
                except Exception as e:
                    logger.error(f"Error auto-nurturing lead {lead.business_name}: {e}")
                    
        logger.info(f"Lead nurturing complete. Nurtured {nurtured_count} leads.")
    finally:
        db.close()


def run_daily_scraping_job():
    """
    Background job that automatically scrapes leads for target niches to keep
    the pipeline active daily.
    """
    logger.info("Starting scheduled daily scraping job...")
    db: Session = SessionLocal()
    
    niches = ["Restaurant", "Gym", "Salon", "Dentist", "Clinic", "School", "Real Estate"]
    cities = ["Noida", "Delhi", "Mumbai", "Bangalore", "Pune", "Gurugram"]
    
    niche = niches[len(db.query(Lead).all()) % len(niches)]
    city = cities[len(db.query(Lead).all()) % len(cities)]
    
    try:
        leads = scrape_leads("Google Maps", niche, city, limit=5, db=db)
        logger.info(f"Daily scraping job completed. Saved {len(leads)} leads for {niche} in {city}.")
        
        # Run nurture pipeline immediately for newly scraped leads
        run_auto_nurture_pipeline()
    except Exception as e:
        logger.error(f"Error running daily scraping job: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Starts the background scheduler task queue.
    """
    if not scheduler.running:
        # Run lead nurture check every 15 minutes
        scheduler.add_job(run_auto_nurture_pipeline, 'interval', minutes=15, id='nurture_pipeline')
        # Run daily scraping scraper every day at midnight (or simulated interval here)
        scheduler.add_job(run_daily_scraping_job, 'cron', hour=0, minute=0, id='daily_scraping')
        
        scheduler.start()
        logger.info("APScheduler Background Tasks successfully started.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler Background Tasks successfully stopped.")
