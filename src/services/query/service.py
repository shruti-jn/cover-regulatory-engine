"""
Grounded follow-up query service.
"""

from __future__ import annotations

from collections import OrderedDict
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundException
from src.db.vector import search_similar_rules
from src.models.assessment import Assessment
from src.models.extracted_rule import ExtractedRule
from src.models.parcel_constraint import ParcelConstraint
from src.schemas.query import CitedSource, FollowUpQueryResponse
from src.services.embeddings import EmbeddingService, get_embedding_service

logger = structlog.get_logger()


class FollowUpQueryService:
    """Grounded follow-up query service using vector retrieval."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def answer_question(
        self,
        *,
        db: AsyncSession,
        assessment_id: UUID,
        question: str,
    ) -> FollowUpQueryResponse:
        assessment = await self._load_assessment_context(db, assessment_id)
        jurisdictions = self._extract_jurisdictions(assessment)
        jurisdiction = jurisdictions[0] if jurisdictions else None

        logger.info(
            "follow_up_query_retrieval_started",
            assessment_id=str(assessment_id),
            jurisdiction=jurisdiction,
        )
        query_embedding = await self.embedding_service.generate_embedding(question)
        search_results = await search_similar_rules(
            db,
            query_embedding=query_embedding,
            jurisdiction=jurisdiction,
            limit=3,
            min_similarity=0.6,
        )
        rules = await self._load_ranked_rules(db, [result.rule.id for result in search_results])

        answer = self._render_answer(question=question, rules=rules)
        cited_sources = self._collect_cited_sources(rules)
        logger.info(
            "follow_up_query_retrieval_completed",
            assessment_id=str(assessment_id),
            jurisdiction=jurisdiction,
            retrieved_rule_count=len(rules),
            cited_source_count=len(cited_sources),
        )
        return FollowUpQueryResponse(answer=answer, cited_sources=cited_sources)

    async def _load_assessment_context(self, db: AsyncSession, assessment_id: UUID) -> Assessment:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.constraints)
                .selectinload(ParcelConstraint.extracted_rule)
                .selectinload(ExtractedRule.document)
            )
            .where(Assessment.id == assessment_id)
        )
        result = await db.execute(stmt)
        assessment = result.scalar_one_or_none()
        if assessment is None:
            raise NotFoundException("Assessment", str(assessment_id))
        return assessment

    def _extract_jurisdictions(self, assessment: Assessment) -> list[str]:
        jurisdictions = []
        for constraint in assessment.constraints:
            rule = constraint.extracted_rule
            if rule and rule.document and rule.document.jurisdiction:
                jurisdictions.append(rule.document.jurisdiction)
        return list(OrderedDict.fromkeys(jurisdictions))

    async def _load_ranked_rules(self, db: AsyncSession, rule_ids: list[UUID]) -> list[ExtractedRule]:
        if not rule_ids:
            return []

        stmt = (
            select(ExtractedRule)
            .options(
                selectinload(ExtractedRule.document),
                selectinload(ExtractedRule.provenance_entries),
            )
            .where(ExtractedRule.id.in_(rule_ids))
        )
        result = await db.execute(stmt)
        loaded_rules = {rule.id: rule for rule in result.scalars()}
        return [loaded_rules[rule_id] for rule_id in rule_ids if rule_id in loaded_rules]

    def _render_answer(self, *, question: str, rules: list[ExtractedRule]) -> str:
        if not rules:
            return (
                f"No grounded regulatory evidence was retrieved for the question: {question}. "
                "A follow-up answer cannot be generated without cited source support."
            )

        evidence_lines = []
        for rule in rules:
            value = rule.constraint_value.get("value")
            value_type = rule.constraint_value.get("type", "constraint")
            evidence_lines.append(
                f"{rule.domain}: {value_type}={value} (rule_type={rule.rule_type}, confidence={rule.confidence_score:.2f})"
            )

        return "Grounded answer based on retrieved rules: " + " | ".join(evidence_lines)

    def _collect_cited_sources(self, rules: list[ExtractedRule]) -> list[CitedSource]:
        citations: list[CitedSource] = []
        seen: set[tuple[str | None, int | None]] = set()

        for rule in rules:
            if rule.provenance_entries:
                for provenance in rule.provenance_entries:
                    key = (rule.document.source_url if rule.document else None, provenance.page_number)
                    if key in seen:
                        continue
                    seen.add(key)
                    citations.append(
                        CitedSource(
                            source_url=rule.document.source_url if rule.document else None,
                            page_number=provenance.page_number,
                        )
                    )
            elif rule.document:
                key = (rule.document.source_url, None)
                if key in seen:
                    continue
                seen.add(key)
                citations.append(CitedSource(source_url=rule.document.source_url, page_number=None))

        return citations


_service: FollowUpQueryService | None = None


def get_follow_up_query_service() -> FollowUpQueryService:
    global _service
    if _service is None:
        _service = FollowUpQueryService(get_embedding_service())
    return _service
