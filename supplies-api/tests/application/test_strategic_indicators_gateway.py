from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.gateways.strategic_indicators_gateway import (
    SI_INDICATOR_BY_KPI,
    StrategicIndicatorsGateway,
    _pick_comparable_goal,
)


def test_metrics_by_kpi_preserves_goal_triad_partial_month():
    """Partial period: comparable (goals map) must differ from cadastral goal_value."""
    delpi = MagicMock()
    delpi.get.return_value = {
        "item": {
            "indicators": [
                {
                    "indicator_id": "supplies-otd",
                    "goal_value": 98.0,
                    "goals": {"01": 25.5, "02": 25.5, "consolidated": 30.0},
                    "score": 6.57,
                    "performance_direction": "higher_is_better",
                    "goal_mode": "standard",
                },
            ]
        }
    }
    gateway = StrategicIndicatorsGateway(delpi=delpi)

    consolidated = gateway.metrics_by_kpi(
        access_token="t",
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-08",
    )["KPI-OTD"]
    assert consolidated["goal_value"] == 98.0
    assert consolidated["comparable_goal"] == 30.0
    assert consolidated["reference_goal"] == 98.0
    assert consolidated["comparable_goal"] != consolidated["reference_goal"]
    assert consolidated["score"] == 6.57
    assert consolidated["performance_direction"] == "higher_is_better"

    single = gateway.metrics_by_kpi(
        access_token="t",
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )["KPI-OTD"]
    assert single["comparable_goal"] == 25.5
    assert single["goal_value"] == 98.0
    assert gateway.goals_by_kpi(
        access_token="t",
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )["KPI-OTD"] == 98.0
    assert set(gateway.metrics_by_kpi(
        access_token="t",
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-08",
    )) == set(SI_INDICATOR_BY_KPI)


def test_pick_comparable_goal_branch_and_consolidated():
    goals = {"01": 10.0, "02": 20.0, "consolidated": 15.0}
    assert _pick_comparable_goal(goals, branch="01") == 10.0
    assert _pick_comparable_goal(goals, branch=None) == 15.0
    assert _pick_comparable_goal({}, branch="01") is None


def test_metrics_by_kpi_prefers_si_top_level_triad_for_stock():
    delpi = MagicMock()
    delpi.get.return_value = {
        "item": {
            "indicators": [
                {
                    "indicator_id": "supplies-stock-value",
                    "goal_value": 13_500_000.0,
                    "comparable_goal": 13_500_000.0,
                    "reference_goal": 13_500_000.0,
                    "goals": {"01": 2_500_000.0, "02": 11_000_000.0, "consolidated": 13_500_000.0},
                    "score": 3.04,
                    "performance_direction": "lower_is_better",
                    "goal_mode": "standard",
                },
            ]
        }
    }
    row = StrategicIndicatorsGateway(delpi=delpi).metrics_by_kpi(
        access_token="t",
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-10",
    )["KPI-STOCK-VALUE"]
    assert row["goal_value"] == 13_500_000.0
    assert row["comparable_goal"] == 13_500_000.0
    assert row["reference_goal"] == 13_500_000.0
    assert row["comparable_goal"] == row["reference_goal"]
    assert row["performance_direction"] == "lower_is_better"


def test_metrics_by_kpi_closed_month_comparable_may_equal_reference():
    delpi = MagicMock()
    delpi.get.return_value = {
        "item": {
            "indicators": [
                {
                    "indicator_id": "supplies-cpv",
                    "goal_value": 40.0,
                    "goals": {"consolidated": 40.0},
                    "score": 7.0,
                    "performance_direction": "lower_is_better",
                    "goal_mode": "standard",
                },
            ]
        }
    }
    row = StrategicIndicatorsGateway(delpi=delpi).metrics_by_kpi(
        access_token="t",
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-31",
    )["KPI-CPV"]
    assert row["goal_value"] == 40.0
    assert row["comparable_goal"] == 40.0
    assert row["reference_goal"] == 40.0
    assert row["performance_direction"] == "lower_is_better"
