"""
Assessment export schemas.
"""

from pydantic import Field

from src.schemas.base import BaseSchema


class ExportResponse(BaseSchema):
    """Response for assessment export."""

    download_url: str
    format: str = Field(..., description="pdf or csv")
    included_fields: list[str]
    unresolved_items: list[str]
