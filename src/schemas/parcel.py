"""
Parcel-related Pydantic v2 schemas.
"""

from typing import Optional, List
from uuid import UUID

from pydantic import Field

from src.schemas.base import BaseSchema, TimestampedSchema, UUIDSchema, SuccessResponse


class GeoCodingMetadata(BaseSchema):
    """GCP geocoding metadata."""

    place_id: Optional[str] = None
    accuracy_flag: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class GeoJSONGeometry(BaseSchema):
    """GeoJSON geometry object."""

    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class ParcelBase(BaseSchema):
    """Base parcel schema."""

    apn: str = Field(..., description="Assessor Parcel Number")
    address: str = Field(..., description="Full street address")


class ParcelCreate(ParcelBase):
    """Schema for creating a parcel."""

    geocoding_metadata: Optional[GeoCodingMetadata] = None


class ParcelResponse(ParcelBase, UUIDSchema, TimestampedSchema):
    """Parcel response schema."""

    geometry: GeoJSONGeometry
    geocoding_metadata: Optional[GeoCodingMetadata] = None


class GeocodeRequest(BaseSchema):
    """Request to geocode an address or APN."""

    address: Optional[str] = Field(None, description="Street address to geocode")
    apn: Optional[str] = Field(None, description="Assessor Parcel Number")


class GeocodeCandidate(BaseSchema):
    """Geocoding result candidate."""

    apn: str
    formatted_address: str
    place_id: str
    accuracy_flag: str = Field(..., description="ROOFTOP or INTERPOLATED")


class GeocodeResponse(BaseSchema):
    """Geocoding response with candidates."""

    candidates: List[GeocodeCandidate]


class StoreGCPMetadataRequest(BaseSchema):
    """Request to store GCP geocoding metadata."""

    apn: str
    place_id: str
    location_type: str


class StoreGCPMetadataResponse(SuccessResponse):
    """Response for storing GCP metadata."""

    pass
