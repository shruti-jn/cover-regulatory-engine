"""
Structured observability logging helpers.
"""

from __future__ import annotations

import structlog

REQUIRED_LOG_EVENTS = {
    "GCP_API_FAILURE",
    "LLM_HALLUCINATION_BLOCKED",
    "RAG_EXTRACTION_FAILED",
}


def bind_request_context(request_id: str) -> None:
    """Bind request context to structlog contextvars."""
    structlog.contextvars.bind_contextvars(request_id=request_id)


def clear_request_context() -> None:
    """Clear request-bound structlog contextvars."""
    structlog.contextvars.clear_contextvars()


def get_request_id(default: str = "unknown") -> str:
    """Return the currently bound request id, if any."""
    context = structlog.contextvars.get_contextvars()
    return str(context.get("request_id", default))


def emit_required_log(
    logger,
    event_key: str,
    *,
    request_id: str | None = None,
    **fields,
) -> None:
    """Emit one of the required observability log events."""
    if event_key not in REQUIRED_LOG_EVENTS:
        raise ValueError(f"Unsupported required log event: {event_key}")

    logger.warning(
        event_key,
        event_key=event_key,
        request_id=request_id or get_request_id(),
        **fields,
    )
