"""
Grounded follow-up query API routes.
"""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.query import FollowUpQueryRequest, FollowUpQueryResponse
from src.services.query import get_follow_up_query_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/assessments", tags=["query"])


@router.post("/{id}/query", response_model=FollowUpQueryResponse)
async def follow_up_query(
    id: UUID,
    request: FollowUpQueryRequest,
    db: AsyncSession = Depends(get_db),
    query_service=Depends(get_follow_up_query_service),
):
    logger.info("follow_up_query_request", assessment_id=str(id), question=request.question)
    response = await query_service.answer_question(db=db, assessment_id=id, question=request.question)
    logger.info(
        "follow_up_query_response",
        assessment_id=str(id),
        cited_source_count=len(response.cited_sources),
    )
    return response
