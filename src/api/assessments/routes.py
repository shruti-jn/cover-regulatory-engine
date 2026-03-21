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

from fastapi import APIRouter, Depends, Path, Header, status
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
from src.schemas.parcel import GeoJSONGeometry
from src.core.exceptions import (
    NotFoundException,
    BadRequestException,
    IdempotencyException,
    create_error_response,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["assessments"])


@router.post("/parcels/{apn}/assess", response_model=AssessmentResponse)
async def assess_parcel_buildability(
    apn: str,
    request: CreateAssessmentRequest,
    db: AsyncSession = Depends(get_db),
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

    # Placeholder: Run assessment pipeline
    # For now, return mock data
    return AssessmentResponse(
        assessment_id=UUID("12345678-1234-1234-1234-123456789abc"),
        parcel_geometry=GeoJSONGeometry(
            type="Polygon",
            coordinates=[[[-118.25, 34.05], [-118.24, 34.05], [-118.24, 34.06], [-118.25, 34.06], [-118.25, 34.05]]],
        ),
        constraints=[
            ConstraintResponse(
                domain="setback",
                provenance_state="deterministic",
                confidence_score=0.95,
                constraint_value=ConstraintValue(type="distance", value=20),
                evidence=[
                    ConstraintEvidence(
                        source_title="LAMC Chapter 12.07",
                        source_url="https://codelibrary.amlegal.com/...",
                        jurisdiction="LA City",
                        page_number=45,
                        excerpt="Front setback shall be 20 feet in RS zone",
                    )
                ],
            )
        ],
        scenario_diff=None,
    )


@router.post("/scenario/diff", response_model=DiffScenarioResponse)
async def diff_scenario(
    request: DiffScenarioRequest,
    db: AsyncSession = Depends(get_db),
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

    # Placeholder: Compute diff
    return DiffScenarioResponse(
        diff=ScenarioDiff(changed_constraints=[])
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

    # Placeholder: Store feedback
    # Check for duplicate idempotency key
    return SubmitFeedbackResponse(
        feedback_id=UUID("12345678-1234-1234-1234-123456789def"),
    )
