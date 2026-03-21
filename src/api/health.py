"""
Health check endpoints.
"""

from fastapi import APIRouter, status

router = APIRouter(prefix="/health")


@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "cover-regulatory-engine",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check for Railway."""
    return {
        "status": "ready",
        "service": "cover-regulatory-engine",
    }
