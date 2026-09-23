"""Slide layout quality + auto-layout + designer recipes."""

from __future__ import annotations

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.slide_auto_layout_service import SlideAutoLayoutService
from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)
from tv_app.application.services.presentation_change_notifier import (
    LIBRARY_REASONS,
    resolve_library_recipient_user_ids,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def test_design_tokens_projected():
    cat = PresentationRecipeService.catalog_projection()
    tokens = cat.get("designTokens") or {}
    assert tokens.get("maxPrimarySignalsPerSlide") == 4
    assert "typeScale" in tokens
    assert tokens.get("brand", {}).get("card") == "#ffffff"
    assert "partChrome" in tokens
    assert "TV_KPI_ROW_2" in cat["recipes"]
    assert "TV_KPI_GRID_4" in cat["recipes"]
    assert "TV_HERO_PLUS_TABLE" in cat["recipes"]
    assert "TV_FILTER_STRIP" in cat["recipes"]


def test_row_recipes_no_overlap():
    for recipe_id in ("TV_KPI_ROW_2", "TV_KPI_ROW_3", "TV_KPI_GRID_4"):
        frames = SlideAutoLayoutService.recipe_kpi_frames(recipe_id)
        assert len(frames) >= 2
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                a, b = frames[i], frames[j]
                ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
                bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
                ix1, iy1 = max(a["x"], b["x"]), max(a["y"], b["y"])
                ix2, iy2 = min(ax2, bx2), min(ay2, by2)
                assert ix2 <= ix1 or iy2 <= iy1, recipe_id


def test_layout_overlap_detected():
    cfg = {
        "background": {"type": "color", "value": "#05070a"},
        "blocks": [
            {
                "id": "a",
                "type": "kpi_view",
                "frame": {"x": 10, "y": 10, "w": 40, "h": 40},
                "style": {"color": "#ffffff"},
            },
            {
                "id": "b",
                "type": "kpi_view",
                "frame": {"x": 20, "y": 20, "w": 40, "h": 40},
                "style": {"color": "#ffffff"},
            },
        ],
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert any(i.startswith("block_overlap:") for i in issues)


def test_layout_kpi_density():
    blocks = [
        {
            "id": f"k{i}",
            "type": "kpi_view",
            "frame": {"x": i * 10, "y": 10, "w": 8, "h": 20},
        }
        for i in range(5)
    ]
    issues = SlideLayoutQualityService.collect_native_layout_issues({"blocks": blocks})
    assert any(i.startswith("kpi_density_exceeded:") for i in issues)


def test_layout_negative_clean_row():
    frames = SlideAutoLayoutService.recipe_kpi_frames("TV_KPI_ROW_2")
    cfg = {
        "background": {"type": "gradient", "from": "#05070a", "to": "#0d2840"},
        "blocks": [
            {
                "id": "h",
                "type": "heading",
                "frame": {"x": 3, "y": 3, "w": 94, "h": 8},
                "style": {"color": "#ffffff"},
            },
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": frames[0],
                "style": {"color": "#ffffff"},
            },
            {
                "id": "k2",
                "type": "kpi_view",
                "frame": frames[1],
                "style": {"color": "#ffffff"},
            },
        ],
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert not any(i.startswith("block_overlap:") for i in issues)
    assert not any(i.startswith("kpi_density") for i in issues)


def test_auto_layout_redistributes_colliding_defaults():
    cfg = {
        "blocks": [
            {"id": "k1", "type": "kpi_view", "frame": {"x": 18, "y": 22, "w": 36, "h": 42}},
            {"id": "k2", "type": "kpi_view", "frame": {"x": 18, "y": 22, "w": 36, "h": 42}},
        ]
    }
    assert SlideAutoLayoutService.apply_kpi_row_if_needed(cfg) is True
    f1 = cfg["blocks"][0]["frame"]
    f2 = cfg["blocks"][1]["frame"]
    assert (f1["x"], f1["y"]) != (f2["x"], f2["y"])


def test_auto_layout_respects_informed():
    cfg = {
        "blocks": [
            {"id": "k1", "type": "kpi_view", "frame": {"x": 18, "y": 22, "w": 36, "h": 42}},
            {"id": "k2", "type": "kpi_view", "frame": {"x": 18, "y": 22, "w": 36, "h": 42}},
        ]
    }
    assert (
        SlideAutoLayoutService.apply_kpi_row_if_needed(
            cfg, informed_block_ids={"k1", "k2"}
        )
        is False
    )


def test_hierarchy_inverted_kpi_title_ge_value():
    cfg = {
        "blocks": [
            {
                "id": "k1",
                "type": "kpi_view",
                "frame": {"x": 10, "y": 10, "w": 30, "h": 30},
                "kpiParts": {
                    "title": {"style": {"fontSize": 48}},
                    "value": {"style": {"fontSize": 40}},
                },
            }
        ]
    }
    issues = SlideLayoutQualityService.collect_native_layout_issues(cfg)
    assert any(i.startswith("hierarchy_inverted:") for i in issues)


def test_post_create_layout_chart_table_from_recipe():
    cfg = {
        "blocks": [
            {
                "id": "c1",
                "type": "chart_view",
                "frame": {"x": 18, "y": 22, "w": 36, "h": 42},
            },
            {
                "id": "t1",
                "type": "table_view",
                "frame": {"x": 18, "y": 22, "w": 36, "h": 42},
            },
        ]
    }
    assert SlideAutoLayoutService.apply_post_create_layout(cfg) is True
    assert cfg["blocks"][0]["frame"] != cfg["blocks"][1]["frame"]


def test_directives_designer_and_focus():
    d = VistaAgentIntelligenceService.agent_directives()
    assert d["version"] == VistaAgentIntelligenceService.version()
    assert d["editor_focus"]["principle"] == "PREFER_LIVE_EDITOR_FOCUS"
    assert d["slide_design"]["principle"] == "TYPED_LAYOUT_BEFORE_FREEFORM"
    assert "DESIGN_REFINE" in d["modes"]
    assert "TV_KPI_ROW_2" in d["presentation_recipes"]["catalog"]["recipes"]
    assert "EDITOR_FOCUS" in " ".join(d["object_resolution"]["rules"])


def test_library_recipients():
    users = resolve_library_recipient_user_ids(
        {"ownerUserId": "owner", "id": "p1"},
        shares=[{"targetUserId": "share1"}],
        extra_user_ids=["owner", "extra"],
    )
    assert users == ["owner", "share1", "extra"]
    assert "created" in LIBRARY_REASONS
