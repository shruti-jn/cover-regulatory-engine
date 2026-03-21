"""
Feedback model - Expert feedback captured against a specific assessment.
"""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.assessment import Assessment
    from src.models.user import User


class FeedbackStatus(str, ENUM):
    """Feedback status enum."""
    OPEN = "open"
    RESOLVED = "resolved"


class Feedback(Base):
    """
    Expert feedback captured against a specific assessment.
    
    Allows architects and engineers to provide corrections or annotations
    to automated assessments.
    """

    __tablename__ = "feedback"

    # User who provided the feedback
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Assessment being commented on
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Feedback comment text
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    # Feedback status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FeedbackStatus.OPEN,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="feedback")
    assessment: Mapped["Assessment"] = relationship(back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, assessment_id={self.assessment_id}, status={self.status})>"
