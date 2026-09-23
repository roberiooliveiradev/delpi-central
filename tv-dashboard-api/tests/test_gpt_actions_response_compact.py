"""GPT Actions READ response compaction + byte budget."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES,
    project_playlist_list_item,
    utf8_size,
)
from tv_app.application.services.editor_focus_store import EditorFocusStore


def test_list_item_projection_omits_cover_and_native():
    raw = {
        "id": str(uuid4()),
        "name": "TV PRODUÇÃO",
        "description": "x",
        "isActive": True,
        "revision": 3,
        "updatedAt": "2026-01-01T00:00:00Z",
        "viewportProfile": "full_hd",
        "coverSlide": {"id": "s1", "nativeConfig": {"blocks": [{"type": "kpi_view"}] * 20}},
        "publicToken": "tok",
        "dataDefaults": {"branch": "01"},
        "masterConfig": {"huge": "x" * 5000},
    }
    row = project_playlist_list_item(raw, access_role="owner")
    assert row["name"] == "TV PRODUÇÃO"
    assert "coverSlide" not in row
    assert "coverLayoutDigest" not in row
    assert "publicToken" not in row
    assert "masterConfig" not in row
    assert row["hasDataDefaults"] is True


def test_list_playlists_compact_and_editor_focus_first():
    store = EditorFocusStore(ttl_seconds=90)
    pid = str(uuid4())
    sid = str(uuid4())
    store.record(user_id="u1", playlist_id=pid, slide_id=sid, selected_ids=["b1"])

    repo = MagicMock()
    heavy_cover = {
        "id": "c1",
        "nativeConfig": {"blocks": [{"type": "kpi_view", "frame": {"x": 0}}] * 30},
    }
    repo.list_playlists.return_value = [
        {
            "id": pid,
            "name": f"P{i}",
            "ownerUserId": "u1",
            "revision": 1,
            "coverSlide": heavy_cover,
            "publicToken": "t",
            "masterConfig": {"x": "y" * 2000},
        }
        for i in range(40)
    ]
    repo.get_share_role.return_value = None
    dispatch = GptActionsDispatchService(
        repo=repo, writes=MagicMock(), commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with (
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.services.editor_focus_store.editor_focus_store",
            store,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
    ):
        out = dispatch.list_playlists(user=user, limit=50)

    assert list(out.keys())[0] == "editorFocus"
    assert out["editorFocus"]["playlistId"] == pid
    assert out["editorFocus"]["slideId"] == sid
    assert len(out["items"]) == 40
    assert "coverSlide" not in out["items"][0]
    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_get_playlist_context_index_plus_focused_slide():
    writes = MagicMock()
    playlist_id = str(uuid4())
    s1 = str(uuid4())
    s2 = str(uuid4())
    heavy = {
        "version": 5,
        "blocks": [
            {
                "id": f"b{i}",
                "type": "kpi_view",
                "frame": {"x": 1, "y": 1, "w": 20, "h": 20},
                "resolved": {"rows": [{"v": j} for j in range(50)]},
            }
            for i in range(8)
        ],
    }
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "TV",
        "dataDefaults": {},
        "publicToken": "tok",
        "masterConfig": {"a": 1},
    }
    writes.list_slides.return_value = [
        {"id": s1, "title": "A", "sortOrder": 0, "nativeConfig": heavy},
        {"id": s2, "title": "B", "sortOrder": 1, "nativeConfig": heavy},
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 9
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")
    store = EditorFocusStore(ttl_seconds=90)
    store.record(user_id="u1", playlist_id=playlist_id, slide_id=s2)

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "TV", "dataDefaults": {}},
            ),
        ),
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.services.editor_focus_store.editor_focus_store",
            store,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_brand_assets",
            return_value={},
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_playlist_assets",
            return_value=[],
        ),
    ):
        out = dispatch.get_playlist_context(user=user, playlist_id=playlist_id)

    assert out["editorFocus"]["slideId"] == s2
    assert out["focusedSlideId"] == s2
    assert "nativeConfig" not in out["slides"][0]
    assert out["focusedSlide"]["nativeConfig"]["blocks"][0].get("resolved") is None
    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES
