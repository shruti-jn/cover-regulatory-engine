"""
Parcel API routes.

Implements:
- GET /api/v1/parcels/{apn} - Get parcel facts
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.schemas.parcel import (
    ParcelResponse,
    GeoJSONGeometry,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/parcels", tags=["parcels"])


@router.get("/{apn}", response_model=ParcelResponse)
async def get_parcel_facts(
    apn: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get parcel facts by APN.

    Returns parcel metadata and geometry in GeoJSON format.
    """
    logger.info(
        "get_parcel_facts",
        apn=apn,
    )

    # Placeholder: Query database for parcel
    # For now, return mock data
    return ParcelResponse(
        id=UUID("12345678-1234-1234-1234-123456789abc"),
        apn=apn,
        address="123 Main St, Los Angeles, CA 90012",
        geometry=GeoJSONGeometry(
            type="Polygon",
            coordinates=[[[-118.25, 34.05], [-118.24, 34.05], [-118.24, 34.06], [-118.25, 34.06], [-118.25, 34.05]]],
        ),
        geocoding_metadata={
            "place_id": "ChIJ...",
            "accuracy_flag": "ROOFTOP",
            "lat": 34.0522,
            "lng": -118.2437,
        },
        created_at="2026-03-21T12:00:00",
        updated_at="2026-03-21T12:00:00",
    )
