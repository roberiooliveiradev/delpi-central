from __future__ import annotations

from si_app.application.services.strategic_indicators.indicator_goal_validation_error import (
    StrategicIndicatorsIndicatorGoalValidationError,
)
from si_app.shared.goal_scope import (
    VALID_GOAL_SCOPE_BRANCHES,
    indicator_allows_branch_goals,
    normalize_goal_scope_branch,
)


def validate_goal_scope_branch(
    *,
    goal_scope_branch: str | None,
    scope_type: str,
) -> str:
    normalized = normalize_goal_scope_branch(goal_scope_branch)

    if normalized not in VALID_GOAL_SCOPE_BRANCHES:
        raise StrategicIndicatorsIndicatorGoalValidationError(
            "goal_scope_branch inválido. Use vazio (consolidado), 01 ou 02."
        )

    if normalized and not indicator_allows_branch_goals(scope_type):
        raise StrategicIndicatorsIndicatorGoalValidationError(
            "goal_scope_branch inválido para este indicador. "
            "Use vazio (consolidado), 01 ou 02 conforme o escopo da meta."
        )

    return normalized
