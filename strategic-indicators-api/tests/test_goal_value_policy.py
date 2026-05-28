from __future__ import annotations

from si_app.application.services.strategic_indicators.goal_value_policy import (
    resolve_persisted_goal_value,
)


def test_monthly_curve_persists_zero_goal_value() -> None:
    assert (
        resolve_persisted_goal_value(
            goal_mode="monthly_curve",
            goal_value=174.24,
        )
        == 0.0
    )


def test_standard_goal_value_unchanged() -> None:
    assert (
        resolve_persisted_goal_value(
            goal_mode="standard",
            goal_value=10.5,
        )
        == 10.5
    )
