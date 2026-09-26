import csv
import io
import json
import os
import sqlite3
import tempfile
import shutil
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, and_, not_
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Lead, AnalysisReport, AIQualification, User, OutreachMessage
from backend.app.services.scraper import scrape_leads
from backend.app.core.security import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["Leads"])

class LeadSchema(BaseModel):
    business_name: str
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    address: Optional[str] = None
    google_rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = "New Lead"
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None

class LeadUpdateSchema(BaseModel):
    business_name: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    address: Optional[str] = None
    google_rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None

class ScrapeRequest(BaseModel):
    source: str = Field(..., description="Google Maps, Justdial, or IndiaMART")
    category: str = Field(..., description="e.g. Restaurant, Gym, Dentist")
    city: str = Field(..., description="e.g. Delhi, Noida")
    limit: Optional[int] = 10


@router.get("/")
def get_all_leads(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    website_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    base_query = db.query(Lead)
    
    # Filter by assignment for non-admins
    if current_user.role != "Admin":
        base_query = base_query.filter(Lead.assigned_to_id == current_user.id)

    no_website_condition = or_(
        Lead.website.is_(None),
        Lead.website == "",
        Lead.website == "Not Publicly Available",
        Lead.website.ilike("none"),
        Lead.website.ilike("null"),
        Lead.tags.like('%"MISSING_WEBSITE"%')
    )
    
    # Precompute counts for pipeline badges
    no_website_count = base_query.filter(no_website_condition).count()
    has_website_count = base_query.filter(~no_website_condition).count()

    query = base_query
    if status:
        query = query.filter(Lead.status == status)
    if category:
        query = query.filter(Lead.category == category)
    if city:
        query = query.filter(Lead.city == city)
    if search:
        query = query.filter(
            (Lead.business_name.ilike(f"%{search}%")) |
            (Lead.owner_name.ilike(f"%{search}%")) |
            (Lead.city.ilike(f"%{search}%"))
        )
    if tag:
        query = query.filter(Lead.tags.like(f'%"{tag}"%'))
    if website_filter == "no_website":
        query = query.filter(no_website_condition)
    elif website_filter == "has_website":
        query = query.filter(~no_website_condition)
        
    total = query.count()
    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for lead in leads:
        report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead.id).order_by(AnalysisReport.created_at.desc()).first()
        qualification = db.query(AIQualification).filter(AIQualification.lead_id == lead.id).order_by(AIQualification.created_at.desc()).first()
        
        assigned_user = db.query(User).filter(User.id == lead.assigned_to_id).first() if lead.assigned_to_id else None
        
        # Safe JSON loading
        parsed_tags = []
        if lead.tags:
            try:
                parsed_tags = json.loads(lead.tags)
            except:
                parsed_tags = []

        has_web = bool(lead.website and lead.website not in ["Not Publicly Available", "none", "null", ""])

        results.append({
            "id": lead.id,
            "business_name": lead.business_name,
            "owner_name": lead.owner_name,
            "phone": lead.phone,
            "whatsapp_number": lead.whatsapp_number or "Not Publicly Available",
            "email": lead.email,
            "website": lead.website,
            "has_website": has_web,
            "website_status": "Has Website" if has_web else "No Website",
            "address": lead.address,
            "google_rating": lead.google_rating,
            "reviews_count": lead.reviews_count,
            "category": lead.category,
            "city": lead.city,
            "status": lead.status,
            "tags": parsed_tags,
            "notes": lead.notes,
            "follow_up_date": lead.follow_up_date,
            "assigned_to_id": lead.assigned_to_id,
            "assigned_to_name": assigned_user.full_name if assigned_user else None,
            "created_at": lead.created_at,
            "website_audit_score": report.overall_score if report else None,
            "ai_score": qualification.ai_score if qualification else None,
            "closing_probability": qualification.closing_probability if qualification else None
        })
        
    return {
        "total": total,
        "no_website_count": no_website_count,
        "has_website_count": has_website_count,
        "leads": results
    }


