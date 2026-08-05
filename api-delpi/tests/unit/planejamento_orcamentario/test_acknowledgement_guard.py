import pytest

from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
)


class FakeRepo:
    def __init__(self, exercise=None, guidance=None, ack=None):
        self.exercise = exercise
        self.guidance = guidance
        self.ack = ack

    def get_active_exercise(self):
        return self.exercise

    def get_current_published_guidance(self, exercise_id: str):
        return self.guidance

    def get_acknowledgement(self, *, user_sub: str, guidance_version_id: str):
        return self.ack


def test_guard_requires_ack():
    repo = FakeRepo(
        exercise={"id": "e1", "status": "open"},
        guidance={"id": "g1", "version_number": 1},
        ack=None,
    )
    guard = BudgetGuidanceAcknowledgementGuard(repo)
    state = guard.evaluate(user_sub="u1")
    assert state["modules_unlocked"] is False
    with pytest.raises(BudgetGuidanceAcknowledgementRequiredError):
        guard.assert_modules_unlocked(user_sub="u1")


def test_guard_unlocks_when_ack_and_open():
    repo = FakeRepo(
        exercise={"id": "e1", "status": "open"},
        guidance={"id": "g1", "version_number": 1},
        ack={"id": "a1", "acknowledged_at": "2026-01-01T00:00:00+00:00"},
    )
    guard = BudgetGuidanceAcknowledgementGuard(repo)
    state = guard.evaluate(user_sub="u1")
    assert state["modules_unlocked"] is True
