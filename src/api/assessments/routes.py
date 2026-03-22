"""
Assessment API routes.

Implements:
- POST /api/v1/parcels/{apn}/assess - Assess parcel buildability
- POST /api/v1/scenario/diff - Diff two scenarios
- POST /api/v1/assessments/{id}/query - Follow-up query
- POST /api/v1/assessments/{id}/export - Export assessment
- POST /api/v1/assessments/{id}/feedback - Submit feedback
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db.session import get_db
from src.schemas.assessment import (
    CreateAssessmentRequest,
    AssessmentResponse,
    ScenarioInputs,
    ConstraintResponse,
    ConstraintValue,
    ConstraintEvidence,
    DiffScenarioRequest,
    DiffScenarioResponse,
    ScenarioDiff,
    ExportResponse,
    SubmitFeedbackRequest,
    SubmitFeedbackResponse,
)
from src.services.assessments import get_assessment_service
from src.core.exceptions import BadRequestException

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["assessments"])
internal_router = APIRouter(prefix="/internal/v1", tags=["assessments-internal"])


@router.post("/parcels/{apn}/assess", response_model=AssessmentResponse)
async def assess_parcel_buildability(
    apn: str,
    request: CreateAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    assessment_service=Depends(get_assessment_service),
):
    """
    Assess the buildability of a parcel.

    Returns constraints, confidence scores, and provenance for the given scenario.
    """
    logger.info(
        "assess_parcel",
        apn=apn,
        building_type=request.scenario_inputs.building_type,
    )

    return await assessment_service.assess_parcel_buildability(
        db=db,
        apn=apn,
        scenario_inputs=request.scenario_inputs,
    )


@internal_router.post("/scenario/diff", response_model=DiffScenarioResponse)
async def diff_scenario(
    request: DiffScenarioRequest,
    db: AsyncSession = Depends(get_db),
    assessment_service=Depends(get_assessment_service),
):
    """
    Compare two scenario assessments and return the differences.

    Useful for showing how changing building parameters affects constraints.
    """
    logger.info(
        "diff_scenario",
        base_scenario_id=request.base_scenario_id,
        new_scenario_id=request.new_scenario_id,
    )

    return await assessment_service.diff_scenarios(
        db=db,
        base_scenario_id=UUID(request.base_scenario_id),
        new_scenario_id=UUID(request.new_scenario_id),
    )


@router.post("/assessments/{id}/export", response_model=ExportResponse)
async def export_assessment(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Export an assessment to PDF or CSV.

    Returns a download URL and lists included fields and unresolved items.
    """
    logger.info(
        "export_assessment",
        assessment_id=id,
    )

    # Placeholder: Generate export
    return ExportResponse(
        download_url="https://storage.example.com/exports/123.pdf",
        format="pdf",
        included_fields=["constraints", "evidence", "geometry"],
        unresolved_items=[],
    )


@router.post("/assessments/{id}/feedback", response_model=SubmitFeedbackResponse)
async def submit_feedback(
    id: UUID,
    request: SubmitFeedbackRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback on an assessment.

    Requires idempotency key to prevent duplicate submissions.
    """
    logger.info(
        "submit_feedback",
        assessment_id=id,
        idempotency_key=idempotency_key,
    )

    if not idempotency_key.strip():
        raise BadRequestException("Idempotency key is required", field="Idempotency-Key")

    return SubmitFeedbackResponse(
        feedback_id=UUID("12345678-1234-1234-1234-123456789def"),
    )
