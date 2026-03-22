"""
Assessment export API routes.
"""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.export import ExportResponse
from src.services.export import get_assessment_export_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/assessments", tags=["export"])


@router.post("/{id}/export", response_model=ExportResponse)
async def export_assessment(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    export_service=Depends(get_assessment_export_service),
):
    logger.info("export_assessment_request", assessment_id=str(id))
    response = await export_service.export_assessment(db=db, assessment_id=id)
    logger.info("export_assessment_response", assessment_id=str(id), download_url=response.download_url)
    return response
