"""Document ingestion service for the async RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import md5
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID
import re

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, ServiceUnavailableException
from src.models.extracted_rule import ExtractedRule, RuleDomain, RuleType
from src.models.ingested_document import IngestedDocument
from src.models.ingestion_pipeline import IngestionPipelineStatus
from src.models.rule_provenance import RuleProvenance
from src.services.embeddings import EmbeddingService, get_embedding_service

logger = structlog.get_logger()


class IngestionJobStatus:
    """Pipeline job statuses exposed to admin and worker flows."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(slots=True)
class ParsedDocument:
    """Parsed document payload."""

    title: str
    raw_text: str
    chunks: list[str]
    pages: list[int | None]
    metadata: dict[str, Any]


@dataclass(slots=True)
class IngestionJobSummary:
    """Result summary for a completed ingestion job."""

    job_id: UUID
    status: str
    document_id: UUID | None
    duplicate_skipped: bool
    documents_processed: int
    error_count: int


class IngestionService:
    """Coordinates document fetching, parsing, chunking, and persistence."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def queue_job(
        self,
        *,
        db: AsyncSession,
        document_url: str,
        jurisdiction: str,
    ) -> IngestionPipelineStatus:
        """Create a queued ingestion job."""
        job = IngestionPipelineStatus(
            status=IngestionJobStatus.QUEUED,
            last_run_at=datetime.now(UTC),
            documents_processed=0,
            error_count=0,
        )
        db.add(job)
        await db.flush()
        logger.info(
            "ingestion_job_queued",
            job_id=str(job.id),
            document_url=document_url,
            jurisdiction=jurisdiction,
        )
        return job

    async def process_job(
        self,
        *,
        db: AsyncSession,
        job_id: UUID,
        document_url: str,
        jurisdiction: str,
        source_bytes: bytes | None = None,
        content_type: str | None = None,
        title: str | None = None,
    ) -> IngestionJobSummary:
        """Execute a queued ingestion job end-to-end."""
        job = await self._load_job(db, job_id)
        job.status = IngestionJobStatus.PROCESSING
        job.last_run_at = datetime.now(UTC)
        await db.flush()

        try:
            if source_bytes is None:
                source_bytes, content_type = await self._fetch_source(document_url)

            checksum = md5(source_bytes).hexdigest()
            existing_document = await self._find_existing_document(
                db=db,
                checksum=checksum,
                jurisdiction=jurisdiction,
                source_url=document_url,
            )
            if existing_document is not None:
                job.status = IngestionJobStatus.COMPLETED
                job.documents_processed = 0
                logger.info(
                    "ingestion_duplicate_skipped",
                    job_id=str(job_id),
                    document_id=str(existing_document.id),
                    checksum=checksum,
                    source_url=document_url,
                )
                return IngestionJobSummary(
                    job_id=job.id,
                    status=job.status,
                    document_id=existing_document.id,
                    duplicate_skipped=True,
                    documents_processed=job.documents_processed,
                    error_count=job.error_count,
                )

            parsed = self._parse_document(
                source_bytes=source_bytes,
                document_url=document_url,
                content_type=content_type,
                title=title,
            )
            document = await self._persist_document(
                db=db,
                checksum=checksum,
                jurisdiction=jurisdiction,
                document_url=document_url,
                parsed=parsed,
            )

            job.status = IngestionJobStatus.COMPLETED
            job.documents_processed = 1
            job.last_run_at = datetime.now(UTC)
            await db.flush()
            logger.info(
                "ingestion_job_completed",
                job_id=str(job_id),
                document_id=str(document.id),
                chunk_count=len(parsed.chunks),
            )
            return IngestionJobSummary(
                job_id=job.id,
                status=job.status,
                document_id=document.id,
                duplicate_skipped=False,
                documents_processed=job.documents_processed,
                error_count=job.error_count,
            )
        except Exception as exc:
            job.status = IngestionJobStatus.FAILED
            job.error_count += 1
            job.last_run_at = datetime.now(UTC)
            await db.flush()
            logger.error(
                "rag_ingestion_failed",
                job_id=str(job_id),
                document_url=document_url,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    async def get_job_status(self, *, db: AsyncSession, job_id: UUID) -> IngestionPipelineStatus:
        """Return the persisted ingestion job status."""
        return await self._load_job(db, job_id)

    async def _load_job(self, db: AsyncSession, job_id: UUID) -> IngestionPipelineStatus:
        job = await db.get(IngestionPipelineStatus, job_id)
        if job is None:
            raise NotFoundException("Ingestion job", str(job_id))
        return job

    async def _find_existing_document(
        self,
        *,
        db: AsyncSession,
        checksum: str,
        jurisdiction: str,
        source_url: str,
    ) -> IngestedDocument | None:
        stmt = (
            select(IngestedDocument)
            .where(IngestedDocument.version_hash == checksum)
            .where(IngestedDocument.jurisdiction == jurisdiction)
            .where(IngestedDocument.source_url == source_url)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _fetch_source(self, document_url: str) -> tuple[bytes, str | None]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(document_url)
                response.raise_for_status()
                return response.content, response.headers.get("content-type")
        except httpx.HTTPError as exc:
            raise ServiceUnavailableException(
                f"Unable to fetch ingestion source: {document_url}"
            ) from exc

    def _parse_document(
        self,
        *,
        source_bytes: bytes,
        document_url: str,
        content_type: str | None,
        title: str | None,
    ) -> ParsedDocument:
        page_text = self._extract_page_text(source_bytes=source_bytes, content_type=content_type)
        raw_text = "\n\n".join(text for text, _ in page_text).strip()
        if not raw_text:
            raise ValueError("No readable text could be extracted from document")

        title_value = title or Path(urlparse(document_url).path).name or "ingested-document"
        chunks: list[str] = []
        pages: list[int | None] = []
        for text, page_number in page_text:
            for chunk in self.embedding_service.chunk_text(text):
                normalized = chunk.strip()
                if normalized:
                    chunks.append(normalized)
                    pages.append(page_number)

        return ParsedDocument(
            title=title_value,
            raw_text=raw_text,
            chunks=chunks,
            pages=pages,
            metadata={
                "content_type": content_type,
                "page_count": len(page_text),
                "chunk_count": len(chunks),
                "source_kind": "pdf" if self._looks_like_pdf(source_bytes, content_type) else "text",
            },
        )

    def _extract_page_text(
        self,
        *,
        source_bytes: bytes,
        content_type: str | None,
    ) -> list[tuple[str, int | None]]:
        if self._looks_like_pdf(source_bytes, content_type):
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(source_bytes))
                pages: list[tuple[str, int | None]] = []
                for index, page in enumerate(reader.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    if text:
                        pages.append((text, index))
                if pages:
                    return pages
            except Exception as exc:
                logger.warning("pdf_text_extraction_fallback", error=str(exc))

        decoded = source_bytes.decode("utf-8", errors="ignore").strip()
        return [(decoded, None)]

    def _looks_like_pdf(self, source_bytes: bytes, content_type: str | None) -> bool:
        return (content_type or "").lower().startswith("application/pdf") or source_bytes.startswith(b"%PDF")

    async def _persist_document(
        self,
        *,
        db: AsyncSession,
        checksum: str,
        jurisdiction: str,
        document_url: str,
        parsed: ParsedDocument,
    ) -> IngestedDocument:
        document = IngestedDocument(
            title=parsed.title,
            jurisdiction=jurisdiction,
            source_url=document_url,
            version_hash=checksum,
            raw_text=parsed.raw_text,
            document_metadata=parsed.metadata,
        )
        db.add(document)
        await db.flush()

        embeddings = await self.embedding_service.generate_embeddings_batch(parsed.chunks)
        for chunk, page_number, embedding in zip(parsed.chunks, parsed.pages, embeddings):
            rule = ExtractedRule(
                domain=self._infer_domain(chunk),
                rule_type=self._infer_rule_type(chunk),
                constraint_value=self._extract_constraint_value(chunk),
                confidence_score=self._infer_confidence(chunk),
                embedding=embedding,
                document=document,
            )
            provenance = RuleProvenance(
                excerpt=chunk[:5000],
                page_number=page_number,
                rule=rule,
                document=document,
            )
            db.add(rule)
            db.add(provenance)

        await db.flush()
        return document

    def _infer_domain(self, chunk: str) -> str:
        lower = chunk.lower()
        if "parking" in lower:
            return RuleDomain.PARKING
        if "height" in lower:
            return RuleDomain.HEIGHT
        if "overlay" in lower or "hpoz" in lower or "coastal" in lower:
            return RuleDomain.OVERLAY
        if "adu" in lower:
            return RuleDomain.ADU
        if "setback" in lower or "yard" in lower:
            return RuleDomain.SETBACK
        return RuleDomain.ZONING

    def _infer_rule_type(self, chunk: str) -> str:
        lower = chunk.lower()
        if "shall" in lower or re.search(r"\\b\\d+\\s*(ft|feet|foot|stories?)\\b", lower):
            return RuleType.DETERMINISTIC
        if "may" in lower or "typically" in lower:
            return RuleType.INTERPRETED
        return RuleType.UNRESOLVED

    def _extract_constraint_value(self, chunk: str) -> dict[str, Any]:
        numeric_match = re.search(r"(?P<value>\\d+(?:\\.\\d+)?)\\s*(?P<unit>ft|feet|foot|stories?)", chunk, re.IGNORECASE)
        if numeric_match:
            value = float(numeric_match.group("value"))
            if value.is_integer():
                value = int(value)
            return {
                "type": self._infer_domain(chunk),
                "value": value,
                "unit": numeric_match.group("unit").lower(),
                "excerpt": chunk[:240],
            }

        return {
            "type": self._infer_domain(chunk),
            "value": chunk[:240],
            "unit": None,
            "excerpt": chunk[:240],
        }

    def _infer_confidence(self, chunk: str) -> float:
        rule_type = self._infer_rule_type(chunk)
        if rule_type == RuleType.DETERMINISTIC:
            return 90.0
        if rule_type == RuleType.INTERPRETED:
            return 70.0
        return 45.0


_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    global _service
    if _service is None:
        _service = IngestionService(get_embedding_service())
    return _service
