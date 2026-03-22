from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.export.routes import get_assessment_export_service
from src.db.session import get_db
from src.main import app
from src.schemas.export import ExportResponse
from src.services.export.service import AssessmentExportService


class _StubExportService:
    async def export_assessment(self, *, db, assessment_id):
        return ExportResponse(
            download_url=f"/tmp/{assessment_id}.pdf",
            format="pdf",
            included_fields=["constraints", "evidence", "geometry", "scenario_diff"],
            unresolved_items=["height: provenance_state=interpreted"],
        )


def test_export_service_collects_unresolved_items():
    service = AssessmentExportService()
    response = type(
        "AssessmentResponseStub",
        (),
        {
            "constraints": [
                type(
                    "ConstraintStub",
                    (),
                    {"domain": "height", "provenance_state": "interpreted", "evidence": []},
                )(),
                type(
                    "ConstraintStub",
                    (),
                    {"domain": "setback", "provenance_state": "deterministic", "evidence": [object()]},
                )(),
            ]
        },
    )()

    unresolved = service._collect_unresolved_items(response)

    assert "height: provenance_state=interpreted" in unresolved
    assert "height: missing evidence" in unresolved


def test_export_service_writes_pdf_to_disk():
    with TemporaryDirectory() as tmpdir:
        service = AssessmentExportService(export_root=Path(tmpdir))
        assessment_response = type(
            "AssessmentResponseStub",
            (),
            {
                "assessment_id": uuid4(),
                "parcel_geometry": type("GeometryStub", (), {"type": "Polygon"})(),
                "constraints": [],
            },
        )()
        export_path = Path(tmpdir) / "export.pdf"

        service._write_pdf(export_path, assessment_response)

        assert export_path.exists()
        assert export_path.stat().st_size > 0


def test_export_route_returns_service_payload():
    async def override_db():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_assessment_export_service] = lambda: _StubExportService()
    assessment_id = uuid4()

    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/assessments/{assessment_id}/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["format"] == "pdf"
    assert "unresolved_items" in payload
