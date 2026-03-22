"""Admin API routes."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, UnauthorizedException
from src.db.session import AsyncSessionLocal, get_db
from src.models.ingestion_pipeline import IngestionPipelineStatus
from src.models.user import User, UserRole
from src.schemas.admin import (
    IngestionStatusResponse,
    PipelineStatusResponse,
    TriggerIngestionRequest,
    TriggerIngestionResponse,
)
from src.services.ingestion import IngestionJobStatus, get_ingestion_service
from src.workers.rag.pipeline import get_document_ingestion_worker

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require an authenticated admin user."""
    if not authorization:
        raise UnauthorizedException("Admin authentication required")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedException("Admin authentication required")

    result = await db.execute(select(User).where(User.email == token).limit(1))
    user = result.scalar_one_or_none()
    if user is None or user.role != UserRole.ADMIN:
        raise UnauthorizedException("Admin authentication required")
    return user


async def _run_ingestion_job(
    *,
    job_id: UUID,
    document_url: str,
    jurisdiction: str,
) -> None:
    """Execute ingestion work in a background task with a fresh session."""
    async with AsyncSessionLocal() as session:
        worker = get_document_ingestion_worker()
        try:
            await worker.run_job(
                db=session,
                job_id=job_id,
                document_url=document_url,
                jurisdiction=jurisdiction,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post("/ingest", response_model=TriggerIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_document_ingestion(
    request: TriggerIngestionRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
):
    """Queue a document ingestion job and schedule background processing."""
    if not idempotency_key.strip():
        raise BadRequestException("Idempotency key is required", field="Idempotency-Key")

    job = await ingestion_service.queue_job(
        db=db,
        document_url=request.document_url,
        jurisdiction=request.jurisdiction,
    )
    background_tasks.add_task(
        _run_ingestion_job,
        job_id=job.id,
        document_url=request.document_url,
        jurisdiction=request.jurisdiction,
    )
    logger.info(
        "trigger_ingestion",
        admin_user_id=str(user.id),
        job_id=str(job.id),
        document_url=request.document_url,
        jurisdiction=request.jurisdiction,
        idempotency_key=idempotency_key,
    )
    return TriggerIngestionResponse(job_id=job.id)


@router.get("/ingest/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    job_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
):
    """Return the persisted status for an ingestion job."""
    job = await ingestion_service.get_job_status(db=db, job_id=job_id)
    logger.info("get_ingestion_status", admin_user_id=str(user.id), job_id=str(job_id))
    return IngestionStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=_status_progress(job.status),
        documents_processed=job.documents_processed,
        error_count=job.error_count,
        started_at=job.created_at,
        completed_at=job.updated_at if job.status in {IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED} else None,
        error_message="Ingestion failed" if job.status == IngestionJobStatus.FAILED else None,
    )


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return the latest ingestion pipeline status for admin visibility."""
    stmt = select(IngestionPipelineStatus).order_by(IngestionPipelineStatus.updated_at.desc()).limit(1)
    result = await db.execute(stmt)
    latest = result.scalar_one_or_none()
    logger.info("get_pipeline_status", admin_user_id=str(user.id))

    if latest is None:
        return PipelineStatusResponse(
            status="IDLE",
            last_run_at=None,
            documents_processed=0,
            error_count=0,
        )

    return PipelineStatusResponse(
        status=latest.status,
        last_run_at=latest.last_run_at,
        documents_processed=latest.documents_processed,
        error_count=latest.error_count,
    )


def _status_progress(status_value: str) -> int:
    if status_value == IngestionJobStatus.QUEUED:
        return 0
    if status_value == IngestionJobStatus.PROCESSING:
        return 50
    return 100
