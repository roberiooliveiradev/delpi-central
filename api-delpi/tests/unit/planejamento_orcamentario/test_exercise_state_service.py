import pytest

from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetExerciseInvalidTransitionError,
)
from app.domain.services.planejamento_orcamentario.exercise_state_service import (
    assert_transition,
    modules_unlocked_for_exercise,
)


def test_publish_draft_to_open():
    assert_transition("draft", "open")


def test_invalid_transition_archived():
    with pytest.raises(BudgetExerciseInvalidTransitionError):
        assert_transition("archived", "open")


def test_modules_unlocked_only_open_closing():
    assert modules_unlocked_for_exercise("open") is True
    assert modules_unlocked_for_exercise("closing") is True
    assert modules_unlocked_for_exercise("draft") is False
    assert modules_unlocked_for_exercise("locked") is False
