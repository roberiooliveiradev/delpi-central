import pytest

from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    list_slide_presets,
    resolve_preset_slide,
)


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
    cfg = payload["nativeConfig"]
    assert cfg.get("version") == 4
    blocks = cfg.get("blocks") or []
    types = {block.get("type") for block in blocks}
    assert "heading" in types
    assert "data_kpi" in types
    assert "data_chart" in types
    assert cfg.get("dataFilters", {}).get("periodDays") == 7


def test_resolve_comunicado_stock_panel_preset_v4():
    payload = resolve_preset_slide("preset_comunicado_stock_panel")
    cfg = payload["nativeConfig"]
    blocks = cfg.get("blocks") or []
    data_blocks = [block for block in blocks if str(block.get("type", "")).startswith("data_")]
    assert len(data_blocks) == 2
    table = next(block for block in data_blocks if block.get("type") == "data_table")
    assert table["dataBinding"]["maxRows"] == 5
