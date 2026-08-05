from __future__ import annotations

from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetExerciseInvalidTransitionError,
)

EXERCISE_STATUSES = frozenset({"draft", "open", "closing", "locked", "archived"})

# publish = draft→open (brief "published"); close ≈ closing; archive after locked
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"open", "archived"}),
    "open": frozenset({"closing", "locked"}),
    "closing": frozenset({"locked", "open"}),
    "locked": frozenset({"open", "archived"}),
    "archived": frozenset(),
}


def assert_transition(current: str, target: str) -> None:
    if current not in EXERCISE_STATUSES or target not in EXERCISE_STATUSES:
        raise BudgetExerciseInvalidTransitionError(
            f"Status inválido: {current} → {target}.",
            code="budget_exercise_invalid_transition",
        )
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise BudgetExerciseInvalidTransitionError(
            f"Transição não permitida: {current} → {target}.",
        )


def modules_unlocked_for_exercise(status: str) -> bool:
    return status in {"open", "closing"}
