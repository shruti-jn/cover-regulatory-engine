from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import patch
from uuid import uuid4
import asyncio

from fastapi.testclient import TestClient

from src.api.admin.routes import get_ingestion_service, get_pipeline_status, require_admin
from src.db.session import get_db
from src.main import app
from src.services.ingestion.service import IngestionJobStatus


class _StubIngestionService:
    def __init__(self, queued_job=None, status_job=None):
        self._queued_job = queued_job
        self._status_job = status_job

    async def queue_job(self, *, db, document_url: str, jurisdiction: str):
        return self._queued_job

    async def get_job_status(self, *, db, job_id):
        return self._status_job


def test_require_admin_rejects_missing_authorization():
    try:
        asyncio.run(require_admin(authorization=None, db=SimpleNamespace()))
    except Exception as exc:
        assert exc.__class__.__name__ == "UnauthorizedException"
        return
    raise AssertionError("Expected UnauthorizedException")


def test_trigger_ingestion_returns_accepted_job_id():
    job = SimpleNamespace(id=uuid4())

    async def override_db():
        yield None

    async def override_admin():
        return SimpleNamespace(id=uuid4(), email="admin@example.com")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_admin] = override_admin
    app.dependency_overrides[get_ingestion_service] = lambda: _StubIngestionService(queued_job=job)

    try:
        with patch("src.api.admin.routes._run_ingestion_job", new=AsyncMock()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/admin/ingest",
                    json={"document_url": "https://example.com/code.pdf", "jurisdiction": "LA City"},
                    headers={
                        "Authorization": "Bearer admin@example.com",
                        "Idempotency-Key": "ingest-1",
                    },
                )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["job_id"] == str(job.id)


def test_get_ingestion_status_returns_current_job_state():
    job = SimpleNamespace(
        id=uuid4(),
        status=IngestionJobStatus.PROCESSING,
        documents_processed=0,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async def override_db():
        yield None

    async def override_admin():
        return SimpleNamespace(id=uuid4(), email="admin@example.com")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_admin] = override_admin
    app.dependency_overrides[get_ingestion_service] = lambda: _StubIngestionService(status_job=job)

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/admin/ingest/{job.id}",
                headers={"Authorization": "Bearer admin@example.com"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == IngestionJobStatus.PROCESSING
    assert payload["progress"] == 50


def test_pipeline_status_returns_idle_when_no_jobs_exist():
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
    )
    admin = SimpleNamespace(id=uuid4(), email="admin@example.com")

    response = asyncio.run(get_pipeline_status(user=admin, db=db))

    assert response.status == "IDLE"
    assert response.documents_processed == 0
