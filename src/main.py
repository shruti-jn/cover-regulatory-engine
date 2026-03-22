"""
Cover Home Building Regulatory Engine - FastAPI Application
"""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.middleware.request_id import RequestIdMiddleware
from src.core.middleware.logging import LoggingMiddleware
from src.core.exceptions import APIException, api_exception_handler, general_exception_handler
from src.api.health import router as health_router
from src.api.parcels.routes import router as parcels_router
from src.api.geocoding.routes import router as geocoding_router, internal_router as internal_geocoding_router
from src.api.query.routes import router as query_router
from src.api.assessments.routes import router as assessments_router, internal_router as internal_assessments_router
from src.api.admin.routes import router as admin_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        "application_starting",
        app_name="cover-regulatory-engine",
        environment=settings.ENVIRONMENT,
    )
    yield
    logger.info(
        "application_shutting_down",
        app_name="cover-regulatory-engine",
    )


app = FastAPI(
    title="Cover Home Building Regulatory Engine",
    description="Geospatial regulatory rules engine for parcel buildability assessment",
    version="0.1.0",
    lifespan=lifespan,
)

# Add exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
# Add middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(geocoding_router)
app.include_router(internal_geocoding_router)
app.include_router(parcels_router)
app.include_router(query_router)
app.include_router(assessments_router)
app.include_router(internal_assessments_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Cover Home Building Regulatory Engine",
        "version": "0.1.0",
        "status": "operational",
    }
