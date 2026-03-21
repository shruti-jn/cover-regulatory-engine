"""
Custom exceptions and error handling for the API.

All errors use the standardized error envelope.
"""

from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
import structlog

from src.schemas.base import ErrorResponse, ErrorDetail

logger = structlog.get_logger()


class APIException(Exception):
    """Base API exception with error code and message."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        field: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


class NotFoundException(APIException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class BadRequestException(APIException):
    """Bad request exception."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            code="BAD_REQUEST",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field=field,
        )


class UnauthorizedException(APIException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(APIException):
    """Forbidden exception."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictException(APIException):
    """Resource conflict exception."""

    def __init__(self, message: str):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class IdempotencyException(APIException):
    """Idempotency key conflict exception."""

    def __init__(self, key: str):
        super().__init__(
            code="IDEMPOTENCY_KEY_USED",
            message=f"Idempotency key already used: {key}",
            status_code=status.HTTP_409_CONFLICT,
        )


class ServiceUnavailableException(APIException):
    """Service unavailable exception."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class GeocodingException(APIException):
    """Geocoding service exception."""

    def __init__(self, message: str = "Geocoding service error"):
        super().__init__(
            code="GEOCODING_ERROR",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def create_error_response(exception: APIException) -> JSONResponse:
    """Create a standardized error response from an API exception."""
    error_detail = ErrorDetail(
        code=exception.code,
        message=exception.message,
        field=exception.field,
    )
    response = ErrorResponse(error=error_detail)

    return JSONResponse(
        status_code=exception.status_code,
        content=response.model_dump(),
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle API exceptions."""
    logger.warning(
        "api_exception",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        path=str(request.url.path),
        method=request.method,
    )
    return create_error_response(exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "unexpected_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url.path),
        method=request.method,
    )

    error_detail = ErrorDetail(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
    )
    response = ErrorResponse(error=error_detail)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )
