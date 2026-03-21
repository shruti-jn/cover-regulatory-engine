"""
IngestionPipelineStatus model - Aggregate pipeline health and state for admin visibility.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime

from src.db.base import Base


class PipelineStatus:
    """Pipeline status constants."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"


class IngestionPipelineStatus(Base):
    """
    Aggregate pipeline health and state for admin visibility.
    
    Tracks document ingestion progress and errors for monitoring.
    """

    __tablename__ = "ingestion_pipeline_status"

    # Current pipeline status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PipelineStatus.IDLE,
        index=True,
    )

    # Last run timestamp
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Number of documents processed in the last run
    documents_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Number of errors encountered
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    def __repr__(self) -> str:
        return f"<IngestionPipelineStatus(id={self.id}, status={self.status}, processed={self.documents_processed})>"
