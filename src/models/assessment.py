"""
Assessment model - Persistent output of a buildability evaluation.
"""

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.parcel import Parcel
    from src.models.parcel_constraint import ParcelConstraint
    from src.models.feedback import Feedback


class AssessmentStatus(str, ENUM):
    """Assessment status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Assessment(Base):
    """
    The persistent output of a buildability evaluation for a specific parcel and scenario.
    
    The scenario_hash allows diffing between different assessment configurations.
    """

    __tablename__ = "assessments"

    # Hash of the project inputs (e.g., ADU=true, beds=2) to allow diffing
    scenario_hash: Mapped[str] = mapped_column(nullable=False, index=True)

    # Assessment status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AssessmentStatus.PENDING,
    )

    # Foreign key to Parcel
    parcel_id: Mapped[UUID] = mapped_column(
        ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    parcel: Mapped["Parcel"] = relationship(back_populates="assessments")

    constraints: Mapped[List["ParcelConstraint"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    feedback: Mapped[List["Feedback"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Assessment(id={self.id}, parcel_id={self.parcel_id}, status={self.status})>"
