"""SlidePartChromeService + playlist dataDefaults + Delpi white-card recipes."""

from __future__ import annotations

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)
from tv_app.application.services.data.slide_part_chrome_service import (
    SlidePartChromeService,
)
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    _sanitize_playlist_data_defaults,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()
    clear_presentation_ops_content_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()
    clear_presentation_ops_content_cache()


def test_brand_and_part_chrome_tokens():
    tokens = PresentationRecipeService.catalog_projection()["designTokens"]
    brand = tokens["brand"]
    assert brand["card"] == "#ffffff"
    assert brand["accent"] == "#089bdb"
    assert brand["modes"]["dark"]["accent"] == "#089bdb"
    assert brand["modes"]["light"]["onBg"] == "#0f172a"
    assert brand["modes"]["dark"]["navy"] == "#003866"
    assert brand["modes"]["light"]["accentWash"] == "#e8f4fc"
    assert brand["modes"]["dark"]["borderMuted"] == "#94a3b8"
    assert "partChrome" in tokens
    assert tokens["partChrome"]["kpi"]["valueMinFontSize"]["row"] >= 40
    assert "chartTypeHints" in tokens


def test_kpi_row_recipe_uses_white_card():
    ops = PresentationRecipeService.ops_for_recipe("TV_KPI_ROW_2")
    kpis = [
        op["block"]
        for op in ops
        if op.get("op") == "upsert_block" and op["block"].get("type") == "kpi_view"
    ]
    assert len(kpis) == 2
    for kpi in kpis:
        assert kpi["style"]["backgroundColor"] == "#ffffff"
        assert kpi["kpiParts"]["card"]["style"]["fill"] == "#ffffff"
        assert kpi["kpiParts"]["value"]["style"]["fontSize"] >= 48


def test_part_chrome_fills_missing_kpi_positive():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 3, "y": 16, "w": 46, "h": 50},
                "style": {},
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    kpi = cfg["blocks"][0]
    assert kpi["style"]["backgroundColor"] == "#ffffff"
    assert kpi["kpiParts"]["value"]["style"]["fontSize"] >= 48
    assert kpi["kpiParts"]["value"]["style"]["typographyMode"] == "auto"
    assert kpi["kpiParts"]["icon"]["style"]["iconSize"] >= 32


def test_part_chrome_sibling_chart_table_input():
    cfg = {
        "version": 5,
        "blocks": [
            {"id": "c1", "type": "chart_view", "frame": {"x": 0, "y": 0, "w": 50, "h": 40}},
            {"id": "t1", "type": "table_view", "frame": {"x": 50, "y": 0, "w": 50, "h": 40}},
            {
                "id": "i1",
                "type": "input",
                "frame": {"x": 0, "y": 50, "w": 40, "h": 12},
                "input": {"paramKey": "branch", "targetScope": "slide"},
            },
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    assert cfg["blocks"][0]["chartOptions"]["titleFontSize"] >= 18
    assert cfg["blocks"][1]["tableOptions"]["bodyFontSize"] >= 14
    assert cfg["blocks"][2]["inputParts"]["label"]["style"]["fontSize"] >= 14


def test_part_chrome_negative_skips_informed_fill_but_rebalances_hierarchy():
    """Informed blocks skip default fill; missing title/icon still follow the value."""
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 0, "y": 0, "w": 40, "h": 40},
                "style": {},
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg, informed_block_ids={"k1"}) is False
    assert "kpiParts" not in cfg["blocks"][0]

    cfg2 = {
        "version": 5,
        "blocks": [
            {
                "id": "k2",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 18, "w": 28, "h": 28},
                "kpiParts": {
                    "value": {"style": {"fontSize": 90}},
                    "title": {"style": {}},
                    "icon": {"style": {}},
                },
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg2, informed_block_ids={"k2"}) is True
    parts = cfg2["blocks"][0]["kpiParts"]
    assert parts["title"]["style"]["fontSize"] >= 31  # ~90 * 0.35
    assert parts["icon"]["style"]["iconSize"] >= 49  # ~90 * 0.55


def test_part_chrome_rebalances_kpi_auto_managed_parts_from_value():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 18, "w": 30, "h": 36},
                "kpiParts": {"value": {"style": {"fontSize": 80}}},
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    parts = cfg["blocks"][0]["kpiParts"]
    assert parts["title"]["style"]["fontSize"] >= 28
    assert parts["icon"]["style"]["iconSize"] >= 44


def test_part_chrome_keeps_authored_kpi_parts_above_legibility_min():
    """Authored title/icon are not raised to the value ratio; only token minimums apply."""
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 18, "w": 30, "h": 36},
                "kpiParts": {
                    "value": {"style": {"fontSize": 80}},
                    "title": {"style": {"fontSize": 20}},
                    "icon": {"style": {"iconSize": 28}},
                },
            }
        ],
    }
    SlidePartChromeService.apply_missing_defaults(cfg, informed_block_ids={"k1"})
    parts = cfg["blocks"][0]["kpiParts"]
    assert parts["title"]["style"]["fontSize"] == 20
    assert parts["icon"]["style"]["iconSize"] == 32  # partChrome.kpi.iconMinSize


