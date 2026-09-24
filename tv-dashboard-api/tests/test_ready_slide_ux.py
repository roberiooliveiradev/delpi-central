"""Ready Slide UX — ondas A–D (directives, params, Delpi, quality, projection)."""

from __future__ import annotations

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.join_plan_service import JoinPlanService
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.ready_slide_quality_service import (
    ReadySlideQualityService,
)
from tv_app.application.services.data.visual_projection_service import (
    VisualProjectionService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()
    clear_presentation_ops_content_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()
    clear_presentation_ops_content_cache()


def test_e1_playlist_clarification_and_anti_patterns():
    d = VistaAgentIntelligenceService.agent_directives()
    rules = " ".join(d["object_resolution"]["rules"])
    assert "PLAYLIST_CLARIFICATION" in rules
    assert ">1" in rules or "mais de" in rules.lower() or ">1" in rules
    anti = " ".join(str(x) for x in d["anti_patterns"])
    assert "silenciosamente" in anti.lower() or "playlist" in anti.lower()
    assert d["compound_slide"]["principle"] == "READY_COMPOUND_SLIDE"
    assert "params {}" in " ".join(d["compound_slide"]["forbidden"]).lower() or "params" in anti.lower()


def test_e4d_e4e_referent_and_curation():
    d = VistaAgentIntelligenceService.agent_directives()
    assert d["playlist_curation"]["principle"] == "READ_BEFORE_CURATE"
    assert "PLAYLIST_CURATION" in d["modes"]
    rules = " ".join(d["object_resolution"]["rules"])
    assert "o gráfico" in rules.lower() or "gráfico" in rules.lower()
    assert "ele" in rules.lower()


def test_e5_branch_si_directives():
    d = VistaAgentIntelligenceService.agent_directives()
    assert d["branch_scope"]["principle"] == "INHERIT_THEN_ASK"
    assert d["si_goals"]["principle"] == "CONTRACT_SI_GOAL"
    assert d["write_quality"]["principle"] == "NO_FALSE_VERIFIED"


def test_e6_media_and_mcp_target():
    d = VistaAgentIntelligenceService.agent_directives()
    assert d["media_limits"]["principle"] == "ASSET_ID_ONLY"
    assert d["media_limits"].get("uploadCapability") == "TARGET"
    assert d["media_limits"].get("brandLogoCapability") == "PROVEN"
    assert d["brand_logo"]["principle"] == "ENSURE_OR_THEME_SKIP"
    assert d["mcp_delia"]["status"] == "TARGET"
    parity = d["screenshot_parity"]
    assert "densas" in " ".join(parity["pipeline"]).lower() or "camadas" in " ".join(
        parity["pipeline"]
    ).lower()


def test_e2_enrich_date_range_preset():
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {
            "start_date": {"optional": True},
            "end_date": {"optional": True},
            "dateRangePreset": {"optional": True},
        },
    }
    enriched = ReadySlideQualityService.enrich_data_source_params(
        route, {}, playlist_defaults={"branch": "01"}
    )
    assert enriched.get("dateRangePreset") == "this_month"
    assert enriched.get("branch") == "01"
    ReadySlideQualityService.assert_data_source_params_ready(route, enriched)


def test_e2_assert_inherits_period_from_playlist_defaults():
    """Layering: playlist already has preset → source params {} still ready."""
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {
            "start_date": {"optional": True, "label": "Data início"},
            "end_date": {"optional": True, "label": "Data fim"},
            "dateRangePreset": {"optional": True, "label": "Período"},
        },
    }
    enriched = ReadySlideQualityService.enrich_data_source_params(
        route,
        {},
        playlist_defaults={"dateRangePreset": "this_week", "branch": "01"},
    )
    # Do not duplicate period onto the source when playlist owns it.
    assert "dateRangePreset" not in enriched
    ReadySlideQualityService.assert_data_source_params_ready(
        route,
        enriched,
        playlist_defaults={"dateRangePreset": "this_week", "branch": "01"},
    )


def test_e2_assert_inherits_period_from_slide_filters():
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {
            "start_date": {"optional": True},
            "end_date": {"optional": True},
            "dateRangePreset": {"optional": True},
        },
    }
    ReadySlideQualityService.assert_data_source_params_ready(
        route,
        {},
        slide_filters={"dateRangePreset": "this_month"},
    )