@router.get("/export")
def export_leads_csv(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Streams CSV containing CRM leads data.
    """
    query = db.query(Lead)
    if current_user.role != "Admin":
        query = query.filter(Lead.assigned_to_id == current_user.id)
        
    leads = query.all()
    
    # In-memory CSV stream
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "ID", "Business Name", "Owner Name", "Category", "City", 
        "Website", "Phone", "Email", "Address", "Google Rating", 
        "Reviews Count", "Status", "Tags", "Notes"
    ])
    
    for lead in leads:
        # Load tags
        tag_str = ""
        if lead.tags:
            try:
                tag_str = ", ".join(json.loads(lead.tags))
            except:
                tag_str = lead.tags
                
        writer.writerow([
            lead.id, lead.business_name, lead.owner_name or "", lead.category or "", lead.city or "",
            lead.website or "", lead.phone or "", lead.email or "", lead.address or "", lead.google_rating or "",
            lead.reviews_count or "", lead.status, tag_str, lead.notes or ""
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )


@router.get("/export/excel")
def export_leads_excel(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Streams Excel (.xlsx) file containing B2B leads data.
    """
    query = db.query(Lead)
    if current_user.role != "Admin":
        query = query.filter(Lead.assigned_to_id == current_user.id)
    leads = query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CRM Leads"
    
    # Header styling
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    headers = [
        "ID", "Business Name", "Owner Name", "Category", "City", "State", "Country", "Postal Code",
        "Website", "Phone", "WhatsApp Number", "Email", "Instagram", "Facebook", "LinkedIn",
        "Google Maps URL", "Latitude", "Longitude", "Google Rating", "Reviews Count", "Business Status", "Opening Hours",
        "CRM Status", "Last Verified At", "Created At"
    ]
    
    ws.append(headers)
    
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        
    for lead in leads:
        ws.append([
            lead.id,
            lead.business_name,
            lead.owner_name or "Not Publicly Available",
            lead.category or "Not Publicly Available",
            lead.city or "",
            lead.state or "",
            lead.country or "",
            lead.postal_code or "",
            lead.website or "Not Publicly Available",
            lead.phone or "Not Publicly Available",
            lead.whatsapp_number or "Not Publicly Available",
            lead.email or "Not Publicly Available",
            lead.instagram or "Not Publicly Available",
            lead.facebook or "Not Publicly Available",
            lead.linkedin or "Not Publicly Available",
            lead.maps_url or "",
            lead.latitude,
            lead.longitude,
            lead.google_rating,
            lead.reviews_count or 0,
            lead.business_status or "OPERATIONAL",
            lead.opening_hours or "Not Publicly Available",
            lead.status,
            lead.last_verified_at.strftime("%Y-%m-%d %H:%M:%S") if lead.last_verified_at else "",
            lead.created_at.strftime("%Y-%m-%d %H:%M:%S") if lead.created_at else ""
        ])
        
    for col in ws.columns:
        max_len = 0
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    excel_stream = io.BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads_export.xlsx"}
    )


