"""P0+P1 design intelligence: compound goals, series, audit, blueprint."""

from __future__ import annotations

import json
from pathlib import Path

from tv_app.application.services.data.compound_goal_planner import plan_compound_goals
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_command_planner_service import (
    PresentationCommandPlannerService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)
from tv_app.application.services.data.presentation_suggest_ops_service import (
    PresentationSuggestOpsService,
)
from tv_app.application.services.data.safe_auto_fix_service import SafeAutoFixService
from tv_app.application.services.data.slide_auto_layout_service import SlideAutoLayoutService
from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)
from tv_app.application.services.data.slide_part_chrome_service import SlidePartChromeService
from tv_app.application.services.data.story_digest_service import StoryDigestService
from tv_app.application.services.data.visual_verification_service import (
    VisualVerificationService,
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


def test_kpi_recipes_expose_blueprint_slots_used_by_auto_layout():
    recipes = PresentationRecipeService.document()["recipes"]
    for recipe_id in (
        "TV_KPI_HERO",
        "TV_KPI_ROW_2",
        "TV_KPI_ROW_3",
        "TV_KPI_GRID_4",
        "TV_KPI_PLUS_CHART",
        "TV_KPI_PLUS_CHART_PIE",
        "TV_KPI_SERIES_TABLE",
    ):
        slots = recipes[recipe_id]["blueprint"]["slots"]
        assert slots
    frames = SlideAutoLayoutService.recipe_kpi_frames("TV_KPI_ROW_2")
    assert frames[0]["x"] == 3
    assert frames[1]["x"] == 51


def test_design_audit_issues_are_rich_and_have_no_score():
    audit = DesignIntelligenceService.design_audit(
        {
            "version": 5,
            "blocks": [
                {"id": "a", "type": "kpi_view", "frame": {"x": 0, "y": 0, "w": 40, "h": 40}},
                {"id": "b", "type": "kpi_view", "frame": {"x": 0, "y": 0, "w": 40, "h": 40}},
            ],
        }
    )
    assert "score" not in audit
    overlap = next(item for item in audit["issues"] if item["id"].startswith("block_overlap:"))
    assert overlap["message"]
    assert overlap["blockIds"]
    assert overlap["recommendation"]
    assert overlap["safeAutoFix"] is True
    density = DesignIntelligenceService.design_audit(
        {
            "blocks": [
                {"id": f"k{i}", "type": "kpi_view", "frame": {"x": 4 + i * 18, "y": 20, "w": 16, "h": 30}}
                for i in range(5)
            ]
        }
    )
    density_issue = next(item for item in density["issues"] if item["id"].startswith("kpi_density"))
    assert density_issue["safeAutoFix"] is False
    assert density_issue["recommendedRecipe"] == "TV_KPI_GRID_4"


def test_safe_area_violation_and_negative_inside_margin():
    invaded = SlideLayoutQualityService.collect_native_layout_issues(
        {"blocks": [{"id": "edge", "type": "heading", "frame": {"x": 0, "y": 4, "w": 20, "h": 8}}]}
    )
    assert any(code.startswith("safe_area_violation:edge") for code in invaded)
    inside = SlideLayoutQualityService.collect_native_layout_issues(
        {"blocks": [{"id": "ok", "type": "heading", "frame": {"x": 4, "y": 4, "w": 40, "h": 10}, "style": {"color": "#ffffff"}}]}
    )
    assert not any(code.startswith("safe_area_violation:") for code in inside)


def test_role_resolves_chrome_from_tokens():
    cfg = {
        "blocks": [
            {
                "id": "hero",
                "type": "kpi_view",
                "role": "primaryKpi",
                "variant": "hero",
                "emphasis": "high",
                "density": "comfortable",
                "frame": {"x": 18, "y": 22, "w": 36, "h": 42},
            }
        ]
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    style = cfg["blocks"][0]["style"]
    assert style["fontSize"] > 56
    assert style["backgroundColor"] == "#ffffff"
    assert style["padding"] == 20


def test_chart_style_options_are_typed():
    spec = PresentationOpsContentService.operation_spec("upsert_block")
    props = spec["inputSchema"]["properties"]["block"]["properties"]["chartOptions"]["properties"]
    for key in ("legend", "grid", "labels", "axes", "stackMode", "sort", "topN", "density"):
        assert key in props


def test_monotony_keeps_only_compatible_alternatives():
    digest = DesignIntelligenceService.semantic_digest(
        [{"date": "2026-01-01", "conversion_rate": 0.3}],
        columns=["date", "conversion_rate"],
    )
    rec = DesignIntelligenceService.visual_recommendation(digest, dominant_visual_family="line")
    assert rec["recommendedType"] == "area"
    assert all(item["type"] != "pie" for item in rec["alternatives"])
    assert all(item["type"] != "line" for item in rec["alternatives"])
    plain = DesignIntelligenceService.visual_recommendation(digest)
    assert plain["recommendedType"] == "line"


def test_story_digest_is_compact_index():
    slides = [
        {
            "id": f"s{i}",
            "title": f"Slide {i}",
            "durationSec": 15,
            "nativeConfig": {
                "blocks": [
                    {"type": "kpi_view", "label": "OTD"},
                    {"type": "chart_view", "chartType": "line"},
                ]
            },
        }
        for i in range(8)
    ]
    story = StoryDigestService.digest(slides)
    assert story["totalDurationSec"] == 120
    assert story["slides"][0]["visualFamily"] == "kpi_line"
    assert "repetitiveLayouts" in story
    assert len(json.dumps(story)) < 8000
    assert "nativeConfig" not in json.dumps(story)


def test_safe_autofix_does_not_change_pie_or_metric():
    native = {
        "blocks": [
            {
                "id": "pie",
                "type": "chart_view",
                "chartType": "pie",
                "frame": {"x": 0, "y": 0, "w": 80, "h": 80},
                "chartProjection": {"field": "conversion_rate"},
            }
        ]
    }
    ops = SafeAutoFixService.ops_for(native)
    assert ops
    assert all(op["op"] == "upsert_block" for op in ops)
    assert all("chartType" not in op["block"] for op in ops)
    assert all("chartProjection" not in op["block"] for op in ops)
    plan = PresentationSuggestOpsService.materialize(
        message="revise o layout do slide",
        host_context={"nativeConfig": native, "playlistId": "p", "slideId": "s"},
    )
    assert plan["matchedCapabilityKeys"] == ["safe_auto_fix"]
    density_only = {
        "blocks": [
            {"id": "k0", "type": "kpi_view", "frame": {"x": 4, "y": 18, "w": 18, "h": 28}},
            {"id": "k1", "type": "kpi_view", "frame": {"x": 26, "y": 18, "w": 18, "h": 28}},
            {"id": "k2", "type": "kpi_view", "frame": {"x": 48, "y": 18, "w": 18, "h": 28}},
            {"id": "k3", "type": "kpi_view", "frame": {"x": 70, "y": 18, "w": 18, "h": 28}},
            {"id": "k4", "type": "kpi_view", "frame": {"x": 4, "y": 52, "w": 18, "h": 28}},
        ]
    }
    assert SafeAutoFixService.ops_for(density_only) == []


def test_visual_verification_requires_three_booleans():
    clean = {
        "blocks": [
            {"id": "h", "type": "heading", "frame": {"x": 4, "y": 4, "w": 40, "h": 10}, "style": {"color": "#ffffff"}}
        ]
    }
    ok = VisualVerificationService.build(persisted=True, before_native=clean, after_native=clean)
    assert VisualVerificationService.is_verified(ok) is True
    broken = {"blocks": [{"id": "edge", "type": "heading", "frame": {"x": 0, "y": 0, "w": 10, "h": 10}}]}
    bad = VisualVerificationService.build(persisted=True, before_native=clean, after_native=broken)
    assert bad["layoutGatePassed"] is False
    assert bad["issuesIntroduced"]
    assert VisualVerificationService.is_verified(bad) is False


def test_conversion_series_overlay_declares_value_fields():
    raw = json.loads(
        Path("tv_app/content/tv_data_route_overlays.json").read_text(encoding="utf-8")
    )
    fields = set(raw["overlays"]["get_sales_conversion_rate_series"]["valueFields"])
    assert "conversion_filial_01" in fields
    assert "qtd_proposals_01" in fields