def test_part_chrome_negative_balanced_kpi_unchanged():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 18, "w": 30, "h": 36},
                "style": {"backgroundColor": "#ffffff", "color": "#0f172a"},
                "kpiParts": {
                    "card": {"style": {"fill": "#ffffff", "backgroundColor": "#ffffff", "borderRadius": 16}},
                    "value": {"style": {"fontSize": 56, "color": "#0f172a", "typographyMode": "auto"}},
                    "title": {"style": {"fontSize": 22, "color": "#475569"}},
                    "icon": {"style": {"iconSize": 44, "color": "#089bdb"}},
                },
            }
        ],
    }
    before = {
        "title": cfg["blocks"][0]["kpiParts"]["title"]["style"]["fontSize"],
        "icon": cfg["blocks"][0]["kpiParts"]["icon"]["style"]["iconSize"],
        "value": cfg["blocks"][0]["kpiParts"]["value"]["style"]["fontSize"],
    }
    SlidePartChromeService.apply_missing_defaults(cfg)
    after_parts = cfg["blocks"][0]["kpiParts"]
    assert after_parts["title"]["style"]["fontSize"] == before["title"]
    assert after_parts["icon"]["style"]["iconSize"] == before["icon"]
    assert after_parts["value"]["style"]["fontSize"] == before["value"]


def _family_hierarchy_cfg(*, authored_dependents: bool) -> dict:
    """Chart/table/input/composed group whose primaries are large.

    ``authored_dependents`` decides whether the dependent sizes are already
    persisted (author intent) or absent (auto-managed by part chrome).
    """

    def dependent(value: int) -> dict:
        return {"fontSize": value} if authored_dependents else {}

    chart_opts: dict = {"titleFontSize": 32}
    if authored_dependents:
        chart_opts.update({"legendFontSize": 12, "axisFontSize": 10})
    table_opts: dict = {"bodyFontSize": 22}
    if authored_dependents:
        table_opts["headerFontSize"] = 14
    return {
        "version": 5,
        "blocks": [
            {
                "id": "c1",
                "type": "chart_view",
                "frame": {"x": 4, "y": 40, "w": 92, "h": 50},
                "chartOptions": chart_opts,
            },
            {
                "id": "t1",
                "type": "table_view",
                "frame": {"x": 4, "y": 4, "w": 90, "h": 40},
                "tableOptions": table_opts,
            },
            {
                "id": "i1",
                "type": "input",
                "frame": {"x": 4, "y": 2, "w": 40, "h": 12},
                "input": {"paramKey": "branch", "targetScope": "slide"},
                "inputParts": {
                    "control": {"style": {"fontSize": 24}},
                    "label": {"style": dependent(12)},
                },
            },
            {
                "id": "h1",
                "type": "heading",
                "groupId": "grp_x",
                "content": "Label",
                "style": dependent(14),
                "frame": {"x": 10, "y": 10, "w": 30, "h": 8},
            },
            {
                "id": "v1",
                "type": "text",
                "groupId": "grp_x",
                "content": "—",
                "dataSourceId": "src",
                "textProjection": {"field": "value", "format": "number"},
                "style": {"fontSize": 64},
                "frame": {"x": 10, "y": 20, "w": 30, "h": 20},
            },
        ],
    }


def test_part_chrome_rebalances_auto_managed_chart_table_input_and_composed_group():
    cfg = _family_hierarchy_cfg(authored_dependents=False)
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    chart_opts = cfg["blocks"][0]["chartOptions"]
    assert chart_opts["legendFontSize"] >= 22
    assert chart_opts["axisFontSize"] >= 19
    table_opts = cfg["blocks"][1]["tableOptions"]
    assert table_opts["headerFontSize"] >= table_opts["bodyFontSize"]
    assert table_opts["headerFontSize"] >= 24
    input_parts = cfg["blocks"][2]["inputParts"]
    assert input_parts["label"]["style"]["fontSize"] >= 20
    heading = cfg["blocks"][3]
    assert heading["style"]["fontSize"] >= 28  # ~64 * 0.45
    assert cfg["blocks"][4]["style"]["fontSize"] == 64


def test_part_chrome_keeps_authored_dependents_at_legibility_min_only():
    cfg = _family_hierarchy_cfg(authored_dependents=True)
    all_ids = {b["id"] for b in cfg["blocks"]}
    SlidePartChromeService.apply_missing_defaults(cfg, informed_block_ids=all_ids)
    chart_opts = cfg["blocks"][0]["chartOptions"]
    assert chart_opts["legendFontSize"] == 14  # partChrome.chart.legendMinFontSize
    assert chart_opts["axisFontSize"] == 12  # partChrome.chart.axisMinFontSize
    table_opts = cfg["blocks"][1]["tableOptions"]
    assert table_opts["headerFontSize"] == 16  # partChrome.table.headerMinFontSize
    assert table_opts["bodyFontSize"] == 22
    input_parts = cfg["blocks"][2]["inputParts"]
    assert input_parts["label"]["style"]["fontSize"] == 14  # partChrome.input.labelMinFontSize
    heading = cfg["blocks"][3]
    assert heading["style"]["fontSize"] == 16  # composed/textBound absoluteMinFontSize


