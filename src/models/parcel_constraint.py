"""
ParcelConstraint model - The application of an ExtractedRule to a specific Assessment.
"""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.assessment import Assessment
    from src.models.extracted_rule import ExtractedRule


class ProvenanceState:
    """Provenance state constants."""
    DETERMINISTIC = "deterministic"
    INTERPRETED = "interpreted"
    UNRESOLVED = "unresolved"


class ParcelConstraint(Base):
    """
    The application of an ExtractedRule to a specific Assessment.
    
    Stores the derived geometry (e.g., setback polygon) and evidence array
    for traceability. The scenario_hash is denormalized from Assessment for
    direct querying.
    """

    __tablename__ = "parcel_constraints"

    # Denormalized scenario hash from Assessment for direct querying
    scenario_hash: Mapped[str] = mapped_column(nullable=False, index=True)

    # Whether this constraint is active for the current assessment
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Provenance state: deterministic, interpreted, or unresolved
    provenance_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ProvenanceState.DETERMINISTIC,
        index=True,
    )

    # Evidence array for traceability
    # Array of objects with citations and sources
    evidence: Mapped[list] = mapped_column(JSONB, default=list)

    # Derived geometry (e.g., setback polygon) using PostGIS native type
    derived_geometry: Mapped[Geometry] = mapped_column(
        Geometry("POLYGON", srid=4326),
        nullable=True,
    )

    # Foreign key to Assessment
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to ExtractedRule (the rule that generated this constraint)
    extracted_rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("extracted_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(back_populates="constraints")
    extracted_rule: Mapped["ExtractedRule"] = relationship(back_populates="parcel_constraints")

    def __repr__(self) -> str:
        return f"<ParcelConstraint(id={self.id}, assessment_id={self.assessment_id}, state={self.provenance_state})>"
