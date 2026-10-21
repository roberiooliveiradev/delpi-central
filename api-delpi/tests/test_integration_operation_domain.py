"""Domain tests — integration operation state machine."""

from __future__ import annotations

import pytest

from app.domain.integrations.integration_operation import (
    ALLOWED_TRANSITIONS,
    INDETERMINATE_STATUSES,
    TERMINAL_STATUSES,
    IntegrationStatus,
    InvalidTransitionError,
    assert_transition,
)


@pytest.mark.parametrize(
    "source,target",
    [
        ("CREATED", "SENDING"),
        ("CREATED", "FAILED_PRE_SEND"),
        ("SENDING", "ACKNOWLEDGED"),
        ("SENDING", "REJECTED"),
        ("SENDING", "UNKNOWN"),
        ("ACKNOWLEDGED", "CONFIRMED"),
        ("ACKNOWLEDGED", "RECONCILIATION_REQUIRED"),
        ("UNKNOWN", "CONFIRMED"),
        ("UNKNOWN", "RECONCILIATION_REQUIRED"),
        ("RECONCILIATION_REQUIRED", "CONFIRMED"),
    ],
)
def test_allowed_transitions(source: str, target: str) -> None:
    assert_transition(IntegrationStatus(source), IntegrationStatus(target))


@pytest.mark.parametrize(
    "source,target",
    [
        ("CREATED", "CONFIRMED"),
        ("CREATED", "ACKNOWLEDGED"),
        ("CREATED", "UNKNOWN"),
        ("SENDING", "CONFIRMED"),
        ("SENDING", "CREATED"),
        ("SENDING", "RECONCILIATION_REQUIRED"),
        ("ACKNOWLEDGED", "REJECTED"),
        ("ACKNOWLEDGED", "SENDING"),
        ("UNKNOWN", "REJECTED"),  # never reclassify UNKNOWN without proof
        ("UNKNOWN", "ACKNOWLEDGED"),
        ("CONFIRMED", "UNKNOWN"),
        ("REJECTED", "SENDING"),
        ("FAILED_PRE_SEND", "SENDING"),
        ("RECONCILIATION_REQUIRED", "REJECTED"),
    ],
)
def test_forbidden_transitions(source: str, target: str) -> None:
    with pytest.raises(InvalidTransitionError):
        assert_transition(IntegrationStatus(source), IntegrationStatus(target))


def test_terminal_states_have_no_outgoing() -> None:
    for status in TERMINAL_STATUSES:
        assert ALLOWED_TRANSITIONS[status] == frozenset()


def test_terminal_states_cover_expected() -> None:
    assert TERMINAL_STATUSES == {
        IntegrationStatus.CONFIRMED,
        IntegrationStatus.REJECTED,
        IntegrationStatus.FAILED_PRE_SEND,
    }


def test_indeterminate_states() -> None:
    assert IntegrationStatus.SENDING in INDETERMINATE_STATUSES
    assert IntegrationStatus.UNKNOWN in INDETERMINATE_STATUSES
    assert IntegrationStatus.ACKNOWLEDGED not in INDETERMINATE_STATUSES


def test_every_status_has_transition_map_entry() -> None:
    for status in IntegrationStatus:
        assert status in ALLOWED_TRANSITIONS


def test_invalid_transition_error_carries_states() -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        assert_transition(IntegrationStatus.UNKNOWN, IntegrationStatus.REJECTED)
    assert exc_info.value.status_from == "UNKNOWN"
    assert exc_info.value.status_to == "REJECTED"
    assert exc_info.value.code == "INTEGRATION_OPERATION_INVALID_TRANSITION"
