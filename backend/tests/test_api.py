import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add workspace to path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.db.models import Lead

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_agency.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Setup test tables
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown test tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    # Remove test file
    if os.path.exists("test_agency.db"):
        try:
            os.remove("test_agency.db")
        except Exception as e:
            print(f"Cleanup warning: {e}")


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_lead():
    payload = {
        "business_name": "Test Pizza Place",
        "owner_name": "Mario Rossi",
        "phone": "+91 99999 88888",
        "email": "mario@pizza.com",
        "website": "http://www.testpizzaplace.com",
        "category": "Restaurant",
        "city": "Noida"
    }
    response = client.post("/api/leads/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["business_name"] == "Test Pizza Place"
    assert data["status"] == "New Lead"
    assert "id" in data


def test_get_leads():
    # Insert mock data
    db = TestingSessionLocal()
    mock_lead = Lead(
        business_name="Fit Life Gym",
        category="Gym",
        city="Delhi",
        website="http://fitlifegym.com",
        status="New Lead"
    )
    db.add(mock_lead)
    db.commit()
    db.close()

    response = client.get("/api/leads/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["leads"][0]["business_name"] == "Fit Life Gym"


def test_audit_website():
    db = TestingSessionLocal()
    mock_lead = Lead(
        business_name="Style Studio Salon",
        category="Salon",
        city="Mumbai",
        website="http://stylestudiosalon.com"
    )
    db.add(mock_lead)
    db.commit()
    lead_id = mock_lead.id
    db.close()

    response = client.post(f"/api/analyzer/audit/{lead_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report" in data
    assert data["report"]["overall_score"] > 0
    assert "improvement_report_path" in data["report"]


def test_qualify_and_outreach():
    db = TestingSessionLocal()
    mock_lead = Lead(
        business_name="Smile Dental Clinic",
        category="Dentist",
        city="Bangalore",
        website="http://smiledental.com"
    )
    db.add(mock_lead)
    db.commit()
    lead_id = mock_lead.id
    db.close()

    # Qualify
    resp_qual = client.post(f"/api/ai/qualify/{lead_id}")
    assert resp_qual.status_code == 200
    data_qual = resp_qual.json()
    assert data_qual["status"] == "success"
    assert data_qual["qualification"]["ai_score"] in ["Hot", "Warm", "Cold"]

    # Outreach
    resp_outreach = client.post(f"/api/ai/outreach/{lead_id}")
    if resp_outreach.status_code != 200:
        print(f"OUTREACH FAILED DETAILS: {resp_outreach.text}")
    assert resp_outreach.status_code == 200
    data_out = resp_outreach.json()
    assert data_out["status"] == "success"
    assert "email_subject" in data_out["outreach"]
    assert "cold_call_script" in data_out["outreach"]


def test_portfolio_generator():
    db = TestingSessionLocal()
    mock_lead = Lead(
        business_name="Green Valley School",
        category="School",
        city="Pune"
    )
    db.add(mock_lead)
    db.commit()
    lead_id = mock_lead.id
    db.close()

    response = client.post("/api/portfolio/generate", json={"lead_id": lead_id, "niche": "School"})
    assert response.status_code == 200
    assert "preview_url" in response.json()
