"""
Parcel API routes.

Implements:
- GET /api/v1/parcels/geocode - Geocode address or APN
- GET /api/v1/parcels/{apn} - Get parcel facts
- POST /internal/v1/geocoding/metadata - Store GCP metadata
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.schemas.parcel import (
    GeocodeRequest,
    GeocodeResponse,
    GeocodeCandidate,
    ParcelResponse,
    StoreGCPMetadataRequest,
    StoreGCPMetadataResponse,
    GeoJSONGeometry,
)
from src.core.exceptions import (
    NotFoundException,
    BadRequestException,
    GeocodingException,
    create_error_response,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/parcels", tags=["parcels"])
internal_router = APIRouter(prefix="/internal/v1", tags=["internal"])


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    address: Optional[str] = Query(None, description="Street address to geocode"),
    apn: Optional[str] = Query(None, description="Assessor Parcel Number"),
    db: AsyncSession = Depends(get_db),
):
    """
    Geocode an address or APN to find matching parcels.

    Returns candidates with GCP Place IDs and accuracy flags.
    """
    if not address and not apn:
        raise BadRequestException(
            "Either address or APN must be provided",
            field="query",
        )

    logger.info(
        "geocode_request",
        address=address,
        apn=apn,
    )

    # Placeholder: In production, call GCP Geocoding API
    # For now, return mock data
    candidates = [
        GeocodeCandidate(
            apn="1234-567-890",
            formatted_address="123 Main St, Los Angeles, CA 90012",
            place_id="ChIJ...",
            accuracy_flag="ROOFTOP",
        )
    ]

    return GeocodeResponse(candidates=candidates)


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


@internal_router.post("/geocoding/metadata", response_model=StoreGCPMetadataResponse)
async def store_gcp_metadata(
    request: StoreGCPMetadataRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Store GCP geocoding metadata for a parcel.

    Internal endpoint for the geocoding service.
    Requires idempotency key.
    """
    logger.info(
        "store_gcp_metadata",
        apn=request.apn,
        place_id=request.place_id,
    )

    # Placeholder: Store metadata in database
    return StoreGCPMetadataResponse(status="success")
