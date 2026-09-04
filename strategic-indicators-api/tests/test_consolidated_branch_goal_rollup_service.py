from __future__ import annotations

from si_app.domain.services.consolidated_branch_goal_rollup_service import (
    ConsolidatedBranchGoalRollupService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def test_rollup_sums_currency_standard_goals() -> None:
    service = ConsolidatedBranchGoalRollupService(
        reference_resolver=StrategicIndicatorsCalculator(),
    )
    result = service.rollup_branch_goals(
        indicator={
            "value_unit": "currency",
            "branch_value_aggregation": "sum",
        },
        branch_goals_by_code={
            "01": {
                "goal_label": "R$ 100.000,00",
                "goal_value": 100_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_label": "R$ 80.000,00",
                "goal_value": 80_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        start_date="01-04-2026",
        end_date="30-04-2026",
        competence="2026-04",
    )

    assert result is not None
    assert result["goal_value"] == 180_000.0
    assert result["goal_mode"] == "standard"
    assert result["aggregated_from_branches"] is True


def test_rollup_averages_percent_goals() -> None:
    service = ConsolidatedBranchGoalRollupService(
        reference_resolver=StrategicIndicatorsCalculator(),
    )
    result = service.rollup_branch_goals(
        indicator={
            "value_unit": "percent",
            "branch_value_aggregation": "auto",
        },
        branch_goals_by_code={
            "01": {
                "goal_value": 50.5,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_value": 50.5,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        start_date="01-04-2026",
        end_date="30-04-2026",
        competence="2026-04",
    )

    assert result is not None
    assert result["goal_value"] == 50.5


def test_rollup_monthly_curve_aggregates_reference_as_standard() -> None:
    service = ConsolidatedBranchGoalRollupService(
        reference_resolver=StrategicIndicatorsCalculator(),
    )
    result = service.rollup_branch_goals(
        indicator={
            "value_unit": "currency",
            "branch_value_aggregation": "sum",
        },
        branch_goals_by_code={
            "01": {
                "goal_value": 0.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 9, "target_value": 1_160_000.0}],
            },
            "02": {
                "goal_value": 0.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 9, "target_value": 3_614_000.0}],
            },
        },
        start_date="01-09-2026",
        end_date="04-09-2026",
        competence="2026-09",
    )

    assert result is not None
    assert result["goal_value"] == 4_774_000.0
    assert result["goal_mode"] == "standard"
    assert result["monthly_targets"] == []


def test_rollup_returns_none_when_only_one_branch() -> None:
    service = ConsolidatedBranchGoalRollupService(
        reference_resolver=StrategicIndicatorsCalculator(),
    )
    result = service.rollup_branch_goals(
        indicator={"value_unit": "currency", "branch_value_aggregation": "sum"},
        branch_goals_by_code={
            "01": {
                "goal_value": 100_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        start_date="01-04-2026",
        end_date="30-04-2026",
        competence="2026-04",
    )

    assert result is None
