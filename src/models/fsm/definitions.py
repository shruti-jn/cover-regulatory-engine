"""
Workflow state machine definitions derived from workflow_fsm.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TransitionDefinition:
    event: str
    target: str
    actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MachineDefinition:
    machine_id: str
    initial_state: str
    states: dict[str, tuple[TransitionDefinition, ...]] = field(default_factory=dict)


PARCEL_EVALUATION_SYNC_DEFINITION = MachineDefinition(
    machine_id="ParcelEvaluationSync",
    initial_state="IDLE",
    states={
        "IDLE": (TransitionDefinition(event="SUBMIT_ADDRESS", target="GEOCODING"),),
        "GEOCODING": (
            TransitionDefinition(
                event="GEOCODE_SUCCESS",
                target="FETCHING_PARCEL_FACTS",
                actions=("StoreGCPMetadata",),
            ),
            TransitionDefinition(event="GEOCODE_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "FETCHING_PARCEL_FACTS": (
            TransitionDefinition(event="FACTS_LOADED", target="DETERMINISTIC_RULE_EVALUATION"),
            TransitionDefinition(event="FACTS_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "DETERMINISTIC_RULE_EVALUATION": (
            TransitionDefinition(event="RULES_EVALUATED", target="SPATIAL_CALCULATION"),
            TransitionDefinition(event="EVALUATION_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "SPATIAL_CALCULATION": (
            TransitionDefinition(event="GEOMETRY_DERIVED", target="LLM_EDGE_CASE_SYNTHESIS"),
            TransitionDefinition(event="SPATIAL_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "LLM_EDGE_CASE_SYNTHESIS": (
            TransitionDefinition(event="SYNTHESIS_COMPLETE", target="ASSESSMENT_READY"),
            TransitionDefinition(event="LLM_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "ASSESSMENT_READY": (
            TransitionDefinition(
                event="CHANGE_SCENARIO",
                target="DETERMINISTIC_RULE_EVALUATION",
                actions=("DiffScenarioState",),
            ),
            TransitionDefinition(event="EXPORT_REQUESTED", target="EXPORTING"),
            TransitionDefinition(event="FEEDBACK_SUBMITTED", target="PROCESSING_FEEDBACK"),
            TransitionDefinition(event="QUERY_SUBMITTED", target="QUERYING_FOLLOW_UP"),
        ),
        "QUERYING_FOLLOW_UP": (
            TransitionDefinition(event="QUERY_SUCCESS", target="ASSESSMENT_READY"),
            TransitionDefinition(event="QUERY_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "EXPORTING": (
            TransitionDefinition(event="EXPORT_SUCCESS", target="ASSESSMENT_READY"),
            TransitionDefinition(event="EXPORT_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "PROCESSING_FEEDBACK": (
            TransitionDefinition(event="FEEDBACK_SAVED", target="ASSESSMENT_READY"),
            TransitionDefinition(event="FEEDBACK_FAILURE", target="ERROR_RECOVERABLE"),
        ),
        "ERROR_RECOVERABLE": (
            TransitionDefinition(event="RETRY", target="GEOCODING"),
            TransitionDefinition(event="RESET", target="IDLE"),
        ),
    },
)


RULE_EXTRACTION_ASYNC_DEFINITION = MachineDefinition(
    machine_id="RuleExtractionAsync",
    initial_state="WAITING_FOR_DOCUMENT",
    states={
        "WAITING_FOR_DOCUMENT": (
            TransitionDefinition(event="INGEST_TRIGGERED", target="PARSING_PDF"),
        ),
        "PARSING_PDF": (
            TransitionDefinition(event="PARSE_SUCCESS", target="LLM_RULE_EXTRACTION"),
            TransitionDefinition(event="PARSE_FAILURE", target="EXTRACTION_FAILED"),
        ),
        "LLM_RULE_EXTRACTION": (
            TransitionDefinition(event="EXTRACTION_COMPLETE", target="CACHING_DETERMINISTIC_DB"),
            TransitionDefinition(event="LLM_FAILURE", target="EXTRACTION_FAILED"),
        ),
        "CACHING_DETERMINISTIC_DB": (
            TransitionDefinition(event="CACHE_SUCCESS", target="WAITING_FOR_DOCUMENT"),
            TransitionDefinition(event="DB_FAILURE", target="EXTRACTION_FAILED"),
        ),
        "EXTRACTION_FAILED": (
            TransitionDefinition(
                event="RETRY_EXTRACTION",
                target="PARSING_PDF",
                actions=("ResetExtractionState",),
            ),
        ),
    },
)
