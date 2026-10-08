"""VISTA-LIVE-EDITOR-VISUAL-VERIFICATION-003 — signed preview capability +
canonical_stage rendered artifact (live-editor-captured, revision-bound).

Covers the middleware CONTRACT_DRIFT fix (signed token = AuthZ for the
narrowest prefix only), the additive ``slidePreview.rendered`` contract and
the live-editor visual policy: only artifacts produced by the caller's own
live editor stage (``source=editor_live`` + matching ``clientId``) are visual
evidence — editor closed means ``EDITOR_NOT_OPEN``, never a silent render.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import tv_app.core.security as sec
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.services.data.slide_preview_render_service import (
    SlidePreviewRenderService,
)
from tv_app.application.services.data.slide_preview_token import (
    mint_slide_preview_token,
    parse_slide_preview_token,
)
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.core.security import (
    arequire_fresh_write_authorization as _real_async_gate,
)
from tv_app.core.security import (
    require_fresh_write_authorization as _real_sync_gate,
)
from tv_app.main import app
from tv_app.middleware.auth_middleware import _is_public

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f"
    b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)
AUTH = {"Authorization": "Bearer tok-user"}


def _png(size=(8, 8), color=(10, 120, 200, 255)) -> bytes:
    buf = BytesIO()
    Image.new("RGBA", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _rbac(**over) -> dict:
    base = {
        "id": "user-1",
        "email": "u@delpi.local",
        "name": "User",
        "roles": [],
        "groups": [],
        "permissions": ["tv-dashboard.read", "tv-dashboard.write"],
        "is_superadmin": False,
    }
    base.update(over)
    return base


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


def _patch_preview_service(monkeypatch, tmp_path: Path) -> SlidePreviewRenderService:
    svc = SlidePreviewRenderService(cache_dir=tmp_path)
    monkeypatch.setattr(
        "tv_app.application.services.data.slide_preview_render_service._default_service",
        svc,
    )
    return svc


def _writes_for(*, playlist_id, slides, revision):
    writes = MagicMock()
    writes.get_playlist.return_value = {"id": str(playlist_id), "name": "P"}
    writes.list_slides.return_value = slides
    writes.list_sections.return_value = []
    writes.get_revision.return_value = revision
    return writes


def _live_editor(
    monkeypatch: pytest.MonkeyPatch,
    *,
    actor: str = "u1",
    playlist_id,
    slide_id,
    client_id: str = "c-live",
):
    """Simula editor ao vivo do caller: foco fresco no editorFocusStore +
    clientId presente/vivo no presentation realtime hub."""
    from tv_app.application.services import editor_focus_store as efs_mod
    from tv_app.application.services import presentation_realtime_hub as hub_mod
    from tv_app.application.services.editor_focus_store import EditorFocusStore

    store = EditorFocusStore()
    store.record(
        user_id=actor,
        playlist_id=str(playlist_id),
        slide_id=str(slide_id),
        client_id=client_id,
    )
    monkeypatch.setattr(efs_mod, "editor_focus_store", store)
    hub = SimpleNamespace(
        is_editor_client_live=lambda *a, **k: True,
        request_visual_capture=MagicMock(return_value=True),
    )
    monkeypatch.setattr(hub_mod, "presentation_realtime_hub", hub)
    return SimpleNamespace(store=store, hub=hub)


def _no_live_editor(monkeypatch: pytest.MonkeyPatch):
    """Garante isolamento: nenhum foco/nenhum cliente vivo para ninguém."""
    from tv_app.application.services import editor_focus_store as efs_mod
    from tv_app.application.services import presentation_realtime_hub as hub_mod
    from tv_app.application.services.editor_focus_store import EditorFocusStore

    monkeypatch.setattr(efs_mod, "editor_focus_store", EditorFocusStore())
    hub = SimpleNamespace(
        is_editor_client_live=lambda *a, **k: False,
        request_visual_capture=MagicMock(return_value=True),
    )
    monkeypatch.setattr(hub_mod, "presentation_realtime_hub", hub)
    return hub


# ------------------------------------------------------------------
# A. Signed preview auth — narrowest middleware exception, fail-closed
# ------------------------------------------------------------------


def test_signed_preview_prefix_public_scope_is_narrow():
    assert _is_public("/gpt-actions/v1/slide-previews/abc.def")
    assert _is_public("/apps/tv-dashboard-api/gpt-actions/v1/slide-previews/abc.def")
    # Everything else under /gpt-actions/v1 stays JWT-protected.
    assert not _is_public("/gpt-actions/v1/catalog")
    assert not _is_public("/gpt-actions/v1/changes/preview")
    assert not _is_public("/gpt-actions/v1/changes/commit")
    # No bare prefix escape: missing token or look-alike path is not public.
    assert not _is_public("/gpt-actions/v1/slide-previews")
    assert not _is_public("/gpt-actions/v1/slide-previewsXYZ")


def test_signed_preview_valid_token_200_without_bearer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Route-level proof of the 403 CONTRACT_DRIFT fix: no Authorization
    header, signed token alone authorizes the PNG."""
    from tv_app.interface.http.routes import gpt_actions_routes as routes

    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    monkeypatch.setattr(
        routes._dispatch,
        "_writes",
        _writes_for(
            playlist_id=playlist_id,
            slides=[
                {"id": str(slide_id), "title": "S1", "nativeConfig": _sample_native()}
            ],
            revision=7,
        ),
    )
    token, _ = mint_slide_preview_token(
        playlist_id=str(playlist_id), slide_id=str(slide_id), revision=7
    )
    resp = TestClient(app).get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_signed_preview_tampered_and_expired_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _patch_preview_service(monkeypatch, tmp_path)
    client = TestClient(app)

    tampered = mint_slide_preview_token(
        playlist_id=str(uuid4()), slide_id=str(uuid4()), revision=1
    )[0]
    tampered = tampered[:-1] + ("A" if tampered[-1] != "A" else "B")
    resp = client.get(f"/gpt-actions/v1/slide-previews/{tampered}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PREVIEW_TOKEN_INVALID"

    import tv_app.application.services.data.slide_preview_token as token_mod

    token, exp = mint_slide_preview_token(
        playlist_id=str(uuid4()), slide_id=str(uuid4()), revision=1
    )
    monkeypatch.setattr(
        token_mod, "time", SimpleNamespace(time=lambda: exp + 3600)
    )
    resp = client.get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PREVIEW_TOKEN_EXPIRED"


def test_gpt_actions_rest_surface_still_protected():
    client = TestClient(app)
    assert client.get("/gpt-actions/v1/catalog").status_code == 401
    assert (
        client.post(
            "/gpt-actions/v1/changes/preview",
            json={"target": {}, "ops": []},
        ).status_code
        == 401
    )
    # Missing token: no usable route — the prefix exception does not create one.
    assert client.get("/gpt-actions/v1/slide-previews/").status_code in (401, 404)


# ------------------------------------------------------------------
# B. canonical_stage artifact — revision-bound, isolated, fail-closed
# ------------------------------------------------------------------


def _artifact_env(monkeypatch, tmp_path: Path, *, revision=5):
    """Slide + render service + dispatch writes for signed artifact fetches."""
    from tv_app.interface.http.routes import gpt_actions_routes as routes

    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    slide = {
        "id": str(slide_id),
        "title": "S1",
        "nativeConfig": _sample_native(),
        "slideType": "native",
    }
    monkeypatch.setattr(
        routes._dispatch,
        "_writes",
        _writes_for(playlist_id=playlist_id, slides=[slide], revision=revision),
    )
    return svc, playlist_id, slide_id, revision


def test_canonical_artifact_served_with_artifact_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    svc, playlist_id, slide_id, revision = _artifact_env(monkeypatch, tmp_path)
    artifact_png = _png(size=(16, 9))
    svc.store_rendered_png(
        slide_id=str(slide_id), revision=revision, png=artifact_png, width=16, height=9
    )
    token, _ = mint_slide_preview_token(
        playlist_id=str(playlist_id),
        slide_id=str(slide_id),
        revision=revision,
        artifact="canonical_stage",
    )
    resp = TestClient(app).get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 200, resp.text
    assert resp.content == artifact_png


def test_canonical_artifact_stale_revision_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    svc, playlist_id, slide_id, _revision = _artifact_env(
        monkeypatch, tmp_path, revision=9
    )
    # Artifact bound to OLD revision 5; playlist is now at 9.
    svc.store_rendered_png(
        slide_id=str(slide_id), revision=5, png=_png(), width=8, height=8
    )
    token, _ = mint_slide_preview_token(
        playlist_id=str(playlist_id),
        slide_id=str(slide_id),
        revision=5,
        artifact="canonical_stage",
    )
    resp = TestClient(app).get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PREVIEW_REVISION_STALE"


def test_canonical_artifact_missing_is_expired_not_schematic_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Artifact token must never silently serve the schematic render."""
    _svc, playlist_id, slide_id, revision = _artifact_env(monkeypatch, tmp_path)
    token, _ = mint_slide_preview_token(
        playlist_id=str(playlist_id),
        slide_id=str(slide_id),
        revision=revision,
        artifact="canonical_stage",
    )
    resp = TestClient(app).get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PREVIEW_ARTIFACT_EXPIRED"


def test_canonical_artifact_isolated_per_slide(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    svc, playlist_id, slide_id, revision = _artifact_env(monkeypatch, tmp_path)
    other_slide = uuid4()
    from tv_app.interface.http.routes import gpt_actions_routes as routes

    writes = routes._dispatch._writes
    writes.list_slides.return_value.append(
        {"id": str(other_slide), "title": "S2", "nativeConfig": {}, "slideType": "native"}
    )
    svc.store_rendered_png(
        slide_id=str(slide_id), revision=revision, png=_png(), width=8, height=8
    )
    token, _ = mint_slide_preview_token(
        playlist_id=str(playlist_id),
        slide_id=str(other_slide),
        revision=revision,
        artifact="canonical_stage",
    )
    resp = TestClient(app).get(f"/gpt-actions/v1/slide-previews/{token}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PREVIEW_ARTIFACT_EXPIRED"


# ------------------------------------------------------------------
# C. slidePreview.rendered contract (additive)
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


def test_include_preview_editor_closed_visual_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """VISTA_VISUAL_EDITOR_CLOSED — sem editor vivo do caller, a estrutura
    segue disponível e a evidência visual é unavailable/EDITOR_NOT_OPEN —
    mesmo com artifact cacheado de uma sessão anterior (page-close)."""
    svc = _patch_preview_service(monkeypatch, tmp_path)
    hub = _no_live_editor(monkeypatch)
    playlist_id, slide_id = uuid4(), uuid4()
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_id),
                "title": "S1",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            }
        ],
        revision=5,
    )
    # Artifact antigo existe, mas não há editor vivo → não é evidência visual.
    svc.store_rendered_png(
        slide_id=str(slide_id),
        revision=5,
        png=_png(size=(16, 9)),
        source="editor_live",
        client_id="c-old-session",
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    preview = out["slidePreview"]
    assert preview["kind"] == "schematic_layout"  # structural path preserved
    assert preview["previewUrl"]  # schematic signed URL still emitted
    assert out["layoutDigest"] is not None or "layoutDigest" in out
    rendered = preview["rendered"]
    assert rendered["kind"] == "canonical_stage"
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "EDITOR_NOT_OPEN"
    assert "previewUrl" not in rendered
    # Nenhuma captura foi pedida — não existe editor para atendê-la.
    hub.request_visual_capture.assert_not_called()


def test_include_preview_editor_open_capture_pending(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """VISTA_VISUAL_EDITOR_OPEN_CAPTURE_REQUEST — editor vivo + slide visível
    sem artifact: a API pede captura direcionada ao clientId do caller e
    responde pending/EDITOR_CAPTURE_PENDING; resend é bounded."""
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    live = _live_editor(
        monkeypatch, playlist_id=playlist_id, slide_id=slide_id, client_id="c-9"
    )
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_id),
                "title": "S1",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            }
        ],
        revision=5,
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "pending"
    assert rendered["failureCode"] == "EDITOR_CAPTURE_PENDING"
    live.hub.request_visual_capture.assert_called_once()
    kwargs = live.hub.request_visual_capture.call_args.kwargs
    assert kwargs["playlist_id"] == str(playlist_id)
    assert kwargs["user_id"] == "u1"
    assert kwargs["client_id"] == "c-9"
    assert kwargs["slide_id"] == str(slide_id)
    assert kwargs["revision"] == 5
    assert kwargs["request_id"]

    # Resend bounded: dentro da janela não reenvia o mesmo pedido.
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    assert out["slidePreview"]["rendered"]["status"] == "pending"
    assert live.hub.request_visual_capture.call_count == 1


def test_include_preview_wrong_slide_not_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Editor ao vivo focado no slide B; pedido de preview do slide A →
    EDITOR_SLIDE_NOT_OPEN, sem pedido de captura (nunca troca o slide)."""
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_a, slide_b = uuid4(), uuid4(), uuid4()
    live = _live_editor(
        monkeypatch, playlist_id=playlist_id, slide_id=slide_b
    )
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_a),
                "title": "A",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            },
            {
                "id": str(slide_b),
                "title": "B",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            },
        ],
        revision=5,
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_a)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "EDITOR_SLIDE_NOT_OPEN"
    live.hub.request_visual_capture.assert_not_called()


