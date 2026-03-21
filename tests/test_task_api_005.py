from __future__ import annotations

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.db.session import get_db
from src.main import app
from src.schemas.query import FollowUpQueryResponse
from src.services.query import get_follow_up_query_service
from src.services.query.service import FollowUpQueryService


def _build_rule(*, source_url: str, page_number: int | None = None):
    return SimpleNamespace(
        id=uuid4(),
        domain="setback",
        rule_type="deterministic",
        confidence_score=0.92,
        constraint_value={"type": "distance", "value": 20},
        document=SimpleNamespace(source_url=source_url, jurisdiction="LA City"),
        provenance_entries=[SimpleNamespace(page_number=page_number)] if page_number is not None else [],
    )


def _build_assessment():
    rule = _build_rule(source_url="https://example.com/doc", page_number=12)
    constraint = SimpleNamespace(extracted_rule=rule)
    return SimpleNamespace(
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        constraints=[constraint],
    )


def test_follow_up_query_service_returns_grounded_answer_and_citations():
    embedding_service = SimpleNamespace(generate_embedding=AsyncMock(return_value=[0.1, 0.2, 0.3]))
    service = FollowUpQueryService(embedding_service=embedding_service)
    assessment = _build_assessment()
    retrieved_rule = _build_rule(source_url="https://example.com/doc", page_number=12)
    db = object()

    with (
        patch.object(service, "_load_assessment_context", AsyncMock(return_value=assessment)),
        patch("src.services.query.service.search_similar_rules", AsyncMock(return_value=[SimpleNamespace(rule=SimpleNamespace(id=retrieved_rule.id))])),
        patch.object(service, "_load_ranked_rules", AsyncMock(return_value=[retrieved_rule])),
    ):
        response = __import__("asyncio").run(
            service.answer_question(db=db, assessment_id=assessment.id, question="What is the setback?")
        )

    assert "Grounded answer based on retrieved rules" in response.answer
    assert response.cited_sources[0].source_url == "https://example.com/doc"
    assert response.cited_sources[0].page_number == 12


def test_follow_up_query_service_returns_no_evidence_message_when_search_is_empty():
    embedding_service = SimpleNamespace(generate_embedding=AsyncMock(return_value=[0.1, 0.2, 0.3]))
    service = FollowUpQueryService(embedding_service=embedding_service)
    assessment = _build_assessment()

    with (
        patch.object(service, "_load_assessment_context", AsyncMock(return_value=assessment)),
        patch("src.services.query.service.search_similar_rules", AsyncMock(return_value=[])),
        patch.object(service, "_load_ranked_rules", AsyncMock(return_value=[])),
    ):
        response = __import__("asyncio").run(
            service.answer_question(db=object(), assessment_id=assessment.id, question="Unknown question?")
        )

    assert "No grounded regulatory evidence was retrieved" in response.answer
    assert response.cited_sources == []


class _StubQueryService:
    async def answer_question(self, *, db, assessment_id, question: str) -> FollowUpQueryResponse:
        return FollowUpQueryResponse(
            answer=f"Grounded answer for: {question}",
            cited_sources=[{"source_url": "https://example.com/doc", "page_number": 7}],
        )


def test_follow_up_query_route_returns_service_payload():
    async def override_db():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_follow_up_query_service] = lambda: _StubQueryService()

    assessment_id = uuid4()
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/assessments/{assessment_id}/query",
                json={"question": "What is the setback?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Grounded answer for: What is the setback?"
    assert payload["cited_sources"][0]["page_number"] == 7
