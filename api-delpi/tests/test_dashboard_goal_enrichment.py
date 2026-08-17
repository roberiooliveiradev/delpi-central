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
        "goal_value": 95.0,
        "comparable_goal": 95.0,
        "reference_goal": 95.0,
        "goal_mode": "standard",
        "has_goal": True,
        "goal_aggregation": "average",
        "goal_period_kind": "exact",
        "goal_period_partial": False,
        "goal_scope_branch": "",
        "goal_scope_label": "Meta consolidada",
        "goal_scope_hint": None,
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
            start_date="2026-08-01",
            end_date="2026-08-17",
        )

    assert result["goal_label"] == "≥ 95%"
    assert result["comparable_goal"] == 95.0
    assert result["goal_value"] == 95.0
    assert result["reference_goal"] == 95.0
    assert result["has_goal"] is True
    assert result["goal_aggregation"] == "average"
    assert result["goal_period_kind"] == "exact"
    assert result["goal_period_partial"] is False
    assert result["goal_scope_branch"] == ""
    assert result["goal_scope_label"] == "Meta consolidada"
    assert result["performance_direction"] == "higher_is_better"
    assert result["otd_percentage"] == 88.0
    assert result["start_date"] == "2026-08-01"
    assert result["end_date"] == "2026-08-17"


def test_enrich_dashboard_metric_preserves_partial_kind_under_summary() -> None:
    service = DashboardGoalsService()
    goal = {
        **_sample_goal(),
        "comparable_goal": 5.0,
        "goal_aggregation": "sum",
        "goal_period_kind": "partial",
        "goal_period_partial": True,
    }
    with (
        patch.object(service, "get_goal", return_value=goal),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            {"ideas_goal": {"total_kaizens": 3}},
            source_key="quality_kaizen_ideas",
            summary_key="ideas_goal",
        )

    assert result["ideas_goal"]["goal_period_kind"] == "partial"
    assert result["ideas_goal"]["goal_period_partial"] is True
    assert result["ideas_goal"]["goal_aggregation"] == "sum"
    assert result["ideas_goal"]["comparable_goal"] == 5.0
    assert result["ideas_goal"]["total_kaizens"] == 3


def test_si_goal_field_labels_include_period_kind() -> None:
    from app.interface.http.kpi_field_labels import SI_GOAL_FIELD_LABELS, kpi_fields

    assert "goal_period_kind" in SI_GOAL_FIELD_LABELS
    assert "goal_period_partial" in SI_GOAL_FIELD_LABELS
    assert "goal_aggregation" in SI_GOAL_FIELD_LABELS
    merged = kpi_fields({"otd_percentage": "OTD"})
    assert merged["goal_period_kind"] == SI_GOAL_FIELD_LABELS["goal_period_kind"]


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


def test_enrich_dashboard_metric_attaches_scope_hint_without_goal() -> None:
    service = DashboardGoalsService()
    goal = {
        "source_key": "supplies_cpv",
        "goal_label": None,
        "comparable_goal": None,
        "has_goal": False,
        "goal_scope_hint": (
            "Metas cadastradas apenas por filial (01 e 02). "
            "Selecione uma filial no filtro."
        ),
    }
    with (
        patch.object(service, "get_goal", return_value=goal),
        patch(
            "app.application.services.strategic_indicators.dashboard_goals_service.get_dashboard_goals_service",
            return_value=service,
        ),
    ):
        result = enrich_dashboard_metric(
            {"summary": {"cpv_percentage": 42.0}},
            source_key="supplies_cpv",
            summary_key="summary",
        )

    assert result["summary"]["goal_scope_hint"] is not None
    assert "filial" in result["summary"]["goal_scope_hint"].lower()


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
