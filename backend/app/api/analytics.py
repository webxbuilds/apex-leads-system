from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.database import get_db
from backend.app.db.models import Lead, Proposal, AIQualification, OutreachLog
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

@router.get("/dashboard")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Module 7 & 11: Calculates and returns KPI summaries, pipelines,
    and conversion insights. Archived leads ('ARC') are excluded from active pipeline metrics.
    """
    active_leads_count = db.query(Lead).filter(Lead.status != "ARC").count()
    archived_leads_count = db.query(Lead).filter(Lead.status == "ARC").count()
    total_leads = active_leads_count
    
    # Standard CRM sales stages
    statuses = ["New Lead", "Contacted", "Interested", "Meeting", "Proposal Sent", "Negotiation", "Won", "Lost"]
    
    # Pipeline breakdown for active leads
    pipeline_data = db.query(Lead.status, func.count(Lead.id))\
                      .filter(Lead.status != "ARC")\
                      .group_by(Lead.status).all()
    pipeline = {status: count for status, count in pipeline_data}
    for s in statuses:
        if s not in pipeline:
            pipeline[s] = 0
            
    won_leads_count = pipeline.get("Won", 0)
    actual_revenue = won_leads_count * 25000.0
    
    proposal_sent_count = pipeline.get("Proposal Sent", 0) + pipeline.get("Negotiation", 0)
    projected_revenue = actual_revenue + (proposal_sent_count * 15000.0)

    conversion_rate = 0.0
    if total_leads > 0:
        conversion_rate = round((won_leads_count / total_leads) * 100, 1)

    # Top Performing Niches (active leads only)
    niches_chart = []
    if total_leads > 0:
        niche_stats = db.query(
            Lead.category, 
            func.count(Lead.id).label("count"),
            func.avg(AIQualification.closing_probability).label("avg_prob")
        ).outerjoin(AIQualification, Lead.id == AIQualification.lead_id)\
         .filter(Lead.status != "ARC")\
         .group_by(Lead.category)\
         .order_by(func.count(Lead.id).desc())\
         .limit(5).all()
         
        for category, count, avg_prob in niche_stats:
            if category:
                niches_chart.append({
                    "niche": category,
                    "leads_count": count,
                    "success_probability": round((avg_prob or 0.5) * 100, 1)
                })

    # Lead sources breakdown (active leads only)
    cities_chart = {}
    if total_leads > 0:
        sources_data = db.query(Lead.city, func.count(Lead.id))\
                         .filter(Lead.status != "ARC")\
                         .group_by(Lead.city).all()
        cities_chart = {city: count for city, count in sources_data if city}

    # Outreach analytics
    total_sent = db.query(OutreachLog).count()
    total_replied = db.query(OutreachLog).filter(OutreachLog.status == "Replied").count()
    total_opened = db.query(OutreachLog).filter(OutreachLog.status.in_(["Opened", "Replied"])).count()
    
    open_rate = round((total_opened / total_sent * 100), 1) if total_sent > 0 else 0.0
    reply_rate = round((total_replied / total_sent * 100), 1) if total_sent > 0 else 0.0

    trend_chart = []
    leads_trend = []

    return {
        "kpis": {
            "total_leads": total_leads,
            "archived_leads": archived_leads_count,
            "won_clients": won_leads_count,
            "conversion_rate": conversion_rate,
            "actual_revenue": actual_revenue,
            "projected_revenue": projected_revenue,
            "open_rate": open_rate,
            "reply_rate": reply_rate
        },
        "pipeline": pipeline,
        "pipeline_stats": pipeline,
        "niches_chart": niches_chart,
        "cities_chart": cities_chart,
        "trend_chart": trend_chart,
        "leads_trend": leads_trend
    }


@router.get("/outreach-logs")
def get_outreach_logs(db: Session = Depends(get_db), limit: int = 50):
    logs = db.query(OutreachLog).order_by(OutreachLog.sent_at.desc()).limit(limit).all()
    results = []
    for log in logs:
        lead = db.query(Lead).filter(Lead.id == log.lead_id).first()
        results.append({
            "id": log.id,
            "business_name": lead.business_name if lead else "Unknown",
            "channel": log.channel,
            "status": log.status,
            "sent_at": log.sent_at,
            "replied_at": log.replied_at
        })
    return results
