"""Perkle - Credit Card Benefit Tracker API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create tables and load card configs
    from app.database import Base, engine, SessionLocal
    from app.services.card_config_loader import load_card_configs
    
    # Import all models so they're registered with Base
    from app import models  # noqa: F401
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        load_card_configs(db)
    finally:
        db.close()
    
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    description="Track your credit card benefits and never miss a perk",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


# Import and include routers
from app.api import auth, benefits, cards, notifications, transactions  # noqa: E402

app.include_router(auth.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(benefits.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