def test_include_preview_user_isolation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Foco de OUTRO usuário nunca satisfaz a verificação visual do caller."""
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    live = _live_editor(
        monkeypatch,
        actor="u2-other-user",
        playlist_id=playlist_id,
        slide_id=slide_id,
    )
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_id),
                "title": "S1",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            }
        ],
        revision=5,
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "EDITOR_NOT_OPEN"
    live.hub.request_visual_capture.assert_not_called()


def test_include_preview_rendered_ready_requires_editor_live(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """ready somente com artifact editor_live do clientId vivo e fresco.
    Artifact sem proveniência live → capture pending, não ready."""
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    live = _live_editor(
        monkeypatch, playlist_id=playlist_id, slide_id=slide_id, client_id="c-9"
    )
    slide = {
        "id": str(slide_id),
        "title": "S1",
        "nativeConfig": _sample_native(),
        "slideType": "native",
    }
    writes = _writes_for(playlist_id=playlist_id, slides=[slide], revision=5)
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )

    artifact_png = _png(size=(32, 18))
    svc.store_rendered_png(
        slide_id=str(slide_id),
        revision=5,
        png=artifact_png,
        width=32,
        height=18,
        source="editor_live",
        client_id="c-9",
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "ready"
    assert rendered["kind"] == "canonical_stage"
    assert rendered["source"] == "editor_live"
    assert rendered["revision"] == 5
    assert rendered["width"] == 32
    assert rendered["height"] == 18
    assert rendered["mimeType"] == "image/png"
    assert "slide-previews/" in rendered["previewUrl"]
    assert rendered["expiresAt"]
    live.hub.request_visual_capture.assert_not_called()  # artifact fresco — sem request
    # The minted URL actually serves the artifact bytes.
    token = rendered["previewUrl"].rsplit("/", 1)[-1]
    claims = parse_slide_preview_token(token)
    assert claims["artifact"] == "canonical_stage"
    assert claims["slideId"] == str(slide_id)

    # Artifact sem proveniência live nunca vira ready — novo pedido de captura.
    svc2 = _patch_preview_service(monkeypatch, tmp_path / "other")
    svc2.store_rendered_png(
        slide_id=str(slide_id), revision=5, png=artifact_png, width=32, height=18
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "pending"
    assert rendered["failureCode"] == "EDITOR_CAPTURE_PENDING"

    # Revision race: rev bump torna o artifact stale → capture pending (fail-closed).
    writes.get_revision.return_value = 6
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "pending"
    assert rendered["revision"] == 6


def test_include_preview_page_close_invalidates_visual(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """PAGE CLOSE — artifact ready com editor vivo; ao fechar a página o foco
    morre e o artifact cacheado deixa de ser evidência visual."""
    svc = _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    live = _live_editor(
        monkeypatch, playlist_id=playlist_id, slide_id=slide_id, client_id="c-9"
    )
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_id),
                "title": "S1",
                "nativeConfig": _sample_native(),
                "slideType": "native",
            }
        ],
        revision=5,
    )
    svc.store_rendered_png(
        slide_id=str(slide_id),
        revision=5,
        png=_png(size=(16, 9)),
        source="editor_live",
        client_id="c-9",
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    assert out["slidePreview"]["rendered"]["status"] == "ready"

    # Page close/socket drop → foco limpo + cliente não está mais vivo.
    live.store.clear_playlist_for_user("u1", str(playlist_id))
    live.hub.is_editor_client_live = lambda *a, **k: False
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "EDITOR_NOT_OPEN"
    # O PNG físico continua cacheado, mas não é mais evidência visual.
    assert svc.read_rendered_png(slide_id=str(slide_id), revision=5) is not None


def test_canonical_stage_image_requires_editor_live_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """MCP ImageContent — só projeta pixels quando rendered.status=ready E
    source=editor_live; artifact sem proveniência viva nunca vira imagem."""
    from tv_app.interface.mcp.tool_bridge import _canonical_stage_image

    svc = _patch_preview_service(monkeypatch, tmp_path)
    slide_id = str(uuid4())
    png = _png(size=(16, 9))
    svc.store_rendered_png(
        slide_id=slide_id,
        revision=5,
        png=png,
        source="editor_live",
        client_id="c-9",
    )

    def _data(source):
        return {
            "slidePreview": {
                "slideId": slide_id,
                "rendered": {
                    "kind": "canonical_stage",
                    "status": "ready",
                    "revision": 5,
                    "mimeType": "image/png",
                    "source": source,
                },
            }
        }

    image = _canonical_stage_image(_data("editor_live"))
    assert image is not None
    assert image.mime_type == "image/png"

    assert _canonical_stage_image(_data("editor_stage_capture")) is None
    assert _canonical_stage_image(_data("render_worker")) is None

    blocked = _data("editor_live")
    blocked["slidePreview"]["rendered"]["status"] = "unavailable"
    assert _canonical_stage_image(blocked) is None


def test_include_preview_rendered_external_slide_unsupported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _patch_preview_service(monkeypatch, tmp_path)
    playlist_id, slide_id = uuid4(), uuid4()
    writes = _writes_for(
        playlist_id=playlist_id,
        slides=[
            {
                "id": str(slide_id),
                "title": "Ext",
                "slideType": "external",
                "externalUrl": "https://example.test",
            }
        ],
        revision=3,
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    out = _context_with_preview(dispatch, playlist_id=playlist_id, slide_id=slide_id)
    rendered = out["slidePreview"]["rendered"]
    assert rendered["status"] == "unavailable"
    assert rendered["failureCode"] == "UNSUPPORTED_SLIDE_TYPE"


def test_rendered_store_roundtrip_and_prune_removes_sidecar(tmp_path: Path):
    svc = SlidePreviewRenderService(cache_dir=tmp_path)
    meta = svc.store_rendered_png(
        slide_id="s1", revision=7, png=PNG_BYTES, width=8, height=8
    )
    assert meta["kind"] == "canonical_stage"
    assert svc.read_rendered_png(slide_id="s1", revision=7) == PNG_BYTES
    read_meta = svc.rendered_artifact_meta(slide_id="s1", revision=7)
    assert read_meta and read_meta["revision"] == 7
    # Revision isolation: different revision never reads another artifact.
    assert svc.read_rendered_png(slide_id="s1", revision=8) is None
    # Pruning removes the .json sidecar together with the PNG.
    svc._prune_locked(max_files=0)
    assert svc.read_rendered_png(slide_id="s1", revision=7) is None
    assert svc.rendered_artifact_meta(slide_id="s1", revision=7) is None
    assert not list(tmp_path.glob("*.json"))


# ------------------------------------------------------------------
# E. VISTA intelligence — structural/data/visual levels are distinct
# ------------------------------------------------------------------
#
# NOTE: the `visual_verification` directive block was intentionally removed
# from vista_agent_intelligence.json by the content owner — no test asserts
# it here anymore.


# ------------------------------------------------------------------
# D. Producer upload endpoint — authenticated, edit-scoped, bounded
# ------------------------------------------------------------------


@pytest.fixture()
def upload_env(monkeypatch, tmp_path: Path):
    from delpi_auth.middleware import fastapi_auth as fa

    from tv_app.interface.http import playlist_access_http
    from tv_app.interface.http.routes import slide_routes

    monkeypatch.setattr(sec, "require_fresh_write_authorization", _real_sync_gate)
    monkeypatch.setattr(sec, "arequire_fresh_write_authorization", _real_async_gate)
    monkeypatch.setattr(
        fa, "validate_token", lambda token: {"sub": "user-1", "email": "u@delpi.local"}
    )

    async def _middleware_rbac(token, *, force_refresh=False):
        return _rbac()

    async def _async_rbac(token):
        return _rbac()

    monkeypatch.setattr(fa, "load_user_rbac", _middleware_rbac)
    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _async_rbac)

    state = SimpleNamespace(level="owner")
    monkeypatch.setattr(
        playlist_access_http._access,
        "resolve",
        lambda playlist_id, user: PlaylistAccess(
            level=state.level, playlist={"id": str(playlist_id)}
        ),
    )

    playlist_id, slide_id = uuid4(), uuid4()
    writes = MagicMock()
    writes.get_slide.return_value = {"id": str(slide_id)}
    writes.get_revision.return_value = 5
    monkeypatch.setattr(slide_routes, "_writes", writes)
    svc = _patch_preview_service(monkeypatch, tmp_path)

    state.client = TestClient(app)
    state.playlist_id = playlist_id
    state.slide_id = slide_id
    state.writes = writes
    state.svc = svc
    return state


_UPLOAD_PNG = _png(size=(16, 9))


def _put(upload_env, *, content=_UPLOAD_PNG, content_type="image/png", revision=5):
    return upload_env.client.put(
        f"/playlists/{upload_env.playlist_id}/slides/{upload_env.slide_id}"
        f"/rendered-preview?revision={revision}",
        headers={**AUTH, "Content-Type": content_type},
        content=content,
    )


def test_rendered_preview_upload_requires_auth(upload_env):
    resp = upload_env.client.put(
        f"/playlists/{upload_env.playlist_id}/slides/{upload_env.slide_id}"
        "/rendered-preview?revision=5",
        headers={"Content-Type": "image/png"},
        content=PNG_BYTES,
    )
    assert resp.status_code == 401


def test_rendered_preview_upload_success_stores_artifact(upload_env):
    resp = _put(upload_env)
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]
    assert data["status"] == "ready"
    assert data["kind"] == "canonical_stage"
    assert data["revision"] == 5
    assert (
        upload_env.svc.read_rendered_png(
            slide_id=str(upload_env.slide_id), revision=5
        )
        == _UPLOAD_PNG
    )


def test_rendered_preview_upload_wrong_mime_rejected(upload_env):
    resp = _put(upload_env, content_type="image/svg+xml")
    assert resp.status_code == 415


def test_rendered_preview_upload_invalid_png_rejected(upload_env):
    resp = _put(upload_env, content=b"not-a-png-at-all")
    assert resp.status_code == 422


def test_rendered_preview_upload_stale_revision_rejected(upload_env):
    resp = _put(upload_env, revision=4)
    assert resp.status_code == 409
    assert resp.json()["data"]["code"] == "PREVIEW_REVISION_STALE"


def test_rendered_preview_upload_oversized_rejected(upload_env, monkeypatch):
    from tv_app.interface.http.routes import slide_routes

    monkeypatch.setattr(slide_routes, "_RENDERED_PREVIEW_MAX_BYTES", 10)
    resp = _put(upload_env)
    assert resp.status_code == 413


def test_rendered_preview_upload_read_only_actor_denied(upload_env):
    upload_env.level = "viewer"
    resp = _put(upload_env)
    assert resp.status_code == 404  # fail-closed as not-found (no privilege leak)
    assert (
        upload_env.svc.read_rendered_png(
            slide_id=str(upload_env.slide_id), revision=5
        )
        is None
    )


# ------------------------------------------------------------------
# D2. Proveniência live — source=editor_live só com clientId do foco vivo
# ------------------------------------------------------------------


def _focus_upload_user(
    monkeypatch, upload_env, *, client_id="c-9", slide_id=None, stale=False
):
    """Foca o editor do usuário autenticado do upload_env (sub=user-1)."""
    from tv_app.application.services import editor_focus_store as efs_mod
    from tv_app.application.services.editor_focus_store import EditorFocusStore

    store = EditorFocusStore(ttl_seconds=15.0 if stale else 90.0)
    store.record(
        user_id="user-1",
        playlist_id=str(upload_env.playlist_id),
        slide_id=str(slide_id or upload_env.slide_id),
        client_id=client_id,
    )
    monkeypatch.setattr(efs_mod, "editor_focus_store", store)
    return store


def test_rendered_preview_upload_live_clientid_marks_editor_live(
    upload_env, monkeypatch
):
    _focus_upload_user(monkeypatch, upload_env, client_id="c-9")
    resp = upload_env.client.put(
        f"/playlists/{upload_env.playlist_id}/slides/{upload_env.slide_id}"
        "/rendered-preview?revision=5&clientId=c-9",
        headers={**AUTH, "Content-Type": "image/png"},
        content=_UPLOAD_PNG,
    )
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["source"] == "editor_live"
    meta = upload_env.svc.rendered_artifact_meta(
        slide_id=str(upload_env.slide_id), revision=5
    )
    assert meta["source"] == "editor_live"
    assert meta["clientId"] == "c-9"


def test_rendered_preview_upload_without_focus_not_live(upload_env, monkeypatch):
    """clientId fornecido sem foco vivo correspondente → artifact guardado,
    mas proveniência NÃO é editor_live (nunca satisfaz visual da VISTA)."""
    _focus_upload_user(monkeypatch, upload_env, client_id="c-other")
    resp = upload_env.client.put(
        f"/playlists/{upload_env.playlist_id}/slides/{upload_env.slide_id}"
        "/rendered-preview?revision=5&clientId=c-9",
        headers={**AUTH, "Content-Type": "image/png"},
        content=_UPLOAD_PNG,
    )
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["source"] == "editor_stage_capture"
    meta = upload_env.svc.rendered_artifact_meta(
        slide_id=str(upload_env.slide_id), revision=5
    )
    assert meta["source"] == "editor_stage_capture"
    assert meta["clientId"] is None


def test_rendered_preview_upload_wrong_slide_focus_not_live(
    upload_env, monkeypatch
):
    """Foco vivo em OUTRO slide → upload deste slide não ganha proveniência
    live (evita artifact do slide escondido mascarar-se como palco visível)."""
    _focus_upload_user(monkeypatch, upload_env, client_id="c-9", slide_id=uuid4())
    resp = upload_env.client.put(
        f"/playlists/{upload_env.playlist_id}/slides/{upload_env.slide_id}"
        "/rendered-preview?revision=5&clientId=c-9",
        headers={**AUTH, "Content-Type": "image/png"},
        content=_UPLOAD_PNG,
    )
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["source"] == "editor_stage_capture"
