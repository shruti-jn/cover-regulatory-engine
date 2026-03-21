"""
Pydantic v2 schemas for API request/response validation.

All schemas use Pydantic v2 BaseModel with model_config.
"""

# Base schemas
from src.schemas.base import (
    BaseSchema,
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse,
    TimestampedSchema,
    UUIDSchema,
)

# Parcel schemas
from src.schemas.parcel import (
    GeoCodingMetadata,
    GeoJSONGeometry,
    ParcelBase,
    ParcelCreate,
    ParcelResponse,
    GeocodeRequest,
    GeocodeCandidate,
    GeocodeResponse,
    StoreGCPMetadataRequest,
    StoreGCPMetadataResponse,
)

# Assessment schemas
from src.schemas.assessment import (
    AssessmentStatus,
    ProvenanceState,
    ScenarioInputs,
    ConstraintEvidence,
    ConstraintValue,
    ConstraintResponse,
    ScenarioDiffConstraint,
    ScenarioDiff,
    CreateAssessmentRequest,
    AssessmentResponse,
    DiffScenarioRequest,
    DiffScenarioResponse,
    FollowUpQueryRequest,
    CitedSource,
    FollowUpQueryResponse,
    ExportRequest,
    ExportResponse,
    SubmitFeedbackRequest,
    SubmitFeedbackResponse,
)

# Admin schemas
from src.schemas.admin import (
    IngestionStatus,
    TriggerIngestionRequest,
    TriggerIngestionResponse,
    IngestionStatusResponse,
    PipelineStatusResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "TimestampedSchema",
    "UUIDSchema",
    # Parcel
    "GeoCodingMetadata",
    "GeoJSONGeometry",
    "ParcelBase",
    "ParcelCreate",
    "ParcelResponse",
    "GeocodeRequest",
    "GeocodeCandidate",
    "GeocodeResponse",
    "StoreGCPMetadataRequest",
    "StoreGCPMetadataResponse",
    # Assessment
    "AssessmentStatus",
    "ProvenanceState",
    "ScenarioInputs",
    "ConstraintEvidence",
    "ConstraintValue",
    "ConstraintResponse",
    "ScenarioDiffConstraint",
    "ScenarioDiff",
    "CreateAssessmentRequest",
    "AssessmentResponse",
    "DiffScenarioRequest",
    "DiffScenarioResponse",
    "FollowUpQueryRequest",
    "CitedSource",
    "FollowUpQueryResponse",
    "ExportRequest",
    "ExportResponse",
    "SubmitFeedbackRequest",
    "SubmitFeedbackResponse",
    # Admin
    "IngestionStatus",
    "TriggerIngestionRequest",
    "TriggerIngestionResponse",
    "IngestionStatusResponse",
    "PipelineStatusResponse",
]
