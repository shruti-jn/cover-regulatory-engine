"""
In-memory observability metrics registry.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


FSM_STATES = (
    "GEOCODING",
    "FETCHING_PARCEL_FACTS",
    "DETERMINISTIC_RULE_EVALUATION",
    "SPATIAL_CALCULATION",
    "LLM_EDGE_CASE_SYNTHESIS",
    "PARSING_PDF",
    "LLM_RULE_EXTRACTION",
    "CACHING_DETERMINISTIC_DB",
)


@dataclass
class ObservabilityMetrics:
    """In-memory counters and latency buckets for required observability metrics."""

    fsm_state_latency_ms: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    fsm_error_rate: int = 0
    unsupported_claim_rate: int = 0
    abstention_rate: int = 0

    def record_fsm_state_latency(self, state: str, duration_ms: float) -> None:
        if state not in FSM_STATES:
            raise ValueError(f"Unsupported FSM state metric: {state}")
        self.fsm_state_latency_ms[state].append(duration_ms)

    def increment_fsm_error(self) -> None:
        self.fsm_error_rate += 1

    def increment_unsupported_claim(self) -> None:
        self.unsupported_claim_rate += 1

    def increment_abstention(self) -> None:
        self.abstention_rate += 1

    def snapshot(self) -> dict[str, object]:
        return {
            "fsm_state_latency_ms": {state: values[:] for state, values in self.fsm_state_latency_ms.items()},
            "fsm_error_rate": self.fsm_error_rate,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "abstention_rate": self.abstention_rate,
        }


_registry: ObservabilityMetrics | None = None


def get_metrics_registry() -> ObservabilityMetrics:
    global _registry
    if _registry is None:
        _registry = ObservabilityMetrics()
    return _registry
