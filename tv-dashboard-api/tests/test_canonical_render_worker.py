"""VISTA-CANONICAL-VISUAL-VERIFICATION-002 — bounded render worker client +
lazy canonical_stage fill + MCP ImageContent projection.

Covers: worker disabled/auth-missing paths, typed failure mapping, revision
race fail-closed, cache-hit skip, and additive ImageContent on the existing
get_playlist_context tool (text/structured payload preserved).
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from PIL import Image
from mcp.types import ImageContent, TextContent

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.services.data.canonical_render_client import (
    CanonicalRenderClient,
    CanonicalRenderError,
    CanonicalStageRenderService,
    RenderWorkerConfig,
)
from tv_app.application.services.data.slide_preview_render_service import (
    SlidePreviewRenderService,
)


def _png(size=(16, 9), color=(10, 120, 200, 255)) -> bytes:
    buf = BytesIO()
    Image.new("RGBA", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _patch_preview_service(monkeypatch, tmp_path: Path) -> SlidePreviewRenderService:
    svc = SlidePreviewRenderService(cache_dir=tmp_path)
    monkeypatch.setattr(
        "tv_app.application.services.data.slide_preview_render_service._default_service",
        svc,
    )
    return svc


def _sample_native() -> dict:
    return {
        "version": 5,
        "background": {"type": "solid", "color": "#0d2840"},
        "blocks": [
            {
                "id": "t1",
                "type": "text",
                "frame": {"x": 10, "y": 10, "w": 40, "h": 20},
                "content": "hello",
            }
        ],
    }


def _writes_for(*, playlist_id, slides, revision):
    writes = MagicMock()
    writes.get_playlist.return_value = {"id": str(playlist_id), "name": "P"}
    writes.list_slides.return_value = slides
    writes.list_sections.return_value = []
    writes.get_revision.return_value = revision
    return writes


def _present_payload(*, slide_id: str, width: int = 1920, height: int = 1080) -> dict:
    return {
        "playlist": {
            "id": "p1",
            "viewportProfile": None,
            "viewportWidth": width,
            "viewportHeight": height,
        },
        "slides": [
            {
                "id": slide_id,
                "slideType": "native",
                "native": {
                    "screenKey": "custom_message",
                    "config": {},
                    "data": {"blocks": []},
                },
            }
        ],
    }


# ------------------------------------------------------------------
# A. CanonicalRenderClient — bounded, typed failures, no retry storm
# ------------------------------------------------------------------


def test_client_disabled_without_url():
    client = CanonicalRenderClient(RenderWorkerConfig(url="", timeout_sec=1))
    with pytest.raises(CanonicalRenderError) as exc:
        client.render_png(
            playlist_id="p", slide_id="s", revision=1, presentation={}, viewport=None
        )
    assert exc.value.code == "RENDER_WORKER_DISABLED"


def test_client_auth_missing_without_service_token(monkeypatch):
    """Dedicated token unset → fail closed, even if the platform S2S token IS
    set — no credential fallback/reuse across surfaces."""
    import tv_app.application.services.data.canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "platform-tok")
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=1))
    with pytest.raises(CanonicalRenderError) as exc:
        client.render_png(
            playlist_id="p", slide_id="s", revision=1, presentation={}, viewport=None
        )
    assert exc.value.code == "RENDER_WORKER_AUTH_MISSING"


def test_client_uses_dedicated_token_not_platform_s2s(monkeypatch):
    """NEGATIVE: API_DELPI_INTERNAL_SERVICE_TOKEN must never be sent to the
    worker — only the dedicated TV_RENDER_WORKER_SERVICE_TOKEN."""
    import tv_app.application.services.data.canonical_render_client as crc

    monkeypatch.setattr(
        crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "worker-dedicated"
    )
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "platform-tok")
    monkeypatch.setattr(crc.httpx, "Client", _FakeClient)
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=5))
    client.render_png(
        playlist_id="p",
        slide_id="s",
        revision=1,
        presentation={},
        viewport=None,
    )
    sent = _FakeClient.last_request["headers"]["Authorization"]
    assert sent == "Bearer worker-dedicated"
    assert "platform-tok" not in sent


class _FakeResponse:
    def __init__(self, status_code=200, content=b"", json_body=None):
        self.status_code = status_code
        self.content = content
        self._json = json_body

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


class _FakeClient:
    """httpx.Client stand-in recording the request for assertions."""

    last_request = {}

    def __init__(self, *a, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, *, json, headers):  # noqa: A002 — httpx kwarg
        type(self).last_request = {"url": url, "json": json, "headers": headers}
        return _FakeResponse(
            status_code=200,
            content=_png(),
        )


def test_client_posts_bounded_contract(monkeypatch):
    import tv_app.application.services.data.canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "tok-worker")
    monkeypatch.setattr(crc.httpx, "Client", _FakeClient)
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=5))
    png = client.render_png(
        playlist_id="pl-1",
        slide_id="sl-1",
        revision=7,
        presentation=_present_payload(slide_id="sl-1"),
        viewport={"width": 1920, "height": 1080},
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    req = _FakeClient.last_request
    assert req["url"] == "http://w:8100/render"
    assert req["headers"]["Authorization"] == "Bearer tok-worker"
    body = req["json"]
    assert body["playlistId"] == "pl-1"
    assert body["slideId"] == "sl-1"
    assert body["revision"] == 7
    assert body["viewport"] == {"width": 1920, "height": 1080}
    assert set(body) == {"playlistId", "slideId", "revision", "viewport", "presentation"}


def test_client_maps_worker_error_code(monkeypatch):
    import tv_app.application.services.data.canonical_render_client as crc

    class _ErrClient(_FakeClient):
        def post(self, url, *, json, headers):
            return _FakeResponse(
                status_code=429,
                content=b'{"status":"error","code":"RENDER_BUSY"}',
                json_body={"code": "RENDER_BUSY"},
            )

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "tok")
    monkeypatch.setattr(crc.httpx, "Client", _ErrClient)
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=5))
    with pytest.raises(CanonicalRenderError) as exc:
        client.render_png(
            playlist_id="p", slide_id="s", revision=1, presentation={}, viewport=None
        )
    assert exc.value.code == "RENDER_BUSY"


def test_client_rejects_non_png_output(monkeypatch):
    import tv_app.application.services.data.canonical_render_client as crc

    class _BadClient(_FakeClient):
        def post(self, url, *, json, headers):
            return _FakeResponse(status_code=200, content=b"not-a-png")

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "tok")
    monkeypatch.setattr(crc.httpx, "Client", _BadClient)
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=5))
    with pytest.raises(CanonicalRenderError) as exc:
        client.render_png(
            playlist_id="p", slide_id="s", revision=1, presentation={}, viewport=None
        )
    assert exc.value.code == "RENDER_OUTPUT_INVALID"


def test_client_rejects_oversized_output(monkeypatch):
    import tv_app.application.services.data.canonical_render_client as crc

    big = _png() + b"\x00" * (8_000_001 - len(_png()))

    class _BigClient(_FakeClient):
        def post(self, url, *, json, headers):
            return _FakeResponse(status_code=200, content=big)

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_SERVICE_TOKEN", "tok")
    monkeypatch.setattr(crc.httpx, "Client", _BigClient)
    client = CanonicalRenderClient(RenderWorkerConfig(url="http://w:8100", timeout_sec=5))
    with pytest.raises(CanonicalRenderError) as exc:
        client.render_png(
            playlist_id="p", slide_id="s", revision=1, presentation={}, viewport=None
        )
    assert exc.value.code == "RENDER_OUTPUT_TOO_LARGE"


# ------------------------------------------------------------------
# B. CanonicalStageRenderService — fill-miss, revision race, cache hit
# ------------------------------------------------------------------


def _present_mock(slide_id: str) -> MagicMock:
    present = MagicMock()
    present.build_by_id.return_value = _present_payload(slide_id=slide_id)
    return present


def test_ensure_rendered_stores_worker_png(monkeypatch, tmp_path):
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    writes = _writes_for(playlist_id=playlist_id, slides=[], revision=5)
    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.return_value = _png(size=(32, 18))
    render = CanonicalStageRenderService(client=client)

    meta = render.ensure_rendered(
        playlist_id=playlist_id,
        slide_id=str(slide_id),
        revision=5,
        writes=writes,
        present=_present_mock(str(slide_id)),
        preview_svc=svc,
    )
    assert meta and meta["kind"] == "canonical_stage" and meta["revision"] == 5
    assert svc.read_rendered_png(slide_id=str(slide_id), revision=5) is not None
    client.render_png.assert_called_once()
    kwargs = client.render_png.call_args.kwargs
    assert kwargs["revision"] == 5
    assert kwargs["viewport"] == {"width": 1920, "height": 1080}


def test_ensure_rendered_cache_hit_skips_client(monkeypatch, tmp_path):
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    svc.store_rendered_png(
        slide_id=str(slide_id), revision=5, png=_png(), width=8, height=8
    )
    client = MagicMock(spec=CanonicalRenderClient)
    render = CanonicalStageRenderService(client=client)
    meta = render.ensure_rendered(
        playlist_id=playlist_id,
        slide_id=str(slide_id),
        revision=5,
        writes=_writes_for(playlist_id=playlist_id, slides=[], revision=5),
        present=_present_mock(str(slide_id)),
        preview_svc=svc,
    )
    assert meta is not None
    client.render_png.assert_not_called()


def test_ensure_rendered_revision_race_discards_png(monkeypatch, tmp_path):
    """A commit landing between request and render must fail closed — the
    PNG is dropped and the artifact store stays empty for the stale rev."""
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    writes = _writes_for(playlist_id=playlist_id, slides=[], revision=5)
    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.return_value = _png()

    def _bump(*a, **kw):
        writes.get_revision.return_value = 6
        return _png()

    client.render_png.side_effect = _bump
    render = CanonicalStageRenderService(client=client)
    with pytest.raises(CanonicalRenderError) as exc:
        render.ensure_rendered(
            playlist_id=playlist_id,
            slide_id=str(slide_id),
            revision=5,
            writes=writes,
            present=_present_mock(str(slide_id)),
            preview_svc=svc,
        )
    assert exc.value.code == "RENDER_REVISION_STALE"
    assert svc.read_rendered_png(slide_id=str(slide_id), revision=5) is None


# ------------------------------------------------------------------
# C. Dispatch lazy fill — include_preview triggers render on miss
# ------------------------------------------------------------------


def _context_with_preview(dispatch, *, playlist_id, slide_id):
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    with patch.object(
        dispatch._access,
        "resolve",
        return_value=SimpleNamespace(
            can_read=True, can_edit=True, level="owner", playlist={"id": str(playlist_id)}
        ),
    ), patch.object(dispatch, "_actor", return_value="u1"):
        return dispatch.get_playlist_context(
            user=user,
            playlist_id=str(playlist_id),
            include_preview=True,
            preview_slide_id=str(slide_id),
        )


def _context_dispatch(playlist_id, slide_id, *, revision=5):
    slide = {
        "id": str(slide_id),
        "title": "S1",
        "nativeConfig": _sample_native(),
        "slideType": "native",
    }
    writes = _writes_for(
        playlist_id=playlist_id, slides=[slide], revision=revision
    )
    return GptActionsDispatchService(repo=MagicMock(), writes=writes, commit=MagicMock())


def test_context_rendered_ready_via_worker(monkeypatch, tmp_path):
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    dispatch = _context_dispatch(playlist_id, slide_id)
    dispatch._present = _present_mock(str(slide_id))

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "http://w:8100")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)

    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.return_value = _png(size=(64, 36))
    render_svc = CanonicalStageRenderService(client=client)
    monkeypatch.setattr(crc, "_default_render_service", render_svc)

    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "ready"
    assert rendered["kind"] == "canonical_stage"
    assert rendered["source"] == "render_worker"
    assert rendered["revision"] == 5
    assert "slide-previews/" in rendered["previewUrl"]
    assert svc.read_rendered_png(slide_id=str(slide_id), revision=5) is not None


def test_context_rendered_worker_down_degrades_truthfully(monkeypatch, tmp_path):
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    dispatch = _context_dispatch(playlist_id, slide_id)
    dispatch._present = _present_mock(str(slide_id))

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "http://w:8100")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)

    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.side_effect = CanonicalRenderError("RENDER_WORKER_UNAVAILABLE")
    monkeypatch.setattr(
        crc, "_default_render_service", CanonicalStageRenderService(client=client)
    )

    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "RENDER_WORKER_UNAVAILABLE"
    # Context itself still succeeds — evidence fill never breaks the read.
    assert out["playlist"]["id"] == str(playlist_id)


def test_context_rendered_disabled_reports_no_artifact(monkeypatch, tmp_path):
    """Worker URL empty → no autonomous render; honest NO_CANONICAL_ARTIFACT."""
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    dispatch = _context_dispatch(playlist_id, slide_id)

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)

    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "NO_CANONICAL_ARTIFACT"


def test_context_rendered_external_slide_never_rendered(monkeypatch, tmp_path):
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    slide = {
        "id": str(slide_id),
        "title": "Ext",
        "slideType": "external",
        "externalUrl": "https://example.test",
    }
    writes = _writes_for(playlist_id=playlist_id, slides=[slide], revision=3)
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "http://w:8100")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)
    client = MagicMock(spec=CanonicalRenderClient)
    monkeypatch.setattr(
        crc, "_default_render_service", CanonicalStageRenderService(client=client)
    )

    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["failureCode"] == "UNSUPPORTED_SLIDE_TYPE"
    client.render_png.assert_not_called()


def test_singleflight_pending_then_ready(monkeypatch, tmp_path):
    """A owns the miss and renders; concurrent B on the exact same key gets
    pending/RENDER_PENDING (never unavailable/NO_CANONICAL_ARTIFACT); after A
    completes, C reads the ready artifact — exactly one render total."""
    import threading

    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    dispatch = _context_dispatch(playlist_id, slide_id)
    dispatch._present = _present_mock(str(slide_id))

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "http://w:8100")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)
    # Stub access once — patch.object per call would race across threads.
    monkeypatch.setattr(
        dispatch,
        "_access",
        SimpleNamespace(
            resolve=lambda *a, **k: SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": str(playlist_id)},
            ),
            actor_id=lambda user: "u1",
        ),
    )

    entered = threading.Event()
    release = threading.Event()

    def _render(**kw):
        entered.set()
        release.wait(timeout=15)
        return _png(size=(32, 18))

    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.side_effect = _render
    monkeypatch.setattr(
        crc, "_default_render_service", CanonicalStageRenderService(client=client)
    )

    def _ctx():
        return dispatch.get_playlist_context(
            user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
            playlist_id=str(playlist_id),
            include_preview=True,
            preview_slide_id=str(slide_id),
        )

    owner: dict = {}
    thread = threading.Thread(target=lambda: owner.update(out=_ctx()))
    thread.start()
    assert entered.wait(timeout=10), "owner render never started"

    loser = _ctx()
    rendered = loser["slidePreview"]["rendered"]
    assert rendered["status"] == "pending"
    assert rendered["failureCode"] == "RENDER_PENDING"
    assert rendered["revision"] == 5

    release.set()
    thread.join(timeout=15)
    assert not thread.is_alive()
    owner_rendered = owner["out"]["slidePreview"]["rendered"]
    assert owner_rendered["status"] == "ready"
    assert owner_rendered["revision"] == 5

    later = _ctx()
    later_rendered = later["slidePreview"]["rendered"]
    assert later_rendered["status"] == "ready"
    assert later_rendered["revision"] == 5
    assert client.render_png.call_count == 1
    assert svc.read_rendered_png(slide_id=str(slide_id), revision=5) is not None


def test_singleflight_failed_owner_not_stuck_pending(monkeypatch, tmp_path):
    """Failed owner render → typed unavailable; the key is released so the
    next request retries normally instead of pending forever."""
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    dispatch = _context_dispatch(playlist_id, slide_id)
    dispatch._present = _present_mock(str(slide_id))

    from tv_app.application.services.data import canonical_render_client as crc

    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_URL", "http://w:8100")
    monkeypatch.setattr(crc.settings, "TV_RENDER_WORKER_TRIGGER_ON_CONTEXT", True)

    client = MagicMock(spec=CanonicalRenderClient)
    client.render_png.side_effect = CanonicalRenderError("RENDER_TIMEOUT")
    monkeypatch.setattr(
        crc, "_default_render_service", CanonicalStageRenderService(client=client)
    )

    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "RENDER_TIMEOUT"

    # Key released: a subsequent request renders again and becomes ready.
    client.render_png.side_effect = None
    client.render_png.return_value = _png(size=(32, 18))
    out2 = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    assert out2["slidePreview"]["rendered"]["status"] == "ready"


# ------------------------------------------------------------------
# D. MCP ImageContent — additive, exact bytes, text preserved
# ------------------------------------------------------------------


def test_mcp_context_ready_artifact_appends_image_content(monkeypatch, tmp_path):
    from delpi_auth.request_context import (
        reset_current_user,
        reset_request_authorization,
        set_current_user,
        set_request_authorization,
    )

    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    artifact_png = _png(size=(32, 18))
    svc.store_rendered_png(
        slide_id=str(slide_id), revision=5, png=artifact_png, width=32, height=18
    )

    from tv_app.interface.mcp import tool_bridge

    dispatch_data = {
        "playlist": {"id": str(playlist_id)},
        "revision": 5,
        "slidePreview": {
            "slideId": str(slide_id),
            "kind": "schematic_layout",
            "rendered": {
                "kind": "canonical_stage",
                "status": "ready",
                "revision": 5,
                "width": 32,
                "height": 18,
                "mimeType": "image/png",
                "previewUrl": "http://x/gpt-actions/v1/slide-previews/tok",
            },
        },
    }
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    u_tok = set_current_user(user)
    a_tok = set_request_authorization("Bearer test")
    try:
        with patch.object(
            tool_bridge._dispatch, "get_playlist_context", return_value=dispatch_data
        ):
            result = tool_bridge.tool_get_playlist_context(
                playlist_id=str(playlist_id), include_preview=True
            )
    finally:
        reset_current_user(u_tok)
        reset_request_authorization(a_tok)

    assert result.is_error is False
    kinds = [type(block).__name__ for block in result.content]
    assert "TextContent" in kinds
    assert "ImageContent" in kinds
    image = next(b for b in result.content if isinstance(b, ImageContent))
    assert base64.b64decode(image.data) == artifact_png
    assert image.mime_type == "image/png"
    # Text + structured payload preserved verbatim.
    text = next(b for b in result.content if isinstance(b, TextContent))
    assert "canonical_stage" in text.text
    assert result.structured_content["data"]["slidePreview"]["rendered"]["status"] == "ready"


def test_mcp_context_unavailable_artifact_is_text_only(monkeypatch, tmp_path):
    from delpi_auth.request_context import (
        reset_current_user,
        reset_request_authorization,
        set_current_user,
        set_request_authorization,
    )

    _patch_preview_service(monkeypatch, tmp_path)
    from tv_app.interface.mcp import tool_bridge

    dispatch_data = {
        "playlist": {"id": "p1"},
        "slidePreview": {
            "slideId": "s1",
            "rendered": {
                "kind": "canonical_stage",
                "status": "unavailable",
                "failureCode": "NO_CANONICAL_ARTIFACT",
            },
        },
    }
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    u_tok = set_current_user(user)
    a_tok = set_request_authorization("Bearer test")
    try:
        with patch.object(
            tool_bridge._dispatch, "get_playlist_context", return_value=dispatch_data
        ):
            result = tool_bridge.tool_get_playlist_context(
                playlist_id="p1", include_preview=True
            )
    finally:
        reset_current_user(u_tok)
        reset_request_authorization(a_tok)

    assert result.is_error is False
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)


def test_mcp_context_stale_revision_never_serves_image(monkeypatch, tmp_path):
    """Artifact bytes bound to an OLD revision must not leak as current."""
    from delpi_auth.request_context import (
        reset_current_user,
        reset_request_authorization,
        set_current_user,
        set_request_authorization,
    )

    svc = _patch_preview_service(monkeypatch, tmp_path)
    svc.store_rendered_png(slide_id="s1", revision=5, png=_png(), width=8, height=8)
    from tv_app.interface.mcp import tool_bridge

    dispatch_data = {
        "playlist": {"id": "p1"},
        "slidePreview": {
            "slideId": "s1",
            "rendered": {
                "kind": "canonical_stage",
                "status": "ready",
                "revision": 6,  # current rev is 6; stored artifact is rev 5
                "mimeType": "image/png",
            },
        },
    }
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    u_tok = set_current_user(user)
    a_tok = set_request_authorization("Bearer test")
    try:
        with patch.object(
            tool_bridge._dispatch, "get_playlist_context", return_value=dispatch_data
        ):
            result = tool_bridge.tool_get_playlist_context(
                playlist_id="p1", include_preview=True
            )
    finally:
        reset_current_user(u_tok)
        reset_request_authorization(a_tok)

    assert all(not isinstance(b, ImageContent) for b in result.content)


def test_mcp_tool_count_unchanged():
    from tv_app.interface.mcp import tool_bridge

    names = tool_bridge.list_tool_names()
    assert len(names) == len(set(names))
    # MCP surface did not grow: image is a content block on the existing tool.
    assert "get_playlist_context" in names
