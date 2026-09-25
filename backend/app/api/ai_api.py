from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.app.db.database import get_db
from backend.app.db.models import Lead, AIQualification, OutreachMessage
from backend.app.services.ai_service import qualify_lead, generate_outreach_materials

router = APIRouter(prefix="/ai", tags=["AI Automation"])

@router.post("/qualify/{lead_id}")
def run_ai_qualification(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        qualification = qualify_lead(lead.id, db)
        return {
            "status": "success",
            "message": f"Lead {lead.business_name} qualified by AI.",
            "qualification": qualification
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to qualify lead: {str(e)}")


@router.post("/outreach/{lead_id}")
def create_outreach_messages(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        outreach = generate_outreach_materials(lead.id, db)
        return {
            "status": "success",
            "message": f"Personalized outreach materials drafted for {lead.business_name}.",
            "outreach": outreach
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outreach materials: {str(e)}")
        
        
@router.post("/outreach/batch-generate-all")
def batch_generate_outreach(db: Session = Depends(get_db)):
    try:
        from backend.app.services.ai_service import generate_all_outreach_for_database
        count = generate_all_outreach_for_database(db)
        return {
            "status": "success",
            "message": f"Successfully generated tailored 3-part outreach messages for {count} leads.",
            "processed_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch generate outreach: {str(e)}")


@router.get("/outreach/{lead_id}")
def get_outreach_materials(lead_id: int, db: Session = Depends(get_db)):
    outreach = db.query(OutreachMessage).filter(OutreachMessage.lead_id == lead_id).order_by(OutreachMessage.created_at.desc()).first()
    if not outreach:
        raise HTTPException(status_code=404, detail="No outreach templates drafted for this lead yet.")
    return outreach


class CustomPitchRequest(BaseModel):
    channel: str = "whatsapp"
    custom_instructions: Optional[str] = ""

@router.post("/generate-pitch/{lead_id}")
def create_custom_pitch(lead_id: int, payload: CustomPitchRequest, db: Session = Depends(get_db)):
    from backend.app.services.ai_service import generate_custom_ai_pitch
    try:
        result = generate_custom_ai_pitch(lead_id, payload.channel, payload.custom_instructions or "", db)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate custom AI pitch: {str(e)}")

