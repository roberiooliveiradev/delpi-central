from __future__ import annotations

import pytest

from si_app.application.services.strategic_indicators.goal_curve_validation import (
    validate_curve_targets,
)
from si_app.application.services.strategic_indicators.goal_value_policy import (
    calendar_month_to_curve_point,
    curve_point_indices_for_calendar_months,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def _targets(count: int, value: float = 1.0) -> list[dict]:
    return [
        {"month_number": index, "target_value": value}
        for index in range(1, count + 1)
    ]


def test_validate_curve_targets_quarterly() -> None:
    validate_curve_targets(_targets(4), "quarterly")


def test_validate_curve_targets_rejects_wrong_count() -> None:
    with pytest.raises(ValueError):
        validate_curve_targets(_targets(12), "quarterly")


def test_quarterly_curve_point_for_may() -> None:
    assert calendar_month_to_curve_point("quarterly", 5, year=2026) == 2


def test_calculator_uses_quarterly_curve_point() -> None:
    calculator = StrategicIndicatorsCalculator()
    targets = _targets(4, value=10.0)
    comparable = calculator.calculate_comparable_goal(
        goal_value=0,
        goal_periodicity="quarterly",
        goal_mode="monthly_curve",
        monthly_targets=targets,
        competence="2026-05",
    )
    assert comparable == 10.0


def test_curve_indices_for_multiple_months() -> None:
    indices = curve_point_indices_for_calendar_months(
        "quarterly",
        [1, 2, 3, 4, 5],
        year=2026,
    )
    assert indices == [1, 2]
