"""
Google Maps geocoding integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import anyio
import googlemaps
import structlog

from src.core.config import settings
from src.core.exceptions import BadRequestException, GeocodingException, ServiceUnavailableException

logger = structlog.get_logger()
ALLOWED_ACCURACY_FLAGS = {"ROOFTOP", "INTERPOLATED"}


@dataclass(slots=True)
class GeocodingCandidate:
    """Normalized geocoding candidate."""

    apn: str
    formatted_address: str
    place_id: str
    accuracy_flag: str
    lat: float | None = None
    lng: float | None = None


class GeocodingService:
    """Wrapper around the official Google Maps client."""

    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self._client: googlemaps.Client | None = None

    def _get_client(self) -> googlemaps.Client:
        if not self.api_key:
            raise ServiceUnavailableException("Google Maps API key is not configured")
        if self._client is None:
            self._client = googlemaps.Client(key=self.api_key)
        return self._client

    async def geocode(self, *, address: str | None = None, apn: str | None = None) -> list[GeocodingCandidate]:
        if not address and not apn:
            raise BadRequestException("Either address or APN must be provided", field="query")

        query = address or apn
        client = self._get_client()
        logger.info("geocoding_provider_request", query=query, lookup_type="address" if address else "apn")

        try:
            results = await anyio.to_thread.run_sync(client.geocode, query)
        except googlemaps.exceptions.Timeout:
            logger.warning("geocoding_timeout", query=query)
            raise ServiceUnavailableException("Geocoding request timed out")
        except googlemaps.exceptions.ApiError as exc:
            logger.warning("geocoding_api_error", query=query, error=str(exc))
            raise GeocodingException(f"Geocoding provider error: {exc}")
        except Exception as exc:
            logger.exception("geocoding_unexpected_failure", query=query, error_type=type(exc).__name__)
            raise ServiceUnavailableException("Geocoding service temporarily unavailable")

        candidates = [self._normalize_candidate(result, fallback_apn=apn) for result in results]
        if not candidates:
            logger.info("geocoding_no_candidates", query=query)
            return []
        logger.info("geocoding_provider_success", query=query, candidate_count=len(candidates))
        return candidates

    def _normalize_candidate(self, result: dict[str, Any], *, fallback_apn: str | None) -> GeocodingCandidate:
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})
        location_type = geometry.get("location_type", "UNKNOWN")
        accuracy_flag = self._normalize_accuracy_flag(location_type)

        return GeocodingCandidate(
            apn=fallback_apn or "UNKNOWN",
            formatted_address=result.get("formatted_address", ""),
            place_id=result.get("place_id", ""),
            accuracy_flag=accuracy_flag,
            lat=location.get("lat"),
            lng=location.get("lng"),
        )

    def _normalize_accuracy_flag(self, location_type: str) -> str:
        if location_type in ALLOWED_ACCURACY_FLAGS:
            return location_type

        logger.info(
            "geocoding_accuracy_flag_downgraded",
            provider_location_type=location_type,
            normalized_accuracy_flag="INTERPOLATED",
        )
        return "INTERPOLATED"


_service: GeocodingService | None = None


def get_geocoding_service() -> GeocodingService:
    global _service
    if _service is None:
        _service = GeocodingService(settings.GOOGLE_MAPS_API_KEY)
    return _service
