"""
Core application components.

Exports:
- config: Pydantic Settings for environment variables
- exceptions: Custom API exceptions and error handlers
- middleware: Request ID and logging middleware
"""

from src.core.config import Settings, settings
from src.core.exceptions import (
    APIException,
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    IdempotencyException,
    ServiceUnavailableException,
    GeocodingException,
    api_exception_handler,
    general_exception_handler,
)

__all__ = [
    "Settings",
    "settings",
    "APIException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "IdempotencyException",
    "ServiceUnavailableException",
    "GeocodingException",
    "api_exception_handler",
    "general_exception_handler",
]
