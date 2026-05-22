from __future__ import annotations

from unittest.mock import patch

from app.application.services.strategic_indicators.dashboard_goals_service import (
    DashboardGoalsService,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import (
    enrich_dashboard_metric,
)


def _sample_goal() -> dict:
    return {
        "source_key": "supplies_otd",
        "goal_label": "≥ 95%",
        "comparable_goal": 95.0,
        "has_goal": True,
        "goal_scope_branch": "",
        "scope_type": "consolidated",
        "performance_direction": "higher_is_better",
    }


def test_enrich_dashboard_metric_attaches_goal_at_root() -> None:
    service = DashboardGoalsService()
    with (
        patch.object(service, "get_goal", return_value=_sample_goal()),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            {"otd_percentage": 88.0},
            source_key="supplies_otd",
        )

    assert result["goal_label"] == "≥ 95%"
    assert result["comparable_goal"] == 95.0
    assert result["has_goal"] is True
    assert result["goal_scope_branch"] == ""
    assert result["performance_direction"] == "higher_is_better"
    assert result["otd_percentage"] == 88.0


def test_enrich_dashboard_metric_attaches_goal_under_summary_key() -> None:
    service = DashboardGoalsService()
    with (
        patch.object(service, "get_goal", return_value=_sample_goal()),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            {"summary": {"otd_percentage": 88.0, "total_lines": 100}},
            source_key="supplies_otd",
            summary_key="summary",
        )

    assert result["summary"]["goal_label"] == "≥ 95%"
    assert result["summary"]["comparable_goal"] == 95.0
    assert result["summary"]["otd_percentage"] == 88.0


def test_enrich_dashboard_metric_attaches_goal_label_without_comparable() -> None:
    service = DashboardGoalsService()
    goal = {
        "source_key": "supplies_stock_value",
        "goal_label": "R$ 13.500.000,00",
        "comparable_goal": None,
        "has_goal": False,
    }
    with (
        patch.object(service, "get_goal", return_value=goal),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            {"summary": {"total_stock_value": 14_000_000}},
            source_key="supplies_stock_value",
            summary_key="summary",
        )

    assert result["summary"]["goal_label"] == "R$ 13.500.000,00"


def test_enrich_dashboard_metric_leaves_payload_when_goal_missing() -> None:
    service = DashboardGoalsService()
    with (
        patch.object(service, "get_goal", return_value=None),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        payload = {"summary": {"otd_percentage": 88.0}}
        result = enrich_dashboard_metric(
            payload,
            source_key="supplies_otd",
            summary_key="summary",
        )

    assert result == payload
