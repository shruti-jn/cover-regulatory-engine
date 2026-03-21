"""
Workflow state machine runtime services.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog

from src.models.fsm import (
    PARCEL_EVALUATION_SYNC_DEFINITION,
    RULE_EXTRACTION_ASYNC_DEFINITION,
    MachineDefinition,
    TransitionDefinition,
)

logger = structlog.get_logger()
ActionHook = Callable[..., Any]


class WorkflowTransitionError(ValueError):
    """Raised when an invalid FSM transition is attempted."""


class WorkflowStateMachine:
    """Runtime wrapper for explicit workflow state machine definitions."""

    def __init__(
        self,
        definition: MachineDefinition,
        *,
        request_id: str | None = None,
        action_hooks: dict[str, ActionHook] | None = None,
    ) -> None:
        self.definition = definition
        self.state = definition.initial_state
        self.request_id = request_id or "unknown"
        self.action_hooks = action_hooks or {}

    def trigger(self, event: str, **context: Any) -> str:
        transition = self._get_transition(event)
        from_state = self.state
        self.state = transition.target

        logger.info(
            "fsm_transition",
            machine_id=self.definition.machine_id,
            from_state=from_state,
            to_state=self.state,
            trigger_event=event,
            request_id=self.request_id,
        )

        for action_name in transition.actions:
            action = self.action_hooks.get(action_name)
            if action is None:
                continue
            action(request_id=self.request_id, from_state=from_state, to_state=self.state, **context)

        return self.state

    def available_events(self) -> tuple[str, ...]:
        return tuple(transition.event for transition in self.definition.states[self.state])

    def _get_transition(self, event: str) -> TransitionDefinition:
        for transition in self.definition.states[self.state]:
            if transition.event == event:
                return transition

        raise WorkflowTransitionError(
            f"Event {event} is not valid from state {self.state} in {self.definition.machine_id}"
        )


def create_parcel_evaluation_machine(
    *,
    request_id: str | None = None,
    action_hooks: dict[str, ActionHook] | None = None,
) -> WorkflowStateMachine:
    return WorkflowStateMachine(
        PARCEL_EVALUATION_SYNC_DEFINITION,
        request_id=request_id,
        action_hooks=action_hooks,
    )


def create_rule_extraction_machine(
    *,
    request_id: str | None = None,
    action_hooks: dict[str, ActionHook] | None = None,
) -> WorkflowStateMachine:
    return WorkflowStateMachine(
        RULE_EXTRACTION_ASYNC_DEFINITION,
        request_id=request_id,
        action_hooks=action_hooks,
    )
