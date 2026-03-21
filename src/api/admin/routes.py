"""
Admin API routes.

Implements:
- POST /api/v1/admin/ingest - Trigger document ingestion
- GET /api/v1/admin/ingest/{job_id} - Get ingestion status
- GET /api/v1/admin/pipeline/status - Get pipeline status
"""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.schemas.admin import (
    TriggerIngestionRequest,
    TriggerIngestionResponse,
    IngestionStatusResponse,
    IngestionStatus,
    PipelineStatusResponse,
)
from src.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    create_error_response,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(
    authorization: str = Header(None, alias="Authorization"),
):
    """Dependency to require admin authentication."""
    if not authorization:
        raise UnauthorizedException("Admin authentication required")
    # Placeholder: Validate admin token
    return True


@router.post("/ingest", response_model=TriggerIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_document_ingestion(
    request: TriggerIngestionRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger document ingestion for RAG pipeline.

    Starts async processing of a municipal document. Returns job ID for status tracking.
    Requires admin authentication and idempotency key.
    """
    logger.info(
        "trigger_ingestion",
        document_url=request.document_url,
        jurisdiction=request.jurisdiction,
        idempotency_key=idempotency_key,
    )

    # Placeholder: Create ingestion job
    job_id = UUID("12345678-1234-1234-1234-123456789abc")

    return TriggerIngestionResponse(job_id=job_id)


@router.get("/ingest/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    job_id: UUID,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the status of a document ingestion job.

    Returns status: QUEUED | PROCESSING | COMPLETED | FAILED
    """
    logger.info(
        "get_ingestion_status",
        job_id=job_id,
    )

    # Placeholder: Query job status
    return IngestionStatusResponse(
        job_id=job_id,
        status=IngestionStatus.QUEUED,
        progress=0,
        documents_processed=0,
        error_count=0,
        started_at=None,
        completed_at=None,
        error_message=None,
    )


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the overall ingestion pipeline status.

    For admin visibility into pipeline health.
    """
    logger.info("get_pipeline_status")

    # Placeholder: Query pipeline status
    return PipelineStatusResponse(
        status="IDLE",
        last_run_at=datetime.utcnow(),
        documents_processed=150,
        error_count=2,
    )
