"""
Admin and ingestion Pydantic v2 schemas.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import Field

from src.schemas.base import BaseSchema, UUIDSchema, TimestampedSchema


class IngestionStatus:
    """Ingestion job status constants."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TriggerIngestionRequest(BaseSchema):
    """Request to trigger document ingestion."""

    document_url: str = Field(..., description="URL of the document to ingest")
    jurisdiction: str = Field(..., description="Jurisdiction of the document")


class TriggerIngestionResponse(BaseSchema):
    """Response for triggering ingestion."""

    job_id: UUID


class IngestionStatusResponse(BaseSchema):
    """Response for ingestion status."""

    job_id: UUID
    status: str = Field(..., description="QUEUED, PROCESSING, COMPLETED, or FAILED")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    documents_processed: Optional[int] = None
    error_count: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PipelineStatusResponse(BaseSchema):
    """Pipeline status for admin visibility."""

    status: str = Field(..., description="IDLE, RUNNING, or ERROR")
    last_run_at: Optional[datetime]
    documents_processed: int
    error_count: int
