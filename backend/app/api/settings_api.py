import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Settings
from backend.app.core.security import get_current_user, require_role
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/settings", tags=["Settings Configuration"])

class SettingsUpdateSchema(BaseModel):
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    gemini_api_key: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    logo_url: Optional[str] = None
    branding_color: Optional[str] = None


@router.get("/")
def get_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    setting = db.query(Settings).filter(Settings.id == 1).first()
    if not setting:
        # Create default config record
        setting = Settings(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.put("/")
def update_settings(
    payload: SettingsUpdateSchema,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))
):
    setting = db.query(Settings).filter(Settings.id == 1).first()
    if not setting:
        setting = Settings(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)
        
    db.commit()
    db.refresh(setting)
    
    # Sync environment variables if keys are updated
    if payload.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = payload.gemini_api_key
        
    return setting
