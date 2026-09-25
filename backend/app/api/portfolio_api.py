from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Lead, PortfolioDemo
from backend.app.services.portfolio_gen import generate_demo_portfolio, render_portfolio_html
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/portfolio", tags=["Portfolio Generator"])

class PortfolioGenerateSchema(BaseModel):
    lead_id: int
    niche: str


@router.post("/generate")
def create_portfolio(payload: PortfolioGenerateSchema, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        url = generate_demo_portfolio(payload.lead_id, payload.niche, db)
        return {
            "status": "success",
            "message": f"Interactive prototype generated for {lead.business_name} under {payload.niche} niche.",
            "preview_url": url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate portfolio: {str(e)}")


@router.get("/preview/{lead_id}", response_class=HTMLResponse)
def preview_portfolio(lead_id: int, niche: Optional[str] = None, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    target_niche = niche or lead.category or "Corporate"
    
    try:
        html_code = render_portfolio_html(lead, target_niche)
        return html_code
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile preview template: {str(e)}")
