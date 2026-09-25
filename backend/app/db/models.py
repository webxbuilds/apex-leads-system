from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="Sales")  # Admin, Sales, Auditor
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_user")
    assigned_tasks = relationship("Task", back_populates="assigned_user")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    owner_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    maps_url = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True, default="India")
    postal_code = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    google_rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    business_status = Column(String, nullable=True)   # OPERATIONAL, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY
    opening_hours = Column(Text, nullable=True)        # JSON string of opening hours
    category = Column(String, nullable=True, index=True)
    status = Column(String, default="New Lead", index=True)  # New Lead, Contacted, Interested, Meeting, Proposal Sent, Negotiation, Won, Lost
    data_source = Column(String, nullable=True)        # "Google Maps API", "DuckDuckGo", "Yelp", "Manual"
    last_verified_at = Column(DateTime, nullable=True) # When real data was last fetched
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # SaaS expansions
    tags = Column(String, nullable=True)  # JSON-serialized string of tag strings (e.g. '["local", "priority"]')
    notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    assigned_user = relationship("User", back_populates="assigned_leads")
    analysis_reports = relationship("AnalysisReport", back_populates="lead", cascade="all, delete-orphan")
    ai_qualifications = relationship("AIQualification", back_populates="lead", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="lead", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="lead", cascade="all, delete-orphan")
    outreach_logs = relationship("OutreachLog", back_populates="lead", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="lead", cascade="all, delete-orphan")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    has_https = Column(Boolean, default=False)
    is_mobile_responsive = Column(Boolean, default=False)
    load_speed_seconds = Column(Float, default=0.0)
    broken_links_count = Column(Integer, default=0)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    missing_alt_tags = Column(Integer, default=0)
    has_contact_form = Column(Boolean, default=False)
    has_whatsapp_button = Column(Boolean, default=False)
    has_google_maps_embed = Column(Boolean, default=False)
    social_links = Column(Text, nullable=True)  # JSON-serialized string of found social links
    ui_score = Column(Integer, default=0)
    ux_score = Column(Integer, default=0)
    overall_score = Column(Integer, default=0)
    improvement_report_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    lead = relationship("Lead", back_populates="analysis_reports")


class AIQualification(Base):
    __tablename__ = "ai_qualifications"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    ai_score = Column(String, nullable=False)  # Hot, Warm, Cold
    reason = Column(Text, nullable=False)
    closing_probability = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    lead = relationship("Lead", back_populates="ai_qualifications")


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    email_subject = Column(String, nullable=True)
    email_content = Column(Text, nullable=True)
    whatsapp_message = Column(Text, nullable=True)
    linkedin_message = Column(Text, nullable=True)
    instagram_dm = Column(Text, nullable=True)
    cold_call_script = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    lead = relationship("Lead", back_populates="outreach_messages")


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    proposal_type = Column(String, nullable=False)  # Proposal, Quotation, Invoice, Contract
    title = Column(String, nullable=False)
    status = Column(String, default="Draft")  # Draft, Sent, Accepted, Declined
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    lead = relationship("Lead", back_populates="proposals")


class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)  # Email, WhatsApp, LinkedIn, Instagram
    status = Column(String, default="Sent")  # Sent, Opened, Replied, Bounced
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    replied_at = Column(DateTime, nullable=True)

    # Relationship
    lead = relationship("Lead", back_populates="outreach_logs")


class PortfolioDemo(Base):
    __tablename__ = "portfolio_demos"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=True)  # Optional reference to a specific lead
    niche = Column(String, nullable=False)  # Restaurant, Gym, Dentist, Clinic, Salon, School, Real Estate, Hospital, Lawyer, Ecommerce
    business_name = Column(String, nullable=False)
    demo_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default="Pending")  # Pending, Completed
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    lead = relationship("Lead", back_populates="tasks")
    assigned_user = relationship("User", back_populates="assigned_tasks")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, default="Apex Website Agency")
    company_email = Column(String, default="hello@apexweb.agency")
    smtp_host = Column(String, default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String, nullable=True)
    smtp_pass = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    n8n_webhook_url = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    branding_color = Column(String, default="#6366f1")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
