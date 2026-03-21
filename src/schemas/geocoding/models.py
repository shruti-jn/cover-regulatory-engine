"""
Geocoding-specific Pydantic schemas.
"""

from typing import Literal

from pydantic import Field

from src.schemas.base import BaseSchema, SuccessResponse

AccuracyFlag = Literal["ROOFTOP", "INTERPOLATED"]


class GeocodeCandidate(BaseSchema):
    """Geocoding result candidate."""

    apn: str
    formatted_address: str
    place_id: str
    accuracy_flag: AccuracyFlag = Field(..., description="ROOFTOP or INTERPOLATED")


class GeocodeResponse(BaseSchema):
    """Geocoding response with candidates."""

    candidates: list[GeocodeCandidate]


class StoreGCPMetadataRequest(BaseSchema):
    """Request to store GCP geocoding metadata."""

    apn: str
    place_id: str
    location_type: AccuracyFlag


class StoreGCPMetadataResponse(SuccessResponse):
    """Response for storing GCP metadata."""

    pass
