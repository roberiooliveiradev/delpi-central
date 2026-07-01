from __future__ import annotations

import pytest

from cx_app.application.services.feedback_service import (
    FeedbackAlreadyExistsError,
    FeedbackService,
    FeedbackValidationError,
)
from cx_app.application.services.participant_service import ParticipantNotFoundError
from cx_app.domain.feedback import FeedbackInput

_ACTIVE = {"id": "p1", "public_token": "tok", "full_name": "Ana Souza", "is_active": True}


class FakeParticipants:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def get_by_token(self, token: str):
        if self._row and self._row.get("public_token") == token:
            return self._row
        return None


class FakeFeedback:
    def __init__(self, existing: bool = False) -> None:
        self.existing = existing
        self.created: list[dict] = []

    def exists_for_participant(self, participant_id: str) -> bool:
        return self.existing

    def create(self, data: dict) -> dict:
        self.created.append(data)
        return {**data, "id": "fb1", "created_at": "2026-07-01T12:00:00Z"}


def _service(row=_ACTIVE, existing=False):
    feedback = FakeFeedback(existing=existing)
    service = FeedbackService(
        participant_repository=FakeParticipants(row),
        feedback_repository=feedback,
    )
    return service, feedback


def test_submit_success_persists_and_returns_view():
    service, feedback = _service()
    result = service.submit(
        "tok", FeedbackInput(rating=5, liked_most="  Montar o cabo  ", suggestions="")
    )
    assert result["rating"] == 5
    assert result["likedMost"] == "Montar o cabo"
    assert len(feedback.created) == 1
    assert feedback.created[0]["participant_id"] == "p1"
    # texto vazio vira None
    assert feedback.created[0]["suggestions"] is None


def test_submit_unknown_token_raises_not_found():
    service, _ = _service(row=None)
    with pytest.raises(ParticipantNotFoundError):
        service.submit("tok", FeedbackInput(rating=4))


def test_submit_inactive_participant_raises_not_found():
    service, _ = _service(row={**_ACTIVE, "is_active": False})
    with pytest.raises(ParticipantNotFoundError):
        service.submit("tok", FeedbackInput(rating=4))


def test_submit_twice_raises_already_exists():
    service, _ = _service(existing=True)
    with pytest.raises(FeedbackAlreadyExistsError):
        service.submit("tok", FeedbackInput(rating=4))


@pytest.mark.parametrize("rating", [0, 6, -1, 10])
def test_submit_invalid_rating_raises_validation(rating):
    service, _ = _service()
    with pytest.raises(FeedbackValidationError):
        service.submit("tok", FeedbackInput(rating=rating))


def test_get_status_reports_submitted_flag():
    service, _ = _service(existing=True)
    status = service.get_status("tok")
    assert status["fullName"] == "Ana Souza"
    assert status["submitted"] is True


def test_get_status_unknown_token_raises_not_found():
    service, _ = _service(row=None)
    with pytest.raises(ParticipantNotFoundError):
        service.get_status("tok")
