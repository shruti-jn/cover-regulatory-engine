from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from src.db.session import get_db
from src.main import app
from src.schemas.assessment import (
    AssessmentResponse,
    ConstraintEvidence,
    ConstraintResponse,
    ConstraintValue,
    DiffScenarioResponse,
    ScenarioDiff,
    ScenarioDiffConstraint,
)
from src.schemas.parcel import GeoJSONGeometry
from src.services.assessments import get_assessment_service
from src.services.assessments.service import AssessmentService


class _StubAssessmentService:
    async def assess_parcel_buildability(self, *, db, apn: str, scenario_inputs):
        return AssessmentResponse(
            assessment_id=uuid4(),
            parcel_geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[[[-118.25, 34.05], [-118.24, 34.05], [-118.24, 34.06], [-118.25, 34.06], [-118.25, 34.05]]],
            ),
            constraints=[
                ConstraintResponse(
                    domain="setback",
                    provenance_state="deterministic",
                    confidence_score=0.92,
                    constraint_value=ConstraintValue(type="distance", value=20),
                    evidence=[
                        ConstraintEvidence(
                            source_title="LAMC Chapter 12.07",
                            source_url="https://example.com/doc",
                            jurisdiction="LA City",
                            page_number=12,
                            excerpt="Front setback shall be 20 feet.",
                        )
                    ],
                )
            ],
            scenario_diff=None,
        )

    async def diff_scenarios(self, *, db, base_scenario_id, new_scenario_id):
        return DiffScenarioResponse(
            diff=ScenarioDiff(
                changed_constraints=[
                    ScenarioDiffConstraint(
                        domain="setback",
                        before_value=20,
                        after_value=16,
                        confidence_delta=0.04,
                        geometry_changed=True,
                    )
                ]
            )
        )


def test_assessment_service_diff_scenarios_detects_constraint_changes():
    service = AssessmentService()
    base_rule = SimpleNamespace(domain="setback", confidence_score=0.9, constraint_value={"value": 20})
    new_rule = SimpleNamespace(domain="setback", confidence_score=0.95, constraint_value={"value": 16})
    base_constraint = SimpleNamespace(extracted_rule=base_rule, derived_geometry="base-geom")
    new_constraint = SimpleNamespace(extracted_rule=new_rule, derived_geometry=None)
    base_assessment = SimpleNamespace(constraints=[base_constraint])
    new_assessment = SimpleNamespace(constraints=[new_constraint])

    async def load_assessment(db, assessment_id):
        return base_assessment if assessment_id == "base" else new_assessment

    service._load_assessment_with_relationships = load_assessment  # type: ignore[method-assign]

    response = asyncio.run(
        service.diff_scenarios(db=object(), base_scenario_id="base", new_scenario_id="new")
    )

    assert response.diff.changed_constraints[0].domain == "setback"
    assert response.diff.changed_constraints[0].before_value == 20
    assert response.diff.changed_constraints[0].after_value == 16
    assert response.diff.changed_constraints[0].geometry_changed is True


def test_assess_parcel_route_returns_service_payload():
    async def override_db():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_assessment_service] = lambda: _StubAssessmentService()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/parcels/123-456-789/assess",
                json={"scenario_inputs": {"building_type": "ADU", "bedrooms": 2}},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["constraints"][0]["domain"] == "setback"
    assert payload["constraints"][0]["evidence"][0]["page_number"] == 12


def test_internal_scenario_diff_route_returns_service_payload():
    async def override_db():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_assessment_service] = lambda: _StubAssessmentService()
    base_id = str(uuid4())
    new_id = str(uuid4())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/internal/v1/scenario/diff",
                json={"base_scenario_id": base_id, "new_scenario_id": new_id},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["diff"]["changed_constraints"][0]["domain"] == "setback"
