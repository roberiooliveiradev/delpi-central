"""B1 — capability expansion through the six semantic verbs.

New typed ops (update_playlist, activate_playlist, deactivate_playlist,
duplicate_slide, reorder_sections) flow through ``execute`` PREPARE->COMMIT;
new reads (slide_preset.list, media_asset.list) flow through ``read``.
Surface stays exactly six tools — no new MCP tool was created.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from test_vista_mcp_write_surface import (
    _access_patches,
    _ctx,
    _editor,
    _governed_dispatch,
    _preview_result,
    _viewer,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError,
)


def _stub_readbacks(writes, playlist_id):
    """Post-commit authoritative read-back mocks (canonical commit service)."""
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.get_playlist.return_value = {"id": playlist_id}
    writes.list_slides.return_value = []
    writes.list_sections.return_value = []


def _run_commit(dispatch, writes, user, playlist_id, ops, key, stubs=None):
    """prepare -> commit through the semantic execute verb."""
    _stub_readbacks(writes, playlist_id)
    if callable(stubs):
        stubs()
    with _ctx(user), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService, "preview", return_value=_preview_result(orderedOps=ops, appliedOps=[o.get("op") for o in ops])
    ):
        prepared = tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="prepare",
            target={"playlistId": playlist_id}, operations=ops)
        assert prepared.is_error is False
        handle = prepared.structured_content["data"]["proposal_handle"]
        return tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="commit",
            proposal_handle=handle, idempotency_key=key)


# ---------------------------------------------------------------------------
# Surface invariant
# ---------------------------------------------------------------------------


def test_surface_still_six_tools():
    assert MCP_TOOL_NAMES == (
        "get_context", "read", "analyze", "knowledge", "execute", "delete")


# ---------------------------------------------------------------------------
# B1.1 update_playlist
# ---------------------------------------------------------------------------


def test_update_playlist_commits_repo_fields():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    
    writes.update_playlist.return_value = {"id": playlist_id,
                                "name": "Painel Operacional"}
    ops = [{"op": "update_playlist",
            "name": "Painel Operacional",
            "defaultDurationSec": 15,
            "transitionStyle": "fade",
            "playbackMode": "presentation"}]
    result = _run_commit(
        dispatch, writes, user, playlist_id, ops, "k-upd-1",
        stubs=lambda: setattr(
            writes.get_playlist, "return_value",
            {"id": playlist_id, "name": "Painel Operacional",
             "defaultDurationSec": 15, "transitionStyle": "fade",
             "playbackMode": "presentation"}))
    assert result.is_error is False
    assert result.structured_content["data"]["status"] == "VERIFIED"
    kwargs = writes.update_playlist.call_args.kwargs
    assert kwargs["name"] == "Painel Operacional"
    assert kwargs["default_duration_sec"] == 15
    assert kwargs["transition_style"] == "fade"
    assert kwargs["playback_mode"] == "presentation"


def test_update_playlist_empty_fields_fails():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        side_effect=PresentationPatchError("update_playlist exige campo."),
    ):
        result = tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="prepare",
            target={"playlistId": str(uuid4())},
            operations=[{"op": "update_playlist"}])
    assert result.is_error is True
    assert result.structured_content["httpStatus"] in (400, 409, 422)
    assert writes.method_calls == []


# ---------------------------------------------------------------------------
# B1.2 activate / deactivate playlist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_name,expected", [
    ("activate_playlist", True),
    ("deactivate_playlist", False),
])
def test_toggle_playlist_active_commits(op_name, expected):
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    
    writes.set_playlist_active.return_value = {"id": playlist_id, "isActive": expected}
    result = _run_commit(dispatch, writes, user, playlist_id,
                         [{"op": op_name}], f"k-{op_name}",
                         stubs=lambda: setattr(
                             writes.get_playlist, "return_value",
                             {"id": playlist_id, "isActive": expected}))
    assert result.is_error is False
    kwargs = writes.set_playlist_active.call_args.kwargs
    assert kwargs["is_active"] is expected


def test_toggle_requires_write_permission():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="prepare",
            target={"playlistId": str(uuid4())},
            operations=[{"op": "activate_playlist"}])
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 403
    assert writes.method_calls == []


# ---------------------------------------------------------------------------
# B1.3 duplicate_slide
# ---------------------------------------------------------------------------


def test_duplicate_slide_commits_copy():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    user = _editor()
    
    writes.duplicate_slide.return_value = {
        "id": str(uuid4()), "title": "T (cópia)"}
    new_id = writes.duplicate_slide.return_value["id"]
    result = _run_commit(dispatch, writes, user, playlist_id,
                         [{"op": "duplicate_slide", "slideId": slide_id}],
                         "k-dup-1",
                         stubs=lambda: setattr(
                             writes.list_slides, "return_value",
                             [{"id": slide_id}, {"id": new_id}]))
    assert result.is_error is False
    args = writes.duplicate_slide.call_args.args
    assert str(args[1]) == slide_id


def test_duplicate_slide_requires_slide_id():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        side_effect=PresentationPatchError("missingTarget"),
    ):
        result = tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="prepare",
            target={"playlistId": str(uuid4())},
            operations=[{"op": "duplicate_slide"}])
    assert result.is_error is True
    assert writes.method_calls == []


# ---------------------------------------------------------------------------
# B1.4 reorder_sections
# ---------------------------------------------------------------------------


def test_reorder_sections_commits():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    
    s1, s2 = str(uuid4()), str(uuid4())
    writes.reorder_sections.return_value = [{"id": s1}, {"id": s2}]
    ops = [{"op": "reorder_sections",
            "items": [{"id": s1, "sortOrder": 0},
                      {"id": s2, "sortOrder": 1}]}]
    result = _run_commit(dispatch, writes, user, playlist_id, ops, "k-rs-1",
                         stubs=lambda: setattr(
                             writes.list_sections, "return_value",
                             [{"id": s1, "sortOrder": 0},
                              {"id": s2, "sortOrder": 1}]))
    assert result.is_error is False
    items = writes.reorder_sections.call_args.args[1]
    assert items[0]["id"] == s1 and items[0]["sortOrder"] == 0


def test_reorder_sections_bad_items_fails():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        side_effect=PresentationPatchError("reorderItemsRequired"),
    ):
        result = tool_bridge.tool_execute(
            entity="presentation", action="apply_mutation", phase="prepare",
            target={"playlistId": str(uuid4())},
            operations=[{"op": "reorder_sections", "items": []}])
    assert result.is_error is True
    assert writes.method_calls == []


# ---------------------------------------------------------------------------
# B1.5 read.slide_preset.list + read.media_asset.list
# ---------------------------------------------------------------------------


def test_read_slide_preset_list():
    dispatch, _, _ = _governed_dispatch()
    fake = [{"presetKey": "kpi_basic", "title": "KPI básico"}]
    with _ctx(_viewer()), patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch(
        "tv_app.application.services.slide_preset_service.list_slide_presets",
        return_value=fake,
    ):
        result = tool_bridge.tool_read(entity="slide_preset", action="list")
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["count"] == 1
    assert data["items"][0]["presetKey"] == "kpi_basic"


def test_read_media_asset_list():
    dispatch, _, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    fake = [{"id": "a1", "mediaKind": "image", "url": "/m/a1"}]
    with _ctx(_viewer()), patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch(
        "tv_app.infrastructure.persistence.repositories.media_repository."
        "MediaRepository.list_for_playlist",
        return_value=fake,
    ):
        result = tool_bridge.tool_read(
            entity="media_asset", action="list", ref=playlist_id,
            filters={"mediaKind": "image"})
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["count"] == 1
    assert data["playlistId"] == playlist_id


def test_read_media_asset_requires_playlist_ref():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_read(entity="media_asset", action="list")
    assert result.is_error is True
    assert result.structured_content["code"] == "VALIDATION_ERROR"


def test_read_media_asset_rejects_unknown_filter():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_read(
            entity="media_asset", action="list", ref=str(uuid4()),
            filters={"evil": True})
    assert result.is_error is True
    assert result.structured_content["code"] in (
        "VALIDATION_ERROR", "UNKNOWN_FILTER")
