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
from src.api.health import router as health_router

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Cover Home Building Regulatory Engine",
        "version": "0.1.0",
        "status": "operational",
    }
