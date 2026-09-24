"""Unit tests for PresentationMutation deep-merge (partial nested patches)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tv_app.application.services.data.presentation_mutation.merge import (
    deep_merge_dicts,
    merge_block_patch,
    merge_data_binding,
    merge_native_config_key,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)


@pytest.fixture(autouse=True)
def _clear_catalog():
    clear_presentation_ops_content_cache()
    yield
    clear_presentation_ops_content_cache()


def test_deep_merge_preserves_siblings_and_clears_null():
    base = {"fontSize": 28, "color": "red", "fontWeight": "normal"}
    out = deep_merge_dicts(base, {"fontSize": 48, "fontWeight": "bold"})
    assert out == {"fontSize": 48, "color": "red", "fontWeight": "bold"}
    cleared = deep_merge_dicts(out, {"color": None})
    assert "color" not in cleared
    assert cleared["fontSize"] == 48


def test_merge_block_patch_preserves_style_color():
    existing = {
        "id": "b1",
        "type": "text",
        "content": "Olá",
        "style": {"color": "red", "fontSize": 28, "fontWeight": "normal"},
        "frame": {"x": 1, "y": 2, "w": 10, "h": 5},
    }
    cleaned = {
        "id": "b1",
        "type": "text",
        "style": {"fontSize": 48, "fontWeight": "bold"},
    }
    merged = merge_block_patch(existing, cleaned)
    assert merged["style"]["color"] == "red"
    assert merged["style"]["fontSize"] == 48
    assert merged["style"]["fontWeight"] == "bold"
    assert merged["frame"] == existing["frame"]


def test_merge_block_patch_preserves_frame_siblings():
    existing = {"id": "b1", "type": "text", "frame": {"x": 1, "y": 2, "w": 10, "h": 5}}
    cleaned = {"id": "b1", "type": "text", "frame": {"w": 40}}
    merged = merge_block_patch(existing, cleaned)
    assert merged["frame"] == {"x": 1, "y": 2, "w": 40, "h": 5}


def test_merge_data_binding_keeps_refresh_sec():
    prior = {
        "operationId": "op.a",
        "params": {"a": 1},
        "refreshSec": 30,
        "selectedValueFields": ["x"],
    }
    patch = {"operationId": "op.a", "params": {"a": 2}, "displayMode": "kpi", "label": "L"}
    out = merge_data_binding(prior, patch)
    assert out["refreshSec"] == 30
    assert out["selectedValueFields"] == ["x"]
    assert out["params"]["a"] == 2
    assert out["displayMode"] == "kpi"


def test_merge_native_background_preserves_underlay():
    cfg = {
        "background": {
            "type": "image",
            "assetId": "asset-1",
            "underlay": {"opacity": 0.4},
        }
    }
    merge_native_config_key(
        cfg, "background", {"type": "solid", "value": "#0033aa"}
    )
    assert cfg["background"]["type"] == "solid"
    assert cfg["background"]["value"] == "#0033aa"
    assert cfg["background"]["underlay"] == {"opacity": 0.4}
    assert cfg["background"]["assetId"] == "asset-1"


def test_preview_upsert_block_partial_style_keeps_color(monkeypatch):
    from uuid import uuid4
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )

    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 3, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "txt-1",
                            "type": "text",
                            "content": "Olá mundo",
                            "style": {
                                "color": "red",
                                "fontSize": 28,
                                "fontWeight": "normal",
                            },
                        }
                    ],
                },
            }

    svc = PresentationPatchService(repo=_Repo())

    result = svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {
                        "id": "txt-1",
                        "type": "text",
                        "style": {"fontSize": 48, "fontWeight": "bold"},
                    },
                }
            ],
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-1")
    assert block["style"]["color"] == "red"
    assert block["style"]["fontSize"] == 48
    assert block["style"]["fontWeight"] == "bold"


def test_preview_upsert_text_projection_sanitizes_dual_bind(monkeypatch):
    """Campo-equivalent textProjection write clears contradictory contentRuns.dataRef."""
    from uuid import uuid4

    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 1, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "txt-dual",
                            "type": "text",
                            "content": "",
                            "textProjection": {"field": "Meta"},
                            "contentRuns": [
                                {"text": "ACUMULADO "},
                                {"dataRef": {"field": "filter.start_date"}},
                                {"text": " - "},
                                {"dataRef": {"field": "filter.end_date"}},
                            ],
                        }
                    ],
                },
            }

    svc = PresentationPatchService(repo=_Repo())
    result = svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {
                        "id": "txt-dual",
                        "type": "text",
                        "textProjection": {"field": "Rol", "format": "number"},
                    },
                }
            ],
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-dual")
    assert block["textProjection"]["field"] == "Rol"
    assert block["contentRuns"] == [{"text": "ACUMULADO "}, {"text": " - "}]
    assert not any(
        isinstance(run, dict) and isinstance(run.get("dataRef"), dict)
        for run in block.get("contentRuns") or []
    )
