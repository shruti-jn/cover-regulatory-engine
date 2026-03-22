"""
Assessment and scenario diff services.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

import structlog
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundException
from src.models.assessment import Assessment, AssessmentStatus
from src.models.extracted_rule import ExtractedRule
from src.models.parcel import Parcel
from src.models.parcel_constraint import ParcelConstraint
from src.schemas.assessment import (
    AssessmentResponse,
    ConstraintEvidence,
    ConstraintResponse,
    ConstraintValue,
    DiffScenarioResponse,
    ScenarioDiff,
    ScenarioDiffConstraint,
    ScenarioInputs,
)
from src.schemas.parcel import GeoJSONGeometry

logger = structlog.get_logger()


class AssessmentService:
    """Deterministic parcel assessment service."""

    async def assess_parcel_buildability(
        self,
        *,
        db: AsyncSession,
        apn: str,
        scenario_inputs: ScenarioInputs,
    ) -> AssessmentResponse:
        parcel = await self._load_parcel(db, apn)
        scenario_hash = self._hash_scenario_inputs(scenario_inputs)
        existing = await self._load_existing_assessment(db, parcel.id, scenario_hash)
        if existing is not None:
            logger.info("assessment_reused", apn=apn, assessment_id=str(existing.id))
            return await self._serialize_assessment(db, existing)

        rules = await self._load_rules(db)
        assessment = Assessment(
            parcel_id=parcel.id,
            scenario_hash=scenario_hash,
            status=AssessmentStatus.COMPLETED,
        )
        db.add(assessment)
        await db.flush()

        for rule in rules:
            derived_geometry = await self._derive_geometry_if_supported(db, parcel, rule)
            constraint = ParcelConstraint(
                scenario_hash=scenario_hash,
                is_active=True,
                provenance_state="deterministic",
                evidence=self._build_evidence(rule),
                derived_geometry=derived_geometry,
                assessment_id=assessment.id,
                extracted_rule_id=rule.id,
            )
            db.add(constraint)

        await db.flush()
        reloaded = await self._load_assessment_with_relationships(db, assessment.id)
        logger.info("assessment_created", apn=apn, assessment_id=str(assessment.id), rule_count=len(rules))
        return await self._serialize_assessment(db, reloaded)

    async def diff_scenarios(
        self,
        *,
        db: AsyncSession,
        base_scenario_id: UUID,
        new_scenario_id: UUID,
    ) -> DiffScenarioResponse:
        base_assessment = await self._load_assessment_with_relationships(db, base_scenario_id)
        new_assessment = await self._load_assessment_with_relationships(db, new_scenario_id)
        base_by_domain = {c.extracted_rule.domain: c for c in base_assessment.constraints}
        new_by_domain = {c.extracted_rule.domain: c for c in new_assessment.constraints}

        changed_constraints: list[ScenarioDiffConstraint] = []
        for domain in sorted(set(base_by_domain) | set(new_by_domain)):
            base_constraint = base_by_domain.get(domain)
            new_constraint = new_by_domain.get(domain)
            before_value = self._constraint_value(base_constraint)
            after_value = self._constraint_value(new_constraint)
            if before_value == after_value:
                continue
            changed_constraints.append(
                ScenarioDiffConstraint(
                    domain=domain,
                    before_value=before_value,
                    after_value=after_value,
                    confidence_delta=self._confidence_delta(base_constraint, new_constraint),
                    geometry_changed=self._geometry_changed(base_constraint, new_constraint),
                )
            )

        return DiffScenarioResponse(diff=ScenarioDiff(changed_constraints=changed_constraints))

    async def _load_parcel(self, db: AsyncSession, apn: str) -> Parcel:
        result = await db.execute(select(Parcel).where(Parcel.apn == apn).limit(1))
        parcel = result.scalar_one_or_none()
        if parcel is None:
            raise NotFoundException("Parcel", apn)
        return parcel

    async def _load_existing_assessment(
        self,
        db: AsyncSession,
        parcel_id: UUID,
        scenario_hash: str,
    ) -> Assessment | None:
        result = await db.execute(
            select(Assessment)
            .where(Assessment.parcel_id == parcel_id, Assessment.scenario_hash == scenario_hash)
            .limit(1)
        )
        assessment = result.scalar_one_or_none()
        if assessment is None:
            return None
        return await self._load_assessment_with_relationships(db, assessment.id)

    async def _load_rules(self, db: AsyncSession) -> list[ExtractedRule]:
        result = await db.execute(
            select(ExtractedRule)
            .options(
                selectinload(ExtractedRule.document),
                selectinload(ExtractedRule.provenance_entries),
            )
            .order_by(ExtractedRule.confidence_score.desc())
            .limit(5)
        )
        return list(result.scalars())

    async def _load_assessment_with_relationships(self, db: AsyncSession, assessment_id: UUID) -> Assessment:
        result = await db.execute(
            select(Assessment)
            .options(
                selectinload(Assessment.parcel),
                selectinload(Assessment.constraints)
                .selectinload(ParcelConstraint.extracted_rule)
                .selectinload(ExtractedRule.document),
                selectinload(Assessment.constraints)
                .selectinload(ParcelConstraint.extracted_rule)
                .selectinload(ExtractedRule.provenance_entries),
            )
            .where(Assessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()
        if assessment is None:
            raise NotFoundException("Assessment", str(assessment_id))
        return assessment

    async def _derive_geometry_if_supported(
        self,
        db: AsyncSession,
        parcel: Parcel,
        rule: ExtractedRule,
    ):
        if rule.domain != "setback":
            return None
        value = rule.constraint_value.get("value")
        if not isinstance(value, (int, float)):
            return None

        result = await db.execute(
            select(func.ST_Buffer(Parcel.geometry, -float(value))).where(Parcel.id == parcel.id)
        )
        return result.scalar_one_or_none()

    def _build_evidence(self, rule: ExtractedRule) -> list[dict]:
        evidence = []
        for provenance in rule.provenance_entries:
            evidence.append(
                {
                    "source_title": rule.document.title if rule.document else "Unknown source",
                    "source_url": rule.document.source_url if rule.document else None,
                    "jurisdiction": rule.document.jurisdiction if rule.document else "Unknown",
                    "page_number": provenance.page_number,
                    "excerpt": provenance.excerpt,
                }
            )
        if evidence:
            return evidence
        if rule.document:
            return [
                {
                    "source_title": rule.document.title,
                    "source_url": rule.document.source_url,
                    "jurisdiction": rule.document.jurisdiction,
                    "page_number": None,
                    "excerpt": None,
                }
            ]
        return []

    async def _serialize_assessment(self, db: AsyncSession, assessment: Assessment) -> AssessmentResponse:
        parcel_geometry = GeoJSONGeometry.model_validate(mapping(to_shape(assessment.parcel.geometry)))
        constraints: list[ConstraintResponse] = []
        for constraint in assessment.constraints:
            derived_geometry = None
            if constraint.derived_geometry is not None:
                geojson = await self._geometry_to_geojson(db, constraint.derived_geometry)
                if geojson is not None:
                    derived_geometry = GeoJSONGeometry.model_validate(geojson)

            rule = constraint.extracted_rule
            constraints.append(
                ConstraintResponse(
                    domain=rule.domain,
                    provenance_state=constraint.provenance_state,
                    confidence_score=rule.confidence_score / 100 if rule.confidence_score > 1 else rule.confidence_score,
                    constraint_value=ConstraintValue(
                        type=rule.constraint_value.get("type", "constraint"),
                        value=rule.constraint_value.get("value"),
                    ),
                    derived_geometry=derived_geometry,
                    evidence=[ConstraintEvidence.model_validate(item) for item in (constraint.evidence or [])],
                )
            )

        return AssessmentResponse(
            assessment_id=assessment.id,
            parcel_geometry=parcel_geometry,
            constraints=constraints,
            scenario_diff=None,
        )

    async def _geometry_to_geojson(self, db: AsyncSession, geometry) -> dict | None:
        result = await db.execute(select(func.ST_AsGeoJSON(geometry)))
        geojson = result.scalar_one_or_none()
        return json.loads(geojson) if geojson else None

    def _hash_scenario_inputs(self, scenario_inputs: ScenarioInputs) -> str:
        payload = json.dumps(scenario_inputs.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _constraint_value(self, constraint: ParcelConstraint | None):
        if constraint is None:
            return None
        return constraint.extracted_rule.constraint_value.get("value")

    def _confidence_delta(
        self,
        base_constraint: ParcelConstraint | None,
        new_constraint: ParcelConstraint | None,
    ) -> float:
        base_score = base_constraint.extracted_rule.confidence_score if base_constraint else 0.0
        new_score = new_constraint.extracted_rule.confidence_score if new_constraint else 0.0
        return (new_score - base_score) / 100 if max(base_score, new_score) > 1 else new_score - base_score

    def _geometry_changed(
        self,
        base_constraint: ParcelConstraint | None,
        new_constraint: ParcelConstraint | None,
    ) -> bool:
        return bool(base_constraint and base_constraint.derived_geometry) != bool(
            new_constraint and new_constraint.derived_geometry
        )


_service: AssessmentService | None = None


def get_assessment_service() -> AssessmentService:
    global _service
    if _service is None:
        _service = AssessmentService()
    return _service