def test_part_chrome_uninformed_authored_dependents_not_raised_to_primary_ratio():
    """Default fill may still rescue sub-minimum sizes, but never applies primary ratios."""
    cfg = _family_hierarchy_cfg(authored_dependents=True)
    SlidePartChromeService.apply_missing_defaults(cfg)
    chart_opts = cfg["blocks"][0]["chartOptions"]
    assert chart_opts["legendFontSize"] < 22  # ratio target ~32 * 0.7
    table_opts = cfg["blocks"][1]["tableOptions"]
    assert 16 <= table_opts["headerFontSize"] < 24  # ratio target ~22 * 1.12
    input_parts = cfg["blocks"][2]["inputParts"]
    assert 14 <= input_parts["label"]["style"]["fontSize"] < 20  # ratio target ~24 * 0.85
    assert cfg["blocks"][3]["style"]["fontSize"] < 28  # ratio target ~64 * 0.45


def test_part_chrome_composed_group_member_without_size_gets_group_default():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "p",
                "type": "text",
                "groupId": "grp_y",
                "content": "95,0%",
                "style": {"fontSize": 76},
                "frame": {"x": 6, "y": 10, "w": 40, "h": 16},
            },
            {
                "id": "v",
                "type": "text",
                "groupId": "grp_y",
                "content": "",
                "textProjection": {"field": "reference_goal", "format": "percent"},
                "style": {},
                "frame": {"x": 28, "y": 28, "w": 18, "h": 10},
            },
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    assert cfg["blocks"][1]["style"]["fontSize"] == 65  # round(76 * valueSiblingMinRatio)
    assert cfg["blocks"][0]["style"]["fontSize"] == 76

    # Materialized default is persisted state from now on: a later pass keeps it.
    cfg["blocks"][1]["style"]["fontSize"] = 63
    SlidePartChromeService.apply_missing_defaults(cfg)
    assert cfg["blocks"][1]["style"]["fontSize"] == 63


def test_part_chrome_negative_static_caption_not_forced_hero():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "cap",
                "type": "text",
                "content": "nota de rodapé",
                "style": {"fontSize": 16},
                "frame": {"x": 4, "y": 90, "w": 90, "h": 8},
            }
        ],
    }
    SlidePartChromeService.apply_missing_defaults(cfg)
    assert cfg["blocks"][0]["style"]["fontSize"] == 16


def test_layout_gate_part_font_below_min():
    cfg = {
        "version": 5,
        "background": {"type": "color", "value": "#0d2840"},
        "blocks": [
            {
                "id": "tiny",
                "type": "kpi_view",
                "frame": {"x": 3, "y": 16, "w": 46, "h": 50},
                "kpiParts": {
                    "value": {"style": {"fontSize": 10}},
                    "title": {"style": {"fontSize": 8}},
                },
            }
        ],
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert any(i.startswith("part_font_below_min:tiny:value") for i in issues)
    assert any(i.startswith("part_font_below_min:tiny:title") for i in issues)


def test_patch_playlist_data_defaults_in_ops_catalog():
    assert "patch_playlist_data_defaults" in PresentationOpsContentService.allowed_ops()
    spec = PresentationOpsContentService.operation_spec("patch_playlist_data_defaults")
    assert spec["requiresSlide"] is False
    assert "dataDefaults" in (spec.get("inputSchema") or {}).get("required", [])


def test_sanitize_playlist_defaults_positive_and_negative():
    assert _sanitize_playlist_data_defaults({"branch": "01", "periodDays": 30}) == {
        "branch": "01",
        "periodDays": 30,
    }
    try:
        _sanitize_playlist_data_defaults({"nested": {"a": 1}})
        assert False, "expected PresentationWriteError"
    except PresentationWriteError as exc:
        assert "escalar" in str(exc).lower()


def test_filter_strip_and_chart_bar_recipes():
    assert PresentationRecipeService.get("TV_FILTER_STRIP")
    assert PresentationRecipeService.resolve_from_nl("faixa de filtros do slide")
    bar = PresentationRecipeService.ops_for_recipe("TV_KPI_PLUS_CHART_BAR")
    chart = next(
        op["block"]
        for op in bar
        if op.get("op") == "upsert_block" and op["block"].get("type") == "chart_view"
    )
    assert chart.get("chartType") == "bar"
    pie = PresentationRecipeService.ops_for_recipe("TV_KPI_PLUS_CHART_PIE")
    chart_pie = next(
        op["block"]
        for op in pie
        if op.get("op") == "upsert_block" and op["block"].get("type") == "chart_view"
    )
    assert chart_pie.get("chartType") == "pie"


def test_slide_design_directives_mention_filters_and_charts():
    d = VistaAgentIntelligenceService.agent_directives()
    rules = " ".join(d["slide_design"]["rules"])
    assert "patch_playlist_data_defaults" in rules
    assert "chartType" in rules or "bar" in rules.lower()
    assert "brand.card" in rules or "brancos" in rules.lower()