def test_e2_negative_empty_params_still_fails_without_enrich():
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {
            "start_date": {"optional": True, "label": "Data início"},
            "end_date": {"optional": True, "label": "Data fim"},
            "dateRangePreset": {"optional": True, "label": "Período"},
        },
    }
    try:
        ReadySlideQualityService.assert_data_source_params_ready(route, {})
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_e2_negative_empty_layers_still_fail():
    route = {
        "paramStrategy": "date_range",
        "openEndedDateRange": False,
        "paramSchema": {
            "start_date": {"optional": True},
            "end_date": {"optional": True},
            "dateRangePreset": {"optional": True},
        },
    }
    try:
        ReadySlideQualityService.assert_data_source_params_ready(
            route,
            {},
            playlist_defaults={"branch": "01"},
            slide_filters={},
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_e3_delpi_defaults_and_recipes():
    kpi = PresentationOpsContentService.block_defaults("kpi_view")
    assert kpi["frame"]["w"] <= 45
    assert "#0d2840" in str(kpi.get("style") or {}) or "#0d2840" in str(
        kpi.get("kpiParts") or {}
    )
    catalog = PresentationRecipeService.catalog_projection()
    assert "TV_KPI_SERIES_TABLE" in catalog["recipes"]
    assert "TV_KPI_HERO" in catalog["recipes"]
    ops = PresentationRecipeService.ops_for_recipe("TV_KPI_HERO")
    assert any(op.get("op") == "patch_native_config" for op in ops)
    kpi_blocks = [
        op["block"]
        for op in ops
        if op.get("op") == "upsert_block" and isinstance(op.get("block"), dict)
        and op["block"].get("type") == "kpi_view"
    ]
    assert kpi_blocks
    assert kpi_blocks[0]["frame"]["w"] <= 45


def test_e4_auto_projection_from_value_fields():
    route = {
        "valueFields": ["ppm", "value"],
        "valueFieldTypes": {"ppm": "number", "value": "number"},
    }
    kpi = VisualProjectionService.kpi_projection(route)
    assert kpi.get("metrics")
    assert kpi["metrics"][0]["field"] in {"ppm", "value"}
    chart = VisualProjectionService.chart_projection(
        {"valueFields": ["period", "value"], "valueFieldTypes": {"value": "number"}}
    )
    assert chart.get("yField") == "value"
    table = VisualProjectionService.table_projection(route)
    assert table.get("columns")


def test_e4_quality_empty_projection_detected():
    native = {
        "blocks": [
            {
                "id": "v1",
                "type": "kpi_view",
                "dataSourceId": "ds1",
                "kpiProjection": {},
            }
        ]
    }
    issues = ReadySlideQualityService.collect_native_quality_issues(native)
    assert any("projection.empty" in i for i in issues)


def test_e4_quality_resolved_error_detected():
    native = {
        "blocks": [
            {"id": "ds1", "type": "data_source", "resolved": {"error": "Informe o período"}}
        ]
    }
    issues = ReadySlideQualityService.collect_native_quality_issues(native)
    assert any("resolved.error" in i for i in issues)


def test_e5_join_hints_service():
    proposal = JoinPlanService.propose(
        left_columns=["branch", "ppm"],
        right_columns=["branch", "name"],
    )
    assert proposal is not None and proposal.is_usable
    assert proposal.left_key == "branch"
    step = JoinPlanService.merge_step_from_join_hints(
        {"proposal": proposal.to_dict()},
        source_id="src-b",
    )
    assert step is not None
    assert step["op"] == "merge"
    assert step["leftKey"] == "branch"
    assert step["sourceId"] == "src-b"
    assert (
        JoinPlanService.merge_step_from_join_hints({"proposal": {"confidence": 0.1}}, source_id="x")
        is None
    )


def test_e6_eval_corpus_markers_documented_in_directives():
    """Corpus R-style: casos cobertos por directives/recipes (smoke de rastreio)."""
    d = VistaAgentIntelligenceService.agent_directives()
    compound = " ".join(d["compound_slide"]["pipeline"])
    assert "dateRangePreset" in compound or "this_month" in compound
    recipes = d["presentation_recipes"]["catalog"]["recipes"]
    assert "TV_KPI_SERIES_TABLE" in recipes
    assert "TV_KPI_PLUS_CHART" in recipes
