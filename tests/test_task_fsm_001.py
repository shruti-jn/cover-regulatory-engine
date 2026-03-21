from __future__ import annotations

import pytest

from src.services.fsm import (
    WorkflowTransitionError,
    create_parcel_evaluation_machine,
    create_rule_extraction_machine,
)


def test_parcel_evaluation_machine_happy_path_and_actions():
    calls: list[tuple[str, str]] = []

    def store_gcp_metadata(**kwargs):
        calls.append(("StoreGCPMetadata", kwargs["to_state"]))

    def diff_scenario_state(**kwargs):
        calls.append(("DiffScenarioState", kwargs["to_state"]))

    machine = create_parcel_evaluation_machine(
        request_id="req-123",
        action_hooks={
            "StoreGCPMetadata": store_gcp_metadata,
            "DiffScenarioState": diff_scenario_state,
        },
    )

    assert machine.state == "IDLE"
    assert machine.trigger("SUBMIT_ADDRESS") == "GEOCODING"
    assert machine.trigger("GEOCODE_SUCCESS") == "FETCHING_PARCEL_FACTS"
    assert machine.trigger("FACTS_LOADED") == "DETERMINISTIC_RULE_EVALUATION"
    assert machine.trigger("RULES_EVALUATED") == "SPATIAL_CALCULATION"
    assert machine.trigger("GEOMETRY_DERIVED") == "LLM_EDGE_CASE_SYNTHESIS"
    assert machine.trigger("SYNTHESIS_COMPLETE") == "ASSESSMENT_READY"
    assert machine.trigger("CHANGE_SCENARIO") == "DETERMINISTIC_RULE_EVALUATION"

    assert calls == [
        ("StoreGCPMetadata", "FETCHING_PARCEL_FACTS"),
        ("DiffScenarioState", "DETERMINISTIC_RULE_EVALUATION"),
    ]


def test_parcel_evaluation_error_recoverable_supports_retry_and_reset():
    machine = create_parcel_evaluation_machine()

    machine.trigger("SUBMIT_ADDRESS")
    assert machine.trigger("GEOCODE_FAILURE") == "ERROR_RECOVERABLE"
    assert machine.trigger("RETRY") == "GEOCODING"
    assert machine.trigger("GEOCODE_FAILURE") == "ERROR_RECOVERABLE"
    assert machine.trigger("RESET") == "IDLE"


def test_rule_extraction_machine_retry_action():
    calls: list[str] = []

    def reset_extraction_state(**kwargs):
        calls.append(kwargs["to_state"])

    machine = create_rule_extraction_machine(
        action_hooks={"ResetExtractionState": reset_extraction_state}
    )

    assert machine.trigger("INGEST_TRIGGERED") == "PARSING_PDF"
    assert machine.trigger("PARSE_FAILURE") == "EXTRACTION_FAILED"
    assert machine.trigger("RETRY_EXTRACTION") == "PARSING_PDF"
    assert calls == ["PARSING_PDF"]


def test_invalid_transition_raises_error():
    machine = create_parcel_evaluation_machine()

    with pytest.raises(WorkflowTransitionError):
        machine.trigger("FACTS_LOADED")
