import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import database configs
from backend.app.db.database import engine, Base
# Import routers
from backend.app.api.leads import router as leads_router
from backend.app.api.analyzer_api import router as analyzer_router
from backend.app.api.ai_api import router as ai_router
from backend.app.api.proposals_api import router as proposals_router
from backend.app.api.portfolio_api import router as portfolio_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.auth import router as auth_router
from backend.app.api.settings_api import router as settings_router
from backend.app.api.tasks_api import router as tasks_router
# Import background scheduler
from backend.app.services.scheduler import start_scheduler, stop_scheduler

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create database tables if they do not exist
logger.info("Initializing database models...")
Base.metadata.create_all(bind=engine)

# Create static directories
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "reports"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "proposals"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FastAPI application...")
    # Initialize background scheduler tasks
    start_scheduler()
    yield
    logger.info("Shutting down FastAPI application...")
    # Shut down background tasks cleanly
    stop_scheduler()


app = FastAPI(
    title="AI Website Agency Operating System API",
    description="Backend services for scraping, website auditing, AI qualifications, CRM syncing, proposal automation, and portfolio generators.",
    version="1.0.0",
    lifespan=lifespan
)

def ensure_default_admin():
    try:
        from backend.app.db.database import SessionLocal
        from backend.app.db.models import User
        from backend.app.core.security import hash_password
        db = SessionLocal()
        admin = db.query(User).filter(User.email == "admin@apex.com").first()
        if not admin:
            admin = User(
                email="admin@apex.com",
                hashed_password=hash_password("password123"),
                full_name="Admin User",
                role="Admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Auto-seeded default admin user: admin@apex.com")
        db.close()
    except Exception as e:
        logger.error(f"Error ensuring default admin: {e}")

# Call ensure default admin
ensure_default_admin()

# CORS middleware configuration: supports all web and preview origins dynamically
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount static asset server (HTML reports and PDFs)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(analyzer_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(proposals_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Website Agency System API",
        "timestamp": os.popen("echo %DATE% %TIME%").read().strip() if os.name == 'nt' else os.popen("date").read().strip()
    }
