"""
SQLAlchemy 2.0 models for Cover Regulatory Engine.

All models use SQLAlchemy 2.0 DeclarativeBase with mapped_column().
Geometry columns use GeoAlchemy2 with PostGIS native types.
"""

from src.db.base import Base

# Spatial Reasoning context
from src.models.parcel import Parcel
from src.models.assessment import Assessment, AssessmentStatus
from src.models.parcel_constraint import ParcelConstraint, ProvenanceState
from src.models.feedback import Feedback, FeedbackStatus

# Regulatory Policy context
from src.models.ingested_document import IngestedDocument
from src.models.extracted_rule import ExtractedRule, RuleDomain, RuleType
from src.models.rule_provenance import RuleProvenance

# System Administration context
from src.models.user import User, UserRole
from src.models.ingestion_pipeline import IngestionPipelineStatus, PipelineStatus

__all__ = [
    # Base
    "Base",
    # Spatial Reasoning
    "Parcel",
    "Assessment",
    "AssessmentStatus",
    "ParcelConstraint",
    "ProvenanceState",
    "Feedback",
    "FeedbackStatus",
    # Regulatory Policy
    "IngestedDocument",
    "ExtractedRule",
    "RuleDomain",
    "RuleType",
    "RuleProvenance",
    # System Administration
    "User",
    "UserRole",
    "IngestionPipelineStatus",
    "PipelineStatus",
]
