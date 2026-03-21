"""
Geocoding endpoints backed by Google Maps.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.parcel import Parcel
from src.schemas.parcel import (
    GeocodeCandidate,
    GeocodeResponse,
    StoreGCPMetadataRequest,
    StoreGCPMetadataResponse,
)
from src.services.geocoding import get_geocoding_service
from src.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(prefix="/api/v1/parcels", tags=["geocoding"])
internal_router = APIRouter(prefix="/internal/v1", tags=["geocoding-internal"])


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    address: str | None = Query(None, description="Street address to geocode"),
    apn: str | None = Query(None, description="Assessor Parcel Number"),
    geocoding_service=Depends(get_geocoding_service),
):
    candidates = await geocoding_service.geocode(address=address, apn=apn)
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

    result = await db.execute(select(Parcel).where(Parcel.apn == request.apn))
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise NotFoundException("Parcel", request.apn)

    existing_key = (parcel.geocoding_metadata or {}).get("idempotency_key")
    if existing_key == idempotency_key:
        return StoreGCPMetadataResponse(status="success")

    parcel.geocoding_metadata = {
        **(parcel.geocoding_metadata or {}),
        "place_id": request.place_id,
        "accuracy_flag": request.location_type,
        "idempotency_key": idempotency_key,
    }
    await db.flush()
    return StoreGCPMetadataResponse(status="success")
