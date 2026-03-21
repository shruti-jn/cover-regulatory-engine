"""
IngestedDocument model - Source municipal zoning or regulatory document.
"""

from uuid import UUID
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.extracted_rule import ExtractedRule
    from src.models.rule_provenance import RuleProvenance


class IngestedDocument(Base):
    """
    Source municipal zoning or regulatory document ingested via the RAG pipeline.
    
    Stores the original document text and metadata for traceability.
    The version_hash enables checksum-based deduplication.
    """

    __tablename__ = "ingested_documents"

    # Document title
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Jurisdiction (e.g., "LA City", "LA County")
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Source URL where the document was retrieved
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # MD5 hash for deduplication (checksum-based ingestion)
    version_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Raw text content extracted from the document
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Additional metadata about the document.
    # The Python attribute avoids SQLAlchemy's reserved Declarative name.
    document_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    extracted_rules: Mapped[List["ExtractedRule"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    rule_provenance_entries: Mapped[List["RuleProvenance"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<IngestedDocument(id={self.id}, title={self.title}, jurisdiction={self.jurisdiction})>"
