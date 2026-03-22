from __future__ import annotations

import pytest

from src.core.observability import (
    emit_required_log,
    get_metrics_registry,
)


class _StubLogger:
    def __init__(self):
        self.calls = []

    def warning(self, event, **kwargs):
        self.calls.append((event, kwargs))


def test_metrics_registry_records_required_metrics():
    metrics = get_metrics_registry()
    metrics.fsm_state_latency_ms.clear()
    metrics.fsm_error_rate = 0
    metrics.unsupported_claim_rate = 0
    metrics.abstention_rate = 0

    metrics.record_fsm_state_latency("GEOCODING", 12.5)
    metrics.increment_fsm_error()
    metrics.increment_unsupported_claim()
    metrics.increment_abstention()

    snapshot = metrics.snapshot()
    assert snapshot["fsm_state_latency_ms"]["GEOCODING"] == [12.5]
    assert snapshot["fsm_error_rate"] == 1
    assert snapshot["unsupported_claim_rate"] == 1
    assert snapshot["abstention_rate"] == 1


def test_emit_required_log_enforces_allowed_event_keys():
    logger = _StubLogger()

    emit_required_log(logger, "GCP_API_FAILURE", request_id="req-1", provider="googlemaps")
    assert logger.calls[0][0] == "GCP_API_FAILURE"
    assert logger.calls[0][1]["event_key"] == "GCP_API_FAILURE"
    assert logger.calls[0][1]["request_id"] == "req-1"

    with pytest.raises(ValueError):
        emit_required_log(logger, "NOT_ALLOWED")
