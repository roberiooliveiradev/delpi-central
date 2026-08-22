import pytest

from travel_expenses_app.domain.services.status_transition_service import (
    TravelReportStatusTransitionError,
    TravelReportStatusTransitionService,
)


def test_draft_is_editable_and_deletable():
    assert TravelReportStatusTransitionService.can_edit("draft") is True
    assert TravelReportStatusTransitionService.can_delete("draft") is True
    assert TravelReportStatusTransitionService.can_delete("submitted") is False


def test_allowed_future_transition():
    TravelReportStatusTransitionService.assert_transition("draft", "submitted")


def test_invalid_transition_raises():
    with pytest.raises(TravelReportStatusTransitionError):
        TravelReportStatusTransitionService.assert_transition("draft", "closed")
