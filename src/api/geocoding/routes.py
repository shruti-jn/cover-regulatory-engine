"""
Geocoding endpoints backed by Google Maps.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.exceptions import BadRequestException, ConflictException, NotFoundException
from src.db.session import get_db
from src.models.parcel import Parcel
from src.schemas.geocoding import (
    GeocodeCandidate,
    GeocodeResponse,
    StoreGCPMetadataRequest,
    StoreGCPMetadataResponse,
)
from src.services.geocoding import get_geocoding_service

router = APIRouter(prefix="/api/v1/parcels", tags=["geocoding"])
internal_router = APIRouter(prefix="/internal/v1", tags=["geocoding-internal"])
logger = structlog.get_logger()


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    address: str | None = Query(None, description="Street address to geocode"),
    apn: str | None = Query(None, description="Assessor Parcel Number"),
    geocoding_service=Depends(get_geocoding_service),
):
    logger.info("geocode_address_request", address=address, apn=apn)
    candidates = await geocoding_service.geocode(address=address, apn=apn)
    logger.info("geocode_address_response", address=address, apn=apn, candidate_count=len(candidates))
    return GeocodeResponse(
        candidates=[
            GeocodeCandidate(
                apn=candidate.apn,
                formatted_address=candidate.formatted_address,
                place_id=candidate.place_id,
                accuracy_flag=candidate.accuracy_flag,
            )
            for candidate in candidates
        ]
    )


@internal_router.post("/geocoding/metadata", response_model=StoreGCPMetadataResponse)
async def store_gcp_metadata(
    request: StoreGCPMetadataRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not idempotency_key.strip():
        raise BadRequestException("Idempotency key is required", field="Idempotency-Key")

    logger.info("store_gcp_metadata_request", apn=request.apn, place_id=request.place_id)
    result = await db.execute(select(Parcel).where(Parcel.apn == request.apn))
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise NotFoundException("Parcel", request.apn)

    existing_key = (parcel.geocoding_metadata or {}).get("idempotency_key")
    if existing_key == idempotency_key:
        logger.info("store_gcp_metadata_idempotent_replay", apn=request.apn, idempotency_key=idempotency_key)
        return StoreGCPMetadataResponse(status="success")
    if existing_key and existing_key != idempotency_key:
        logger.warning(
            "store_gcp_metadata_conflict",
            apn=request.apn,
            existing_idempotency_key=existing_key,
            incoming_idempotency_key=idempotency_key,
        )
        raise ConflictException("Geocoding metadata already stored for parcel")

    parcel.geocoding_metadata = {
        **(parcel.geocoding_metadata or {}),
        "place_id": request.place_id,
        "accuracy_flag": request.location_type,
        "idempotency_key": idempotency_key,
    }
    await db.flush()
    logger.info("store_gcp_metadata_success", apn=request.apn, idempotency_key=idempotency_key)
    return StoreGCPMetadataResponse(status="success")