@router.get("/export/sqlite")
def export_leads_sqlite(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Streams a SQLite database file containing the exported CRM leads.
    """
    query = db.query(Lead)
    if current_user.role != "Admin":
        query = query.filter(Lead.assigned_to_id == current_user.id)
    leads = query.all()
    
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "leads_export.db")
    
    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY,
            business_name TEXT NOT NULL,
            owner_name TEXT,
            phone TEXT,
            whatsapp_number TEXT,
            email TEXT,
            website TEXT,
            instagram TEXT,
            facebook TEXT,
            linkedin TEXT,
            maps_url TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            postal_code TEXT,
            latitude REAL,
            longitude REAL,
            google_rating REAL,
            reviews_count INTEGER,
            business_status TEXT,
            opening_hours TEXT,
            category TEXT,
            status TEXT,
            data_source TEXT,
            last_verified_at TEXT,
            created_at TEXT
        )
        """)
        
        for lead in leads:
            cursor.execute("""
            INSERT INTO leads (
                id, business_name, owner_name, phone, whatsapp_number, email, website,
                instagram, facebook, linkedin, maps_url, address, city, state, country, postal_code,
                latitude, longitude, google_rating, reviews_count, business_status, opening_hours,
                category, status, data_source, last_verified_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.id,
                lead.business_name,
                lead.owner_name,
                lead.phone,
                lead.whatsapp_number,
                lead.email,
                lead.website,
                lead.instagram,
                lead.facebook,
                lead.linkedin,
                lead.maps_url,
                lead.address,
                lead.city,
                lead.state,
                lead.country,
                lead.postal_code,
                lead.latitude,
                lead.longitude,
                lead.google_rating,
                lead.reviews_count,
                lead.business_status,
                lead.opening_hours,
                lead.category,
                lead.status,
                lead.data_source,
                lead.last_verified_at.isoformat() if lead.last_verified_at else None,
                lead.created_at.isoformat() if lead.created_at else None
            ))
            
        conn.commit()
        conn.close()
        
        with open(temp_db_path, "rb") as f:
            db_bytes = f.read()
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
            
    return StreamingResponse(
        io.BytesIO(db_bytes),
        media_type="application/x-sqlite3",
        headers={"Content-Disposition": "attachment; filename=leads_export.db"}
    )


@router.get("/export/postgresql")
def export_leads_postgresql(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Streams a raw PostgreSQL SQL setup and insertion script containing the CRM leads.
    """
    query = db.query(Lead)
    if current_user.role != "Admin":
        query = query.filter(Lead.assigned_to_id == current_user.id)
    leads = query.all()
    
    sql_lines = [
        "-- PostgreSQL Lead Export Script",
        f"-- Generated on: {datetime.now(timezone.utc).isoformat()}\n",
        """CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255),
    phone VARCHAR(50),
    whatsapp_number VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    instagram VARCHAR(255),
    facebook VARCHAR(255),
    linkedin VARCHAR(255),
    maps_url TEXT,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    postal_code VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    google_rating DOUBLE PRECISION,
    reviews_count INTEGER,
    business_status VARCHAR(50),
    opening_hours TEXT,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'New Lead',
    data_source VARCHAR(100),
    last_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);\n"""
    ]
    
    def escape_val(val):
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        val_str = str(val).replace("'", "''")
        return f"'{val_str}'"
        
    for lead in leads:
        cols = [
            "id", "business_name", "owner_name", "phone", "whatsapp_number", "email", "website",
            "instagram", "facebook", "linkedin", "maps_url", "address", "city", "state", "country", "postal_code",
            "latitude", "longitude", "google_rating", "reviews_count", "business_status", "opening_hours",
            "category", "status", "data_source", "last_verified_at", "created_at"
        ]
        vals = [
            escape_val(lead.id),
            escape_val(lead.business_name),
            escape_val(lead.owner_name),
            escape_val(lead.phone),
            escape_val(lead.whatsapp_number),
            escape_val(lead.email),
            escape_val(lead.website),
            escape_val(lead.instagram),
            escape_val(lead.facebook),
            escape_val(lead.linkedin),
            escape_val(lead.maps_url),
            escape_val(lead.address),
            escape_val(lead.city),
            escape_val(lead.state),
            escape_val(lead.country),
            escape_val(lead.postal_code),
            escape_val(lead.latitude),
            escape_val(lead.longitude),
            escape_val(lead.google_rating),
            escape_val(lead.reviews_count),
            escape_val(lead.business_status),
            escape_val(lead.opening_hours),
            escape_val(lead.category),
            escape_val(lead.status),
            escape_val(lead.data_source),
            escape_val(lead.last_verified_at.isoformat() if lead.last_verified_at else None),
            escape_val(lead.created_at.isoformat() if lead.created_at else None)
        ]
        sql_lines.append(f"INSERT INTO leads ({', '.join(cols)}) VALUES ({', '.join(vals)});")
        
    sql_content = "\n".join(sql_lines)
    return StreamingResponse(
        io.BytesIO(sql_content.encode("utf-8")),
        media_type="application/sql",
        headers={"Content-Disposition": "attachment; filename=leads_export_postgresql.sql"}
    )


@router.post("/import")
def import_leads_csv(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Parses and imports uploaded CSV files into the Lead database.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        content = file.file.read().decode("utf-8")
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
        
        imported_count = 0
        for row in reader:
            # Map headers (case insensitive / fuzzy check)
            biz_name = row.get("Business Name") or row.get("business_name")
            if not biz_name:
                continue # name is required
                
            lead = Lead(
                business_name=biz_name,
                owner_name=row.get("Owner Name") or row.get("owner_name"),
                category=row.get("Category") or row.get("category"),
                city=row.get("City") or row.get("city"),
                website=row.get("Website") or row.get("website"),
                phone=row.get("Phone") or row.get("phone"),
                email=row.get("Email") or row.get("email"),
                address=row.get("Address") or row.get("address"),
                status=row.get("Status") or row.get("status") or "New Lead",
                notes=row.get("Notes") or row.get("notes"),
                assigned_to_id=current_user.id
            )
            
            # Save tags if provided
            tags_input = row.get("Tags") or row.get("tags")
            if tags_input:
                parsed_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                lead.tags = json.dumps(parsed_tags)
                
            db.add(lead)
            imported_count += 1
            
        db.commit()
        return {"status": "success", "imported_count": imported_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process CSV file: {str(e)}")


@router.get("/{lead_id}")
def get_lead_details(lead_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Check permissions
    if current_user.role != "Admin" and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this lead profile.")
        
    report = db.query(AnalysisReport).filter(AnalysisReport.lead_id == lead_id).order_by(AnalysisReport.created_at.desc()).first()
    qualification = db.query(AIQualification).filter(AIQualification.lead_id == lead_id).order_by(AIQualification.created_at.desc()).first()
    outreach = db.query(OutreachMessage).filter(OutreachMessage.lead_id == lead_id).order_by(OutreachMessage.created_at.desc()).first()
    
    # Safe tags parsing
    parsed_tags = []
    if lead.tags:
        try:
            parsed_tags = json.loads(lead.tags)
        except:
            parsed_tags = []
            
    assigned_user = db.query(User).filter(User.id == lead.assigned_to_id).first() if lead.assigned_to_id else None

    return {
        "lead": {
            "id": lead.id,
            "business_name": lead.business_name,
            "owner_name": lead.owner_name,
            "phone": lead.phone,
            "whatsapp_number": lead.whatsapp_number or "Not Publicly Available",
            "email": lead.email,
            "website": lead.website,
            "instagram": lead.instagram,
            "facebook": lead.facebook,
            "address": lead.address,
            "google_rating": lead.google_rating,
            "reviews_count": lead.reviews_count,
            "category": lead.category,
            "city": lead.city,
            "status": lead.status,
            "tags": parsed_tags,
            "notes": lead.notes,
            "follow_up_date": lead.follow_up_date,
            "assigned_to_id": lead.assigned_to_id,
            "assigned_to_name": assigned_user.full_name if assigned_user else None,
            "created_at": lead.created_at
        },
        "audit_report": report,
        "ai_qualification": qualification,
        "outreach_materials": outreach
    }


@router.post("/")
def create_lead(payload: LeadSchema, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    data = payload.model_dump()
    # Serialize tags
    tags_list = data.pop("tags", None)
    serialized_tags = json.dumps(tags_list) if tags_list else None
    
    if not data.get("assigned_to_id"):
        data["assigned_to_id"] = current_user.id
        
    lead = Lead(
        **data,
        tags=serialized_tags
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.put("/{lead_id}")
def update_lead(lead_id: int, payload: LeadUpdateSchema, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Check permissions
    if current_user.role != "Admin" and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    update_data = payload.model_dump(exclude_unset=True)
    
    # Serialize tags if updated
    if "tags" in update_data:
        tags_list = update_data.pop("tags")
        lead.tags = json.dumps(tags_list) if tags_list else None
        
    for key, value in update_data.items():
        setattr(lead, key, value)
        
    db.commit()
    db.refresh(lead)
    return lead


# Active scrape tasks tracking in memory
active_scrapes = {}

@router.delete("/bulk/clear-all")
def clear_all_leads(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Deletes all leads and records them in ClearedLead so they never reappear in any search."""
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only administrators can clear all leads.")
    from backend.app.db.models import AnalysisReport, AIQualification, OutreachMessage, Proposal, OutreachLog, PortfolioDemo, Task, ClearedLead
    from backend.app.services.scraper import DEFAULT_HISTORICAL_CLEARED, normalize_phone

    # 1. Record all current leads in ClearedLead
    current_leads = db.query(Lead).all()
    for lead in current_leads:
        clean_name = lead.business_name.strip().lower()
        exists = db.query(ClearedLead).filter(ClearedLead.business_name_clean == clean_name).first()
        if not exists:
            db.add(ClearedLead(
                business_name_clean=clean_name,
                business_name=lead.business_name,
                phone=normalize_phone(lead.phone),
                website=lead.website,
                maps_url=lead.maps_url,
                city=lead.city,
                category=lead.category
            ))

    # 2. Also register historical demo leads so they never reappear
    for hist_name in DEFAULT_HISTORICAL_CLEARED:
        exists = db.query(ClearedLead).filter(ClearedLead.business_name_clean == hist_name).first()
        if not exists:
            db.add(ClearedLead(
                business_name_clean=hist_name,
                business_name=hist_name.title()
            ))

    db.query(AnalysisReport).delete()
    db.query(AIQualification).delete()
    db.query(OutreachMessage).delete()
    db.query(Proposal).delete()
    db.query(OutreachLog).delete()
    db.query(PortfolioDemo).delete()
    db.query(Task).delete()
    deleted_count = db.query(Lead).delete()
    db.commit()
    return {
        "status": "success", 
        "message": f"Successfully cleared {deleted_count} leads and permanently prevented them from reappearing in future searches."
    }


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if current_user.role != "Admin" and lead.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    from backend.app.db.models import ClearedLead
    from backend.app.services.scraper import normalize_phone
    clean_name = lead.business_name.strip().lower()
    exists = db.query(ClearedLead).filter(ClearedLead.business_name_clean == clean_name).first()
    if not exists:
        db.add(ClearedLead(
            business_name_clean=clean_name,
            business_name=lead.business_name,
            phone=normalize_phone(lead.phone),
            website=lead.website,
            maps_url=lead.maps_url,
            city=lead.city,
            category=lead.category
        ))

    db.delete(lead)
    db.commit()
    return {"status": "success", "message": f"Lead {lead_id} successfully deleted and permanently prevented from reappearing."}


def run_background_scrape(task_id: str, source: str, category: str, city: str, limit: int):
    from backend.app.db.database import SessionLocal
    import logging
    logger = logging.getLogger(__name__)
    db_session = SessionLocal()
    try:
        if task_id in active_scrapes:
            active_scrapes[task_id]["status"] = "running"
            active_scrapes[task_id]["progress_message"] = f"Searching for {category} in {city} without websites..."
            
        leads = scrape_leads(source=source, category=category, city=city, limit=limit, db=db_session)
        found_count = len(leads) if leads else 0

        # Mark completed IMMEDIATELY so the frontend and user get the leads without delay
        if task_id in active_scrapes:
            active_scrapes[task_id]["status"] = "completed"
            active_scrapes[task_id]["leads_found"] = found_count
            active_scrapes[task_id]["progress_message"] = f"Finished! Found {found_count} quality leads without websites."
            active_scrapes[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Generate AI qualifications and outreach asynchronously in the background
        from backend.app.services.ai_service import generate_outreach_materials, qualify_lead
        for l in leads:
            try:
                lead_id = l.id if hasattr(l, 'id') else l.get('id')
                if lead_id:
                    qualify_lead(lead_id, db_session)
                    generate_outreach_materials(lead_id, db_session)
            except Exception as ai_err:
                logger.warning(f"Could not auto-generate outreach for scraped lead: {ai_err}")
    except Exception as e:
        logger.error(f"Background scraping task {task_id} failed: {e}")
        if task_id in active_scrapes:
            active_scrapes[task_id]["status"] = "failed"
            active_scrapes[task_id]["error"] = str(e)
            active_scrapes[task_id]["progress_message"] = f"Scraper error: {str(e)}"
    finally:
        db_session.close()


@router.post("/scrape")
def trigger_scrape(payload: ScrapeRequest, background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    import time
    task_id = f"scrape_{int(time.time() * 1000)}"
    active_scrapes[task_id] = {
        "task_id": task_id,
        "status": "running",
        "source": payload.source,
        "category": payload.category,
        "city": payload.city,
        "limit": payload.limit,
        "progress_message": f"Initializing quality scraper for {payload.category} in {payload.city}...",
        "leads_found": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(
        run_background_scrape, 
        task_id=task_id,
        source=payload.source, 
        category=payload.category, 
        city=payload.city, 
        limit=payload.limit
    )
    return {
        "status": "queued",
        "task_id": task_id,
        "message": f"Scraping task initiated in background for {payload.category} in {payload.city} from {payload.source}."
    }


@router.get("/scrape/status/{task_id}")
def get_scrape_status(task_id: str, current_user = Depends(get_current_user)):
    """Allows frontend to poll scraper progress and know when finding leads is complete."""
    if task_id not in active_scrapes:
        return {
            "status": "completed", 
            "task_id": task_id, 
            "leads_found": 0, 
            "progress_message": "Scraper task completed."
        }
    return active_scrapes[task_id]
