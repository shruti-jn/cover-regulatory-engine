"""
RuleProvenance model - Traceability link connecting an extracted rule back to source text.
"""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, Integer, ForeignKey

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.extracted_rule import ExtractedRule
    from src.models.ingested_document import IngestedDocument


class RuleProvenance(Base):
    """
    Traceability link connecting an extracted rule back to the exact text chunk in the source document.
    
    Provides auditability and allows users to verify rule sources.
    """

    __tablename__ = "rule_provenance"

    # The text excerpt that the rule was extracted from
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    # Page number in the source document (if applicable)
    page_number: Mapped[int] = mapped_column(Integer, nullable=True)

    # Foreign key to the extracted rule
    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("extracted_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to the source document
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingested_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    rule: Mapped["ExtractedRule"] = relationship(back_populates="provenance_entries")
    document: Mapped["IngestedDocument"] = relationship(back_populates="rule_provenance_entries")

    def __repr__(self) -> str:
        return f"<RuleProvenance(id={self.id}, rule_id={self.rule_id}, page={self.page_number})>"
