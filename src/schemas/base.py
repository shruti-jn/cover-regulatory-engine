"""
Base Pydantic v2 schemas with standardized error envelope.

All request/response models inherit from these base classes.
"""

from typing import Optional, TypeVar, Generic
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with Pydantic v2 configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={"examples": []},
    )


class ErrorDetail(BaseSchema):
    """Error detail for the error envelope."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error, if applicable")


class ErrorResponse(BaseSchema):
    """
    Standardized error response envelope.

    All API errors use this format for consistency.
    """

    error: ErrorDetail


class SuccessResponse(BaseSchema):
    """Base success response with status."""

    status: str = "success"


class PaginatedResponse(BaseSchema, Generic[T]):
    """Base paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class TimestampedSchema(BaseSchema):
    """Base schema with created_at and updated_at timestamps."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Base schema with UUID primary key."""

    id: UUID
