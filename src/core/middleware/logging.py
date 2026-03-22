"""
Structured logging middleware.
"""

import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.observability import get_request_id

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = get_request_id(getattr(request.state, "request_id", "unknown"))

        logger.info(
            "request_start",
            event_key="request_start",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                "request_error",
                event_key="request_error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error_type=type(exc).__name__,
            )
            raise
        finally:
            if response is not None:
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "request_end",
                    event_key="request_end",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2),
                )
