"""Worker entrypoints for RAG ingestion."""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ingestion import IngestionJobSummary, IngestionService, get_ingestion_service

logger = structlog.get_logger()


class DocumentIngestionWorker:
    """Small worker wrapper around the ingestion service."""

    def __init__(self, ingestion_service: IngestionService):
        self.ingestion_service = ingestion_service

    async def run_job(
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
        logger.info(
            "rag_ingestion_job_started",
            job_id=str(job_id),
            document_url=document_url,
            jurisdiction=jurisdiction,
        )
        summary = await self.ingestion_service.process_job(
            db=db,
            job_id=job_id,
            document_url=document_url,
            jurisdiction=jurisdiction,
            source_bytes=source_bytes,
            content_type=content_type,
            title=title,
        )
        logger.info(
            "rag_ingestion_job_finished",
            job_id=str(job_id),
            status=summary.status,
            duplicate_skipped=summary.duplicate_skipped,
            documents_processed=summary.documents_processed,
        )
        return summary


_worker: DocumentIngestionWorker | None = None


def get_document_ingestion_worker() -> DocumentIngestionWorker:
    global _worker
    if _worker is None:
        _worker = DocumentIngestionWorker(get_ingestion_service())
    return _worker
