"""layoutDigest projection + layout_perception directives + slide preview PNG."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.layout_digest_service import LayoutDigestService
from tv_app.application.services.data.slide_preview_render_service import (
    SlidePreviewRenderService,
)
from tv_app.application.services.data.slide_preview_token import (
    mint_slide_preview_token,
    parse_slide_preview_token,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()


def _sample_native() -> dict:
    return {
        "version": 5,
        "background": {"type": "gradient", "from": "#003866", "to": "#0d2840"},
        "blocks": [
            {
                "id": "kpi-1",
                "type": "kpi_view",
                "frame": {"x": 4, "y": 12, "w": 28, "h": 30},
                "style": {"zIndex": 2},
                "parts": {
                    "value": {"fontSize": 56},
                    "title": {"fontSize": 14, "text": "OTD"},
                    "icon": {"iconSize": 22},
                },
            },
            {
                "id": "chart-1",
                "type": "chart_view",
                "chartType": "area",
                "frame": {"x": 36, "y": 12, "w": 60, "h": 70},
                "style": {"zIndex": 1},
            },
            {
                "id": "ds-1",
                "type": "data_source",
                "dataSourceId": "ds-1",
            },
        ],
    }


def test_layout_digest_projects_frames_and_hints():
    digest = LayoutDigestService.digest_native_config(
        _sample_native(),
        slide_id="slide-a",
        title="Painel",
    )
    assert digest["slideId"] == "slide-a"
    assert digest["blockCount"] == 2
    assert len(digest["blocks"]) == 2
    kpi = next(b for b in digest["blocks"] if b["id"] == "kpi-1")
    assert kpi["frame"] == {"x": 4.0, "y": 12.0, "w": 28.0, "h": 30.0}
    assert kpi["signals"]["kpiValueFontSize"] == 56.0
    chart = next(b for b in digest["blocks"] if b["id"] == "chart-1")
    assert chart["signals"]["chartType"] == "area"
    hints = digest["layoutHints"]
    assert hints["kpiCount"] == 1
    assert hints["maxPrimarySignals"] >= 1
    assert "density" in hints
    assert hints["hasCoarseOverlap"] is False


def test_layout_digest_detects_coarse_overlap():
    native = {
        "blocks": [
            {
                "id": "a",
                "type": "kpi_view",
                "frame": {"x": 10, "y": 10, "w": 40, "h": 40},
            },
            {
                "id": "b",
                "type": "kpi_view",
                "frame": {"x": 20, "y": 20, "w": 40, "h": 40},
            },
        ]
    }
    digest = LayoutDigestService.digest_native_config(native)
    assert digest["layoutHints"]["hasCoarseOverlap"] is True
    assert digest["layoutHints"]["coarseOverlaps"]


def test_layout_perception_directives_projected():
    directives = VistaAgentIntelligenceService.agent_directives()
    lp = directives["layout_perception"]
    assert lp["principle"] == "DIGEST_BEFORE_INVENT_FRAMES"
    rules = " ".join(lp["rules"]).lower()
    assert "layoutdigest" in rules.replace(" ", "").replace("_", "")
    assert "LAYOUT_PERCEPTION" in directives["modes"]
    assert any("layoutdigest" in str(item).lower().replace(" ", "") for item in directives["anti_patterns"])


def test_slide_preview_png_is_valid_and_cached(tmp_path: Path):
    svc = SlidePreviewRenderService(cache_dir=tmp_path)
    png1 = svc.get_or_render(
        slide_id="s1",
        revision=3,
        native_config=_sample_native(),
        title="Demo",
    )
    assert png1[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png1) > 200
    png2 = svc.get_or_render(
        slide_id="s1",
        revision=3,
        native_config={"blocks": []},
        title="ignored-cache",
    )
    assert png1 == png2
    payload = svc.build_preview_payload(
        playlist_id=str(uuid4()),
        slide_id="s1",
        revision=3,
        native_config=_sample_native(),
        public_base_url="https://example.test",
        root_path="/apps/tv-dashboard-api",
    )
    assert payload["width"] == 960
    assert payload["height"] == 540
    assert payload["previewUrl"].startswith(
        "https://example.test/apps/tv-dashboard-api/gpt-actions/v1/slide-previews/"
    )
    assert "expiresAt" in payload


def test_slide_preview_token_roundtrip():
    pid, sid = str(uuid4()), str(uuid4())
    token, exp = mint_slide_preview_token(
        playlist_id=pid, slide_id=sid, revision=7, ttl_sec=120
    )
    claims = parse_slide_preview_token(token)
    assert claims["playlistId"] == pid
    assert claims["slideId"] == sid
    assert claims["revision"] == "7"
    assert claims["expiresAt"] == exp


def test_get_playlist_context_includes_layout_digest():
    from unittest.mock import MagicMock, patch
    from types import SimpleNamespace

    writes = MagicMock()
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    writes.get_playlist.return_value = {"id": playlist_id, "name": "P"}
    writes.list_slides.return_value = [
        {
            "id": slide_id,
            "title": "S1",
            "nativeConfig": _sample_native(),
        }
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 11
    repo = MagicMock()
    dispatch = GptActionsDispatchService(repo=repo, writes=writes, commit=MagicMock())
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with patch.object(
        dispatch._access,
        "resolve",
        return_value=SimpleNamespace(
            can_read=True, can_edit=True, level="owner", playlist={"id": playlist_id}
        ),
    ), patch.object(dispatch, "_actor", return_value="u1"):
        out = dispatch.get_playlist_context(user=user, playlist_id=playlist_id)

    assert "layoutDigest" in out
    assert len(out["layoutDigest"]) == 1
    assert out["layoutDigest"][0]["slideId"] == slide_id
    assert out["layoutDigest"][0]["blockCount"] == 2
    assert out["currentRevision"] == 11


def test_get_playlist_context_include_preview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from unittest.mock import MagicMock, patch
    from types import SimpleNamespace

    from tv_app.application.services.data import slide_preview_render_service as mod

    monkeypatch.setattr(
        mod,
        "_default_service",
        SlidePreviewRenderService(cache_dir=tmp_path),
    )

    writes = MagicMock()
    slide_id = str(uuid4())
    playlist_id = str(uuid4())
    writes.get_playlist.return_value = {"id": playlist_id, "name": "P"}
    writes.list_slides.return_value = [
        {"id": slide_id, "title": "S1", "nativeConfig": _sample_native()}
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 2
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with patch.object(
        dispatch._access,
        "resolve",
        return_value=SimpleNamespace(
            can_read=True, can_edit=True, level="owner", playlist={"id": playlist_id}
        ),
    ), patch.object(dispatch, "_actor", return_value="u1"):
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            include_preview=True,
            preview_slide_id=slide_id,
        )

    preview = out["slidePreview"]
    assert preview["slideId"] == slide_id
    assert preview["revision"] == 2
    assert "slide-previews/" in preview["previewUrl"]

    png, meta = dispatch.get_slide_preview_png(
        user=None,
        token=preview["previewUrl"].rsplit("/", 1)[-1],
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert meta["slideId"] == slide_id


def test_spatial_adjust_from_digest_without_print_smoke():
    """E1 smoke: digest alone informs frame adjust (no user screenshot)."""
    digest = LayoutDigestService.digest_native_config(
        _sample_native(), slide_id="s1", title="S"
    )
    kpi = next(b for b in digest["blocks"] if b["type"] == "kpi_view")
    fr = kpi["frame"]
    # Simulated VISTA decision: enlarge KPI using INFORMED frame
    adjusted = {
        "x": fr["x"],
        "y": fr["y"],
        "w": min(40.0, fr["w"] + 6.0),
        "h": min(40.0, fr["h"] + 4.0),
    }
    assert adjusted["w"] > fr["w"]
    assert adjusted["x"] == fr["x"]
    directives = VistaAgentIntelligenceService.agent_directives()["layout_perception"]
    assert "digest" in directives["summary"].lower()
    assert any("print" in str(f).lower() for f in directives["forbidden"])
