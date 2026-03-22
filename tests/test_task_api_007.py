from __future__ import annotations

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.feedback.routes import get_feedback_service, require_authenticated_user
from src.core.exceptions import NotFoundException, UnauthorizedException
from src.db.session import get_db
from src.main import app
from src.schemas.feedback import SubmitFeedbackResponse
from src.services.feedback.service import FeedbackService


class _StubFeedbackService:
    async def submit_feedback(self, *, db, assessment_id, user, comment: str, idempotency_key: str):
        return SubmitFeedbackResponse(feedback_id=uuid4())


def test_feedback_service_returns_existing_feedback_on_idempotent_replay():
    service = FeedbackService()
    feedback_id = uuid4()
    user = SimpleNamespace(id=uuid4())
    assessment_id = uuid4()
    db = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(id=assessment_id)),
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: SimpleNamespace(id=feedback_id))),
    )

    response = __import__("asyncio").run(
        service.submit_feedback(
            db=db,
            assessment_id=assessment_id,
            user=user,
            comment="Needs correction",
            idempotency_key="idem-1",
        )
    )

    assert response.feedback_id == feedback_id


def test_feedback_service_raises_not_found_for_missing_assessment():
    service = FeedbackService()
    user = SimpleNamespace(id=uuid4())
    db = SimpleNamespace(get=AsyncMock(return_value=None), execute=AsyncMock())

    try:
        __import__("asyncio").run(
            service.submit_feedback(
                db=db,
                assessment_id=uuid4(),
                user=user,
                comment="Needs correction",
                idempotency_key="idem-1",
            )
        )
    except NotFoundException:
        pass
    else:
        raise AssertionError("Expected NotFoundException")


def test_require_authenticated_user_rejects_missing_authorization():
    try:
        __import__("asyncio").run(require_authenticated_user(authorization=None, db=SimpleNamespace()))
    except UnauthorizedException:
        return
    raise AssertionError("Expected UnauthorizedException")


def test_feedback_route_returns_created_response():
    async def override_db():
        yield None

    async def override_user():
        return SimpleNamespace(id=uuid4(), email="user@example.com")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_authenticated_user] = override_user
    app.dependency_overrides[get_feedback_service] = lambda: _StubFeedbackService()

    assessment_id = uuid4()
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/assessments/{assessment_id}/feedback",
                json={"comment": "Needs correction"},
                headers={
                    "Authorization": "Bearer user@example.com",
                    "Idempotency-Key": "idem-1",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert "feedback_id" in response.json()
