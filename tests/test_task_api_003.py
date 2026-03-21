from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

from src.core.exceptions import ConflictException, NotFoundException
from src.db.session import get_db
from src.main import app
from src.models.parcel import Parcel
from src.schemas.parcel import GeoJSONGeometry, ParcelResponse
from src.services.parcels import get_parcel_service
from src.services.parcels.service import ParcelService


class _FakeScalars:
    def __init__(self, values: list[Parcel]):
        self._values = values

    def __iter__(self):
        return iter(self._values)


class _FakeResult:
    def __init__(self, values: list[Parcel]):
        self._values = values

    def scalars(self):
        return _FakeScalars(self._values)


class _StubParcelService:
    async def get_parcel_facts(self, db, apn: str) -> ParcelResponse:
        return ParcelResponse(
            id=uuid4(),
            apn=apn,
            address="123 Main St, Los Angeles, CA 90012",
            geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[[[-118.25, 34.05], [-118.24, 34.05], [-118.24, 34.06], [-118.25, 34.06], [-118.25, 34.05]]],
            ),
            geocoding_metadata={
                "place_id": "test-place-id",
                "accuracy_flag": "ROOFTOP",
                "lat": 34.05,
                "lng": -118.25,
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def _build_parcel(apn: str = "123-456-789") -> Parcel:
    parcel = Parcel(
        apn=apn,
        address="123 Main St, Los Angeles, CA 90012",
        geometry=from_shape(
            Polygon(
                [
                    (-118.25, 34.05),
                    (-118.24, 34.05),
                    (-118.24, 34.06),
                    (-118.25, 34.06),
                    (-118.25, 34.05),
                ]
            ),
            srid=4326,
        ),
        geocoding_metadata={
            "place_id": "test-place-id",
            "accuracy_flag": "ROOFTOP",
            "lat": 34.05,
            "lng": -118.25,
        },
    )
    parcel.id = uuid4()
    parcel.created_at = datetime.now(UTC)
    parcel.updated_at = datetime.now(UTC)
    return parcel


def test_parcel_service_returns_geojson_response():
    service = ParcelService()
    db = type("FakeDB", (), {"execute": None})()
    db.execute = AsyncMock(return_value=_FakeResult([_build_parcel()]))

    response = asyncio.run(service.get_parcel_facts(db=db, apn="123-456-789"))

    assert response.apn == "123-456-789"
    assert response.geometry.type == "Polygon"
    assert response.geometry.coordinates[0][0] == [-118.25, 34.05]
    assert response.geocoding_metadata.place_id == "test-place-id"


def test_parcel_service_raises_not_found_for_missing_apn():
    service = ParcelService()
    db = type("FakeDB", (), {"execute": None})()
    db.execute = AsyncMock(return_value=_FakeResult([]))

    with pytest.raises(NotFoundException):
        asyncio.run(service.get_parcel_facts(db=db, apn="missing-apn"))


def test_parcel_service_raises_conflict_for_duplicate_apn():
    service = ParcelService()
    duplicate_parcels = [_build_parcel("dup-apn"), _build_parcel("dup-apn")]
    db = type("FakeDB", (), {"execute": None})()
    db.execute = AsyncMock(return_value=_FakeResult(duplicate_parcels))

    with pytest.raises(ConflictException):
        asyncio.run(service.get_parcel_facts(db=db, apn="dup-apn"))


def test_get_parcel_facts_route_returns_service_payload():
    async def override_db():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_parcel_service] = lambda: _StubParcelService()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/parcels/123-456-789")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["apn"] == "123-456-789"
    assert payload["geometry"]["type"] == "Polygon"
    assert payload["geocoding_metadata"]["accuracy_flag"] == "ROOFTOP"
