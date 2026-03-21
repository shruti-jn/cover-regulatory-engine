"""
Parcel API routes.

Implements:
- GET /api/v1/parcels/{apn} - Get parcel facts
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.schemas.parcel import (
    ParcelResponse,
)
from src.services.parcels import get_parcel_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/parcels", tags=["parcels"])


@router.get("/{apn}", response_model=ParcelResponse)
async def get_parcel_facts(
    apn: str,
    db: AsyncSession = Depends(get_db),
    parcel_service=Depends(get_parcel_service),
):
    """
    Get parcel facts by APN.

    Returns parcel metadata and geometry in GeoJSON format.
    """
    logger.info(
        "get_parcel_facts",
        apn=apn,
    )
    response = await parcel_service.get_parcel_facts(db=db, apn=apn)
    logger.info("get_parcel_facts_success", apn=apn, parcel_id=str(response.id))
    return response
