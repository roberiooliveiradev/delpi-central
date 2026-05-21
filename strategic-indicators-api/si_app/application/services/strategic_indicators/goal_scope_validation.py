from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.create_indicator_goal_use_case import (
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
            "Indicadores por unidade (per_unit) usam apenas meta consolidada; "
            "goal_scope_branch deve ser vazio. Para metas por filial, use indicadores consolidated "
            "ou indicadores separados por unidade (ex.: ROL Matriz / ROL Filial)."
        )

    return normalized
