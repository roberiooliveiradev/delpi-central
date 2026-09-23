"""P0+P1 design intelligence: compound goals, series, audit, blueprint."""

from __future__ import annotations

from tv_app.application.services.data.compound_goal_planner import plan_compound_goals
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_command_planner_service import (
    PresentationCommandPlannerService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)
from tv_app.application.services.series_points_extractor import chart_series_from_rows


def test_compound_period_and_pause_keeps_every_goal():
    message = (
        "centralizar periodDays=7, remover a duplicidade dos filtros "
        "e desativar os dois slides vazios"
    )
    planned = plan_compound_goals(message)
    assert planned is not None
    ops = [item["op"] for item in planned["ops"]]
    assert ops.count("patch_playlist_data_defaults") == 1
    assert ops.count("re_layer_playlist_filters") == 1
    assert ops.count("update_slide") == 2
    assert "delete_slide" not in ops
    assert len(planned["interpretedGoals"]) == 4
    assert planned["ignoredGoals"] == []


def test_delete_slide_alone_is_not_compound():
    assert plan_compound_goals("apague o slide Personalizado 4") is None


def test_planner_ready_exposes_goal_ledger():
    plan = PresentationCommandPlannerService.plan(
        message="centralizar periodDays=7 e desativar dois slides vazios",
        host_context={"playlistId": "11111111-1111-1111-1111-111111111111", "slideId": "22222222-2222-2222-2222-222222222222"},
    )
    assert plan["status"] == "ready"
    payload = PresentationCommandPlannerService.to_suggest_payload(plan)
    assert any(op.get("op") == "re_layer_playlist_filters" for op in payload["ops"])
    assert payload["interpretedGoals"]


def test_wide_conversion_series_are_not_collapsed():
    rows = [
        {
            "periodo": "2026-01",
            "conversion_filial_01": 0.2,
            "conversion_filial_02": 0.4,
            "qtd_proposals_01": 10,
            "qtd_won_01": 2,
        }
    ]
    chart = chart_series_from_rows(rows)
    assert chart is not None
    fields = {item["field"] for item in chart["series"]}
    assert "conversion_filial_01" in fields
    assert "conversion_filial_02" in fields
    assert all(item["points"][0]["value"] is not None for item in chart["series"])


def test_single_metric_row_does_not_invent_series():
    assert chart_series_from_rows([{"periodo": "2026-01", "value": 1}]) is None


def test_semantic_temporal_rejects_pie():
    digest = DesignIntelligenceService.semantic_digest(
        [{"date": "2026-01-01", "conversion_rate": 0.3}],
        columns=["date", "conversion_rate"],
    )
    rec = DesignIntelligenceService.visual_recommendation(digest)
    assert rec["recommendedType"] == "line"
    assert any(item["type"] == "pie" for item in rec["rejected"])


def test_high_cardinality_prefers_horizontal_bar():
    rows = [{"branch": f"b{i}", "revenue": i} for i in range(6)]
    digest = DesignIntelligenceService.semantic_digest(rows, columns=["branch", "revenue"])
    rec = DesignIntelligenceService.visual_recommendation(digest)
    assert rec["recommendedType"] == "horizontal_bar"


def test_design_audit_has_no_score_and_catalog_has_specs():
    audit = DesignIntelligenceService.design_audit(
        {
            "version": 5,
            "blocks": [
                {"id": "a", "type": "kpi_view", "frame": {"x": 0, "y": 0, "w": 10, "h": 10}},
            ],
        }
    )
    assert "score" not in audit
    assert "issues" in audit
    specs = DesignIntelligenceService.catalog_projection()["componentSpecs"]
    assert "kpi_view" in specs
    assert "chart_view" in specs


def test_bar_recipe_exposes_blueprint_slots():
    recipes = PresentationRecipeService.catalog_projection()["recipes"]
    blueprint = recipes["TV_KPI_PLUS_CHART_BAR"]["blueprint"]
    slot_ids = {slot["id"] for slot in blueprint["slots"]}
    assert {"title", "primaryMetric", "mainVisualization"} <= slot_ids
    tokens = PresentationRecipeService.document()["designTokens"]
    assert "space.1" in tokens["spacing"]
    assert tokens["typography"]["kpiHero"]["minTvSize"] == 64
