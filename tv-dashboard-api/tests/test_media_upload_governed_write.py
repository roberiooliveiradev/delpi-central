"""Regression: media uploads (editor paste + media library) through the real
governed-write gate.

Async route handlers must use the async gate twin: the sync gate runs
``asyncio.run`` and fails inside the server event loop, which surfaced as
503 ``AUTHZ_UNAVAILABLE`` on every image upload. These tests restore the real
gate (the autouse conftest seam replaces it) and drive the HTTP surface the
MFE client ``uploadPlaylistMedia`` uses: direct ``POST /media`` and the
chunked ``/media/uploads`` session.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import tv_app.core.security as sec
from tv_app.application.services.media_chunked_upload_service import (
    MediaChunkedUploadService,
)
from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.core.security import (
    arequire_fresh_write_authorization as _real_async_gate,
)
from tv_app.core.security import (
    require_fresh_write_authorization as _real_sync_gate,
)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f"
    b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)
AUTH = {"Authorization": "Bearer tok-user"}


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


def _asset(**kwargs) -> dict:
    return {
        "id": str(uuid4()),
        "playlistId": str(kwargs.get("playlist_id")),
        "storedName": kwargs.get("stored_name"),
        "originalName": kwargs.get("original_name"),
        "mimeType": kwargs.get("mime_type"),
        "mediaKind": kwargs.get("media_kind"),
        "fileSizeBytes": kwargs.get("file_size_bytes"),
        "createdBy": kwargs.get("created_by"),
    }


@pytest.fixture()
def env(monkeypatch, tmp_path: Path):
    from delpi_auth.middleware import fastapi_auth as fa

    from tv_app.interface.http import playlist_access_http
    from tv_app.interface.http.routes import media_routes
    from tv_app.main import app

    monkeypatch.setattr(sec, "require_fresh_write_authorization", _real_sync_gate)
    monkeypatch.setattr(sec, "arequire_fresh_write_authorization", _real_async_gate)
    monkeypatch.setattr(
        fa, "validate_token", lambda token: {"sub": "user-1", "email": "u@delpi.local"}
    )

    async def _middleware_rbac(token, *, force_refresh=False):
        return _rbac()

    monkeypatch.setattr(fa, "load_user_rbac", _middleware_rbac)

    state = SimpleNamespace(fresh_calls=[], fresh=_rbac(), fresh_error=None, level="owner")

    async def _fresh(token):
        state.fresh_calls.append(token)
        if state.fresh_error is not None:
            raise state.fresh_error
        return state.fresh

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fresh)

    def _resolve(playlist_id, user):
        return PlaylistAccess(level=state.level, playlist={"id": str(playlist_id)})

    monkeypatch.setattr(playlist_access_http._access, "resolve", _resolve)

    from tv_app.config import settings

    monkeypatch.setattr(settings, "TV_DASHBOARD_MEDIA_UPLOAD_DIR", str(tmp_path))
    storage = MediaStorageService(base_dir=str(tmp_path))
    repo = MagicMock()
    repo.create.side_effect = lambda **kw: _asset(**kw)
    monkeypatch.setattr(media_routes, "_storage", storage)
    monkeypatch.setattr(media_routes, "_chunked", MediaChunkedUploadService(storage=storage))
    monkeypatch.setattr(media_routes, "_media_repo", repo)
    monkeypatch.setattr(media_routes, "notify_presentation_changed", lambda **_: None)
    monkeypatch.setattr(
        media_routes, "apply_video_optimize_after_create", lambda *, asset, **_: asset
    )

    state.client = TestClient(app)
    state.repo = repo
    state.storage = storage
    state.tmp = tmp_path
    return state


def _stored_files(tmp: Path) -> list[Path]:
    return [p for p in tmp.iterdir() if p.is_file()]


def _post_image(env, playlist_id, *, headers=AUTH, name="clipboard.png", mime="image/png", data=PNG_BYTES):
    return env.client.post(
        f"/playlists/{playlist_id}/media",
        headers=headers,
        files={"file": (name, data, mime)},
    )


def test_paste_image_upload_succeeds_through_real_gate(env):
    playlist_id = uuid4()
    resp = _post_image(env, playlist_id)

    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["mediaKind"] == "image"
    assert body["data"]["mimeType"] == "image/png"
    assert body["data"]["createdBy"] == "user-1"
    assert env.fresh_calls == ["tok-user"]
    env.repo.create.assert_called_once()
    stored = env.repo.create.call_args.kwargs["stored_name"]
    assert env.storage.read(stored) == PNG_BYTES


def test_library_chunked_upload_succeeds_through_real_gate(env):
    playlist_id = uuid4()
    session = env.client.post(
        f"/playlists/{playlist_id}/media/uploads",
        headers=AUTH,
        json={"originalName": "biblioteca.png", "mimeType": "image/png", "sizeBytes": len(PNG_BYTES)},
    )
    assert session.status_code == 201, session.json()
    upload_id = session.json()["data"]["uploadId"]

    chunk = env.client.put(
        f"/playlists/{playlist_id}/media/uploads/{upload_id}/chunks/0",
        headers={**AUTH, "Content-Type": "application/octet-stream"},
        content=PNG_BYTES,
    )
    assert chunk.status_code == 200, chunk.json()

    done = env.client.post(
        f"/playlists/{playlist_id}/media/uploads/{upload_id}/complete", headers=AUTH
    )
    assert done.status_code == 201, done.json()
    assert done.json()["data"]["originalName"] == "biblioteca.png"
    assert len(env.fresh_calls) == 3
    stored = env.repo.create.call_args.kwargs["stored_name"]
    assert env.storage.read(stored) == PNG_BYTES


def test_upload_without_playlist_edit_access_is_denied(env):
    env.level = "viewer"
    resp = _post_image(env, uuid4())

    assert resp.status_code == 404
    assert resp.json()["success"] is False
    env.repo.create.assert_not_called()
    assert _stored_files(env.tmp) == []


def test_upload_with_revoked_write_permission_is_denied(env):
    env.fresh = _rbac(permissions=["tv-dashboard.read"])
    resp = _post_image(env, uuid4())

    assert resp.status_code == 403
    env.repo.create.assert_not_called()
    assert _stored_files(env.tmp) == []


def test_upload_fails_closed_when_core_is_unavailable(env):
    env.fresh_error = RuntimeError("RBAC lookup failed with status 503")
    resp = _post_image(env, uuid4())

    assert resp.status_code == 503
    assert resp.json()["success"] is False
    env.repo.create.assert_not_called()
    assert _stored_files(env.tmp) == []


def test_chunk_and_complete_fail_closed_when_core_is_unavailable(env):
    playlist_id = uuid4()
    env.fresh_error = RuntimeError("core down")
    chunk = env.client.put(
        f"/playlists/{playlist_id}/media/uploads/u-1/chunks/0",
        headers={**AUTH, "Content-Type": "application/octet-stream"},
        content=PNG_BYTES,
    )
    done = env.client.post(f"/playlists/{playlist_id}/media/uploads/u-1/complete", headers=AUTH)

    assert chunk.status_code == 503
    assert done.status_code == 503
    env.repo.create.assert_not_called()


def test_upload_without_bearer_is_unauthorized(env):
    resp = _post_image(env, uuid4(), headers={})

    assert resp.status_code == 401
    assert env.fresh_calls == []
    env.repo.create.assert_not_called()


def test_upload_rejects_disallowed_media_type(env):
    resp = _post_image(env, uuid4(), name="run.exe", mime="application/x-msdownload", data=b"MZ")

    assert resp.status_code == 422
    env.repo.create.assert_not_called()
    assert _stored_files(env.tmp) == []


_WRITE_GATES_SYNC = {"require_playlist_access", "require_governed_write", "require_fresh_write_authorization"}


def test_async_route_handlers_never_call_sync_write_gate():
    routes_dir = Path(__file__).resolve().parents[1] / "tv_app" / "interface" / "http" / "routes"
    offenders: list[str] = []
    for path in sorted(routes_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.AsyncFunctionDef):
                continue
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name not in _WRITE_GATES_SYNC:
                    continue
                need = next((k.value for k in node.keywords if k.arg == "need"), None)
                if isinstance(need, ast.Constant) and need.value == "read":
                    continue
                offenders.append(f"{path.name}:{node.lineno} {fn.name} -> {name}")
    assert offenders == [], offenders
