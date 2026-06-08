from __future__ import annotations

from datetime import date

from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)
from si_app.shared.goal_scope import uses_strict_branch_goal_resolution


def test_resolved_goals_params_place_branch_after_validity_dates() -> None:
    """ORDER BY CASE usa %s depois de valid_from/valid_to no SQL."""
    params: list = [2026]
    PostgresStrategicIndicatorsIndicatorGoalsRepository._resolved_goal_scope_filter(
        scope_branch="01",
        params=params,
    )
    _, scope_order_params = (
        PostgresStrategicIndicatorsIndicatorGoalsRepository._resolved_goal_scope_order(
            scope_branch="01",
        )
    )
    reference = date(2026, 4, 30)
    PostgresStrategicIndicatorsIndicatorGoalsRepository._append_goal_validity_filter(
        "WHERE 1=1",
        reference_date=reference,
        params=params,
    )
    params.extend(scope_order_params)

    if uses_strict_branch_goal_resolution("01"):
        assert params == [2026, "01", reference, reference]
    else:
        assert params == [2026, "01", reference, reference, "01"]
