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
    """Informed blocks skip default fill; disproportionate title/icon still rebalance."""
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
                    "title": {"style": {"fontSize": 16}},
                    "icon": {"style": {"iconSize": 28}},
                },
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg2, informed_block_ids={"k2"}) is True
    parts = cfg2["blocks"][0]["kpiParts"]
    assert parts["title"]["style"]["fontSize"] >= 31  # ~90 * 0.35
    assert parts["icon"]["style"]["iconSize"] >= 49  # ~90 * 0.55


def test_part_chrome_rebalances_kpi_when_value_dwarfs_title_icon():
    cfg = {
        "version": 5,
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 18, "w": 30, "h": 36},
                "kpiParts": {
                    "value": {"style": {"fontSize": 80}},
                    "title": {"style": {"fontSize": 18}},
                    "icon": {"style": {"iconSize": 32}},
                },
            }
        ],
    }
    assert SlidePartChromeService.apply_missing_defaults(cfg) is True
    parts = cfg["blocks"][0]["kpiParts"]
    assert parts["title"]["style"]["fontSize"] >= 28
    assert parts["icon"]["style"]["iconSize"] >= 44


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
