"""
Parcel lookup services.
"""

from __future__ import annotations

from shapely.geometry import mapping
import structlog
from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictException, NotFoundException
from src.models.parcel import Parcel
from src.schemas.parcel import GeoCodingMetadata, GeoJSONGeometry, ParcelResponse

logger = structlog.get_logger()


class ParcelService:
    """Service for parcel facts retrieval."""

    async def get_parcel_facts(self, db: AsyncSession, apn: str) -> ParcelResponse:
        stmt = select(Parcel).where(Parcel.apn == apn).limit(2)
        result = await db.execute(stmt)
        parcels = list(result.scalars())

        if not parcels:
            logger.warning("parcel_facts_not_found", apn=apn)
            raise NotFoundException("Parcel", apn)
        if len(parcels) > 1:
            logger.error("parcel_facts_duplicate_apn", apn=apn, match_count=len(parcels))
            raise ConflictException("Multiple parcels found for APN")

        parcel = parcels[0]
        geometry = self._serialize_geometry(parcel)
        geocoding_metadata = (parcel.geocoding_metadata or {}).copy()

        logger.info("parcel_facts_loaded", apn=apn, parcel_id=str(parcel.id))
        return ParcelResponse(
            id=parcel.id,
            apn=parcel.apn,
            address=parcel.address,
            geometry=geometry,
            geocoding_metadata=GeoCodingMetadata(**geocoding_metadata) if geocoding_metadata else None,
            created_at=parcel.created_at,
            updated_at=parcel.updated_at,
        )

    def _serialize_geometry(self, parcel: Parcel) -> GeoJSONGeometry:
        shape = to_shape(parcel.geometry)
        geojson = mapping(shape)
        return GeoJSONGeometry.model_validate(geojson)


_service: ParcelService | None = None


def get_parcel_service() -> ParcelService:
    global _service
    if _service is None:
        _service = ParcelService()
    return _service
