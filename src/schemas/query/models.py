"""
Follow-up query schemas.
"""

from src.schemas.base import BaseSchema


class FollowUpQueryRequest(BaseSchema):
    """Request for a grounded follow-up query on an assessment."""

    question: str


class CitedSource(BaseSchema):
    """Source citation for a grounded answer."""

    source_url: str | None = None
    page_number: int | None = None


class FollowUpQueryResponse(BaseSchema):
    """Response for a grounded follow-up query."""

    answer: str
    cited_sources: list[CitedSource]
