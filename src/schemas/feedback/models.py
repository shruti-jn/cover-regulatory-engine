"""
Feedback-specific schemas.
"""

from uuid import UUID

from src.schemas.base import BaseSchema


class SubmitFeedbackRequest(BaseSchema):
    """Request to submit feedback on an assessment."""

    comment: str


class SubmitFeedbackResponse(BaseSchema):
    """Response for feedback submission."""

    feedback_id: UUID
