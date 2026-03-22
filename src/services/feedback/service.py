"""
Feedback persistence service.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException
from src.models.assessment import Assessment
from src.models.feedback import Feedback, FeedbackStatus
from src.models.user import User
from src.schemas.feedback import SubmitFeedbackResponse

logger = structlog.get_logger()


class FeedbackService:
    """Authenticated feedback submission service."""

    async def submit_feedback(
        self,
        *,
        db: AsyncSession,
        assessment_id: UUID,
        user: User,
        comment: str,
        idempotency_key: str,
    ) -> SubmitFeedbackResponse:
        assessment = await db.get(Assessment, assessment_id)
        if assessment is None:
            raise NotFoundException("Assessment", str(assessment_id))

        result = await db.execute(
            select(Feedback).where(
                Feedback.assessment_id == assessment_id,
                Feedback.idempotency_key == idempotency_key,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.info(
                "submit_feedback_idempotent_replay",
                assessment_id=str(assessment_id),
                user_id=str(user.id),
                idempotency_key=idempotency_key,
            )
            return SubmitFeedbackResponse(feedback_id=existing.id)

        feedback = Feedback(
            user_id=user.id,
            assessment_id=assessment_id,
            comment=comment,
            status=FeedbackStatus.OPEN,
            idempotency_key=idempotency_key,
        )
        db.add(feedback)
        await db.flush()
        logger.info(
            "submit_feedback_persisted",
            assessment_id=str(assessment_id),
            user_id=str(user.id),
            feedback_id=str(feedback.id),
        )
        return SubmitFeedbackResponse(feedback_id=feedback.id)


_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    global _service
    if _service is None:
        _service = FeedbackService()
    return _service
