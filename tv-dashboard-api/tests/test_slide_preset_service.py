import pytest

from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    clear_slide_preset_caches,
    export_preset_mdd,
    list_slide_presets,
    resolve_preset_slide,
)
from tv_app.application.services.slide_template_mdd_service import (
    build_slide_template_mdd,
    parse_slide_template_mdd,
)


@pytest.fixture(autouse=True)
def _clear_caches():
    clear_slide_preset_caches()
    yield
    clear_slide_preset_caches()


def test_list_slide_presets_not_empty():
    items = list_slide_presets()
    assert len(items) >= 5
    assert all(item.get("key") for item in items)


def test_resolve_native_preset():
    payload = resolve_preset_slide("preset_production_oee")
    assert payload["slideType"] == "native"
    assert payload["nativeScreenKey"] == "production_oee_overview"


def test_resolve_unknown_preset():
    with pytest.raises(SlidePresetNotFoundError):
        resolve_preset_slide("does-not-exist")


def test_resolve_comunicado_oee_panel_preset_v4():
    payload = resolve_preset_slide("preset_comunicado_oee_panel")
    assert payload["slideType"] == "native"
    assert payload["nativeScreenKey"] == "custom_message"
    assert payload.get("source") == "mdd"
    cfg = payload["nativeConfig"]
    assert cfg.get("version") == 4
    assert cfg.get("background", {}).get("value") == "#f8fafc"
    blocks = cfg.get("blocks") or []
    types = {block.get("type") for block in blocks}
    assert "heading" in types
    assert "data_kpi" in types
    assert "data_chart" in types
    heading = next(block for block in blocks if block.get("type") == "heading")
    assert heading.get("style", {}).get("color") == "#0f172a"
    assert cfg.get("dataFilters", {}).get("periodDays") == 7


def test_resolve_comunicado_stock_panel_preset_v4():
    payload = resolve_preset_slide("preset_comunicado_stock_panel")
    cfg = payload["nativeConfig"]
    assert cfg.get("background", {}).get("value") == "#f8fafc"
    blocks = cfg.get("blocks") or []
    data_blocks = [block for block in blocks if str(block.get("type", "")).startswith("data_")]
    assert len(data_blocks) == 2
    table = next(block for block in data_blocks if block.get("type") == "data_table")
    assert table["dataBinding"]["maxRows"] == 5
    assert table.get("tablePreset") == "banded"
    assert table.get("tableOptions", {}).get("headerBg") == "#089bdb"


def test_export_preset_mdd_roundtrip():
    raw, filename = export_preset_mdd("preset_comunicado_oee_panel")
    assert filename.endswith(".mdd")
    assert len(raw) > 100
    parsed = parse_slide_template_mdd(raw)
    assert parsed["key"] == "preset_comunicado_oee_panel"
    assert parsed["nativeConfig"]["background"]["value"] == "#f8fafc"


def test_build_and_parse_slide_template_mdd():
    raw, filename = build_slide_template_mdd(
        key="custom_test",
        label="Teste",
        description="desc",
        title="Título",
        duration_sec=30,
        native_config={"version": 4, "background": {"type": "color", "value": "#fff"}, "blocks": []},
    )
    assert filename == "custom_test.mdd"
    parsed = parse_slide_template_mdd(raw)
    assert parsed["key"] == "custom_test"
    assert parsed["label"] == "Teste"
    assert parsed["nativeConfig"]["background"]["value"] == "#fff"
