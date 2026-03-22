"""
Feedback API routes.
"""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, UnauthorizedException
from src.db.session import get_db
from src.models.user import User
from src.schemas.feedback import SubmitFeedbackRequest, SubmitFeedbackResponse
from src.services.feedback import get_feedback_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/assessments", tags=["feedback"])


async def require_authenticated_user(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization:
        raise UnauthorizedException("Authentication required")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedException("Authentication required")

    result = await db.execute(select(User).where(User.email == token).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("Authentication required")
    return user


@router.post("/{id}/feedback", response_model=SubmitFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    id: UUID,
    request: SubmitFeedbackRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_authenticated_user),
    feedback_service=Depends(get_feedback_service),
):
    if not idempotency_key.strip():
        raise BadRequestException("Idempotency key is required", field="Idempotency-Key")

    logger.info("submit_feedback_request", assessment_id=str(id), user_id=str(user.id))
    return await feedback_service.submit_feedback(
        db=db,
        assessment_id=id,
        user=user,
        comment=request.comment,
        idempotency_key=idempotency_key,
    )
