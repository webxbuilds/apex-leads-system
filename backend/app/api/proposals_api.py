from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Lead, Proposal
from backend.app.services.proposal_generator import create_proposal_document
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/proposals", tags=["Proposals"])

class ProposalItemSchema(BaseModel):
    description: str
    details: Optional[str] = ""
    price: float

class ProposalCreateSchema(BaseModel):
    lead_id: int
    doc_type: str = Field(..., description="PROPOSAL, QUOTATION, INVOICE, or CONTRACT")
    title: str = Field(..., description="Document display title")
    items: Optional[List[ProposalItemSchema]] = None

class StatusUpdateSchema(BaseModel):
    status: str = Field(..., description="Draft, Sent, Accepted, Declined")


@router.post("/generate")
def generate_proposal(payload: ProposalCreateSchema, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        # Convert items schema to dict
        items_dict = []
        if payload.items:
            items_dict = [item.model_dump() for item in payload.items]
            
        doc = create_proposal_document(
            lead_id=payload.lead_id,
            doc_type=payload.doc_type,
            title=payload.title,
            items=items_dict,
            db=db
        )
        
        return {
            "status": "success",
            "message": f"{payload.doc_type} generated successfully.",
            "document": doc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate proposal: {str(e)}")


@router.get("/lead/{lead_id}")
def get_lead_proposals(lead_id: int, db: Session = Depends(get_db)):
    docs = db.query(Proposal).filter(Proposal.lead_id == lead_id).order_by(Proposal.created_at.desc()).all()
    return docs


@router.put("/{proposal_id}/status")
def update_proposal_status(proposal_id: int, payload: StatusUpdateSchema, db: Session = Depends(get_db)):
    doc = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Proposal document not found")
        
    doc.status = payload.status
    db.commit()
    db.refresh(doc)
    
    # Auto update lead CRM status based on document actions
    lead = db.query(Lead).filter(Lead.id == doc.lead_id).first()
    if lead:
        if payload.status == "Sent":
            lead.status = "Proposal Sent"
        elif payload.status == "Accepted":
            if doc.proposal_type == "CONTRACT":
                lead.status = "Won"
            else:
                lead.status = "Negotiation"
        elif payload.status == "Declined":
            lead.status = "Lost"
        db.commit()
        
    return doc
