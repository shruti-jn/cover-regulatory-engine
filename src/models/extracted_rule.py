"""
ExtractedRule model - A deterministic rule extracted from a document by the RAG pipeline.
"""

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from src.db.base import Base
from src.core.config import settings

if TYPE_CHECKING:
    from src.models.ingested_document import IngestedDocument
    from src.models.rule_provenance import RuleProvenance
    from src.models.parcel_constraint import ParcelConstraint


class RuleDomain:
    """Rule domain constants."""
    ZONING = "zoning"
    SETBACK = "setback"
    HEIGHT = "height"
    OVERLAY = "overlay"
    ADU = "adu"
    PARKING = "parking"


class RuleType:
    """Rule type constants."""
    DETERMINISTIC = "deterministic"
    INTERPRETED = "interpreted"
    UNRESOLVED = "unresolved"


class ExtractedRule(Base):
    """
    A deterministic rule extracted from a document by the async RAG pipeline.
    
    The constraint_value stores structured rule data (type, value, unit).
    The embedding vector enables similarity search for RAG retrieval.
    """

    __tablename__ = "extracted_rules"

    # Rule domain categorization
    domain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Rule type: deterministic, interpreted, or unresolved
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Structured representation of the rule
    # Schema: {type: string, value: string|number|boolean, unit: string}
    constraint_value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Confidence score (0.0 to 100.0) of the extraction
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=50.0,
    )

    # Vector embedding for RAG similarity search
    embedding: Mapped[List[float]] = mapped_column(
        Vector(settings.VECTOR_DIMENSIONS),
        nullable=True,
    )

    # Foreign key to source document
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingested_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    document: Mapped["IngestedDocument"] = relationship(back_populates="extracted_rules")

    provenance_entries: Mapped[List["RuleProvenance"]] = relationship(
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    parcel_constraints: Mapped[List["ParcelConstraint"]] = relationship(
        back_populates="extracted_rule",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ExtractedRule(id={self.id}, domain={self.domain}, type={self.rule_type})>"
