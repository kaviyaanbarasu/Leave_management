from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, get_db
from app.seed import seed_database
from app.routers import (
    employees_router,
    locations_router,
    leave_types_router,
    holidays_router,
    accrual_policies_router,
    leave_requests_router,
    auth_router,
    approvals_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    # Seed initial demo data
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Dynamic PTO & Leave Management System API",
    description="A comprehensive, multi-location PTO and leave management system MVP with location-aware holidays, configurable weekend rules, dynamic accrual policies, and atomic pending reservation.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(leave_types_router, prefix="/api")
app.include_router(holidays_router, prefix="/api")
app.include_router(accrual_policies_router, prefix="/api")
app.include_router(leave_requests_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to Dynamic PTO & Leave Management System API",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
    }


@app.post("/api/seed", tags=["Admin"])
def trigger_seed(db: Session = Depends(get_db)):
    seed_database(db)
    return {"message": "Database successfully seeded with demo data"}
