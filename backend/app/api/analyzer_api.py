from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Lead, AnalysisReport
from backend.app.services.analyzer import analyze_website

router = APIRouter(prefix="/analyzer", tags=["Analyzer"])

@router.post("/audit/{lead_id}")
def audit_lead_website(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if not lead.website:
        raise HTTPException(status_code=400, detail="Lead does not have an active website URL configured.")
        
    try:
        report = analyze_website(lead.id, db)
        return {
            "status": "success",
            "message": f"Website analysis completed successfully for {lead.business_name}",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to audit website: {str(e)}")


@router.get("/reports/{lead_id}")
def get_audit_reports(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    reports = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead_id).order_by(AnalysisReport.created_at.desc()).all()
    return reports
