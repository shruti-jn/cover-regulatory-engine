"""
Assessment and constraint Pydantic v2 schemas.
"""

from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import Field

from src.schemas.base import BaseSchema, TimestampedSchema, UUIDSchema
from src.schemas.parcel import GeoJSONGeometry


class AssessmentStatus:
    """Assessment status constants."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ProvenanceState:
    """Provenance state constants."""
    DETERMINISTIC = "deterministic"
    INTERPRETED = "interpreted"
    UNRESOLVED = "unresolved"


class ScenarioInputs(BaseSchema):
    """Building scenario inputs for assessment."""

    building_type: str = Field(..., description="SFH, ADU, or GUEST_HOUSE")
    bedrooms: Optional[int] = None


class ConstraintEvidence(BaseSchema):
    """Evidence for a constraint."""

    source_title: str
    source_url: Optional[str] = None
    jurisdiction: str
    page_number: Optional[int] = None
    excerpt: Optional[str] = None


class ConstraintValue(BaseSchema):
    """Structured constraint value."""

    type: str
    value: Union[str, int, float, bool]


class ConstraintResponse(BaseSchema):
    """Constraint response schema."""

    domain: str = Field(..., description="zoning, setback, height, overlay, adu, parking")
    provenance_state: str = Field(..., description="deterministic, interpreted, or unresolved")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    constraint_value: ConstraintValue
    derived_geometry: Optional[GeoJSONGeometry] = None
    evidence: List[ConstraintEvidence]


class ScenarioDiffConstraint(BaseSchema):
    """Changed constraint in scenario diff."""

    domain: str
    before_value: Optional[Union[str, int, float, bool]]
    after_value: Optional[Union[str, int, float, bool]]
    confidence_delta: float
    geometry_changed: bool


class ScenarioDiff(BaseSchema):
    """Scenario diff result."""

    changed_constraints: List[ScenarioDiffConstraint]


class CreateAssessmentRequest(BaseSchema):
    """Request to create an assessment."""

    scenario_inputs: ScenarioInputs


class AssessmentResponse(BaseSchema):
    """Assessment response schema."""

    assessment_id: UUID
    parcel_geometry: GeoJSONGeometry
    constraints: List[ConstraintResponse]
    scenario_diff: Optional[ScenarioDiff] = None


class DiffScenarioRequest(BaseSchema):
    """Request to diff two scenarios."""

    base_scenario_id: str
    new_scenario_id: str


class DiffScenarioResponse(BaseSchema):
    """Response for scenario diff."""

    diff: ScenarioDiff


class FollowUpQueryRequest(BaseSchema):
    """Request for follow-up query on an assessment."""

    question: str


class CitedSource(BaseSchema):
    """Source citation for answer."""

    source_url: Optional[str] = None
    page_number: Optional[int] = None


class FollowUpQueryResponse(BaseSchema):
    """Response for follow-up query."""

    answer: str
    cited_sources: List[CitedSource]


class ExportRequest(BaseSchema):
    """Request to export an assessment."""

    pass


class ExportResponse(BaseSchema):
    """Response for assessment export."""

    download_url: str
    format: str = Field(..., description="pdf or csv")
    included_fields: List[str]
    unresolved_items: List[str]


class SubmitFeedbackRequest(BaseSchema):
    """Request to submit feedback on an assessment."""

    comment: str


class SubmitFeedbackResponse(BaseSchema):
    """Response for feedback submission."""

    feedback_id: UUID
