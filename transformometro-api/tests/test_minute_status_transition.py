import pytest

from tm_app.domain.services.minute_status_transition_service import (
    MinuteStatusTransitionError,
    MinuteStatusTransitionService,
)


def test_signature_progress_and_valid_transition():
    assert MinuteStatusTransitionService.status_after_signature_progress(
        signed_count=1, required_count=2
    ) == "partially_signed"
    MinuteStatusTransitionService.assert_transition("signed", "finalized")


def test_invalid_transition_is_rejected():
    with pytest.raises(MinuteStatusTransitionError):
        MinuteStatusTransitionService.assert_transition("draft", "finalized")
