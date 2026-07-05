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
