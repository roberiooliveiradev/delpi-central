"""PHASE 4 — Editor Grounding V2 regression suite.

Covers the §34 contract:
- editorFocus.selectionState (ACTIVE|STALE|ABSENT|AMBIGUOUS)
- editorFocus.selectedObjects[] resolved from persisted slide state
- editorFocus.missingIds[] for unresolved selected ids
- suggest_change server-focus fallback (omitted-only, explicit wins)
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.services.data.presentation_command_planner_service import (
    PresentationCommandPlannerService,
)
from tv_app.application.services.editor_focus_store import EditorFocusStore

PLAYLIST_ID = str(uuid4())
SLIDE_ID = str(uuid4())
OTHER_SLIDE_ID = str(uuid4())

_NATIVE = {
    "version": 1,
    "blocks": [
        {
            "id": "blk-head",
            "type": "heading",
            "content": "Vendas do mês",
            "frame": {"x": 0, "y": 0, "w": 100, "h": 30},
        },
        {
            "id": "blk-text",
            "type": "text",
            "content": "Lorem ipsum",
            "frame": {"x": 0, "y": 40, "w": 100, "h": 60},
        },
        {
            "id": "blk-chart",
            "type": "chart_view",
            "modelId": "mdl-1",
            "dataSourceId": "ds-1",
            "frame": {"x": 0, "y": 120, "w": 60, "h": 60},
        },
        {
            "id": "blk-kpi",
            "type": "kpi_view",
            "dataSourceId": "ds-1",
            "textProjection": {"field": "valor"},
            "frame": {"x": 60, "y": 120, "w": 40, "h": 30},
        },
        {
            "id": "blk-table",
            "type": "table_view",
            "modelId": "mdl-2",
            "frame": {"x": 0, "y": 190, "w": 100, "h": 100},
        },
    ],
}

_OTHER_NATIVE = {
    "version": 1,
    "blocks": [
        {
            "id": "blk-other",
            "type": "text",
            "content": "other slide",
            "frame": {"x": 0, "y": 0, "w": 10, "h": 10},
        },
    ],
}


def _writes():
    writes = MagicMock()
    writes.get_playlist.return_value = {
        "id": PLAYLIST_ID,
        "name": "TV",
        "dataDefaults": {},
    }
    writes.list_slides.return_value = [
        {"id": SLIDE_ID, "title": "A", "sortOrder": 0, "nativeConfig": _NATIVE},
        {
            "id": OTHER_SLIDE_ID,
            "title": "B",
            "sortOrder": 1,
            "nativeConfig": _OTHER_NATIVE,
        },
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 7
    writes.get_slide.side_effect = lambda slide_id, *, playlist_id: next(
        s for s in writes.list_slides.return_value if s["id"] == str(slide_id)
    )
    return writes


def _dispatch(writes) -> GptActionsDispatchService:
    return GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )


def _user(uid: str = "u1"):
    return SimpleNamespace(is_superadmin=True, permissions=[], id=uid)


def _access_ok():
    return SimpleNamespace(
        can_read=True,
        can_edit=True,
        level="owner",
        playlist={"id": PLAYLIST_ID, "name": "TV", "dataDefaults": {}},
    )


def _store_with(
    *, uid: str = "u1", selected: list[str] | None = None, stale: bool = False,
    slide_id: str = SLIDE_ID, playlist_id: str = PLAYLIST_ID,
) -> EditorFocusStore:
    store = EditorFocusStore(ttl_seconds=90)
    store.record(
        user_id=uid,
        playlist_id=playlist_id,
        slide_id=slide_id,
        selected_ids=selected or [],
    )
    if stale:
        with store._lock:
            store._by_user[uid]["_mono"] = time.monotonic() - 120
    return store


def _ctx(dispatch, store, *, uid: str = "u1", can_read: bool = True):
    access = _access_ok()
    if not can_read:
        access = SimpleNamespace(
            can_read=False, can_edit=False, level=None, playlist=None
        )
    return (
        patch.object(dispatch._access, "resolve", return_value=access),
        patch.object(dispatch._access, "actor_id", return_value=uid),
        patch.object(dispatch, "_actor", return_value=uid),
        patch(
            "tv_app.application.services.editor_focus_store.editor_focus_store",
            store,
        ),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
    )


def _focused_ctx(dispatch, store, *, uid: str = "u1", preview_slide_id=None):
    patches = _ctx(dispatch, store, uid=uid)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        return dispatch.get_playlist_context(
            user=_user(uid),
            playlist_id=PLAYLIST_ID,
            scope="editorFocus",
            preview_slide_id=preview_slide_id,
        )


# ------------------------------------------------------------------
# Projection: selectionState / selectedObjects / missingIds
# ------------------------------------------------------------------


def test_projection_fresh_single_selection_is_active():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "ACTIVE"
    assert [o["id"] for o in focus["selectedObjects"]] == ["blk-head"]
    assert focus["selectedObjects"][0]["type"] == "heading"
    assert focus["missingIds"] == []


def test_projection_no_selection_is_absent():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=[])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "ABSENT"
    assert focus["selectedObjects"] == []
    assert focus["missingIds"] == []


def test_projection_stale_selection_reresolves_persisted_object():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"], stale=True)
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["stale"] is True
    assert focus["selectionState"] == "STALE"
    assert [o["id"] for o in focus["selectedObjects"]] == ["blk-head"]
    assert focus["missingIds"] == []


def test_projection_deleted_block_goes_to_missing_ids():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-gone"])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "ABSENT"
    assert focus["selectedObjects"] == []
    assert focus["missingIds"] == ["blk-gone"]


def test_projection_multi_selection_is_ambiguous():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head", "blk-text"])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "AMBIGUOUS"
    assert [o["id"] for o in focus["selectedObjects"]] == ["blk-head", "blk-text"]
    assert focus["missingIds"] == []


def test_projection_partial_missing_selection():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head", "blk-gone"])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "ACTIVE"
    assert [o["id"] for o in focus["selectedObjects"]] == ["blk-head"]
    assert focus["missingIds"] == ["blk-gone"]


def test_projection_slide_drift_resolves_against_authoritative_detail():
    # Focus points to slide A selecting blk-head; preview_slide_id forces
    # detail slide B — persisted detail wins, blk-head lands in missingIds.
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    out = _focused_ctx(dispatch, store, preview_slide_id=OTHER_SLIDE_ID)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "ABSENT"
    assert focus["missingIds"] == ["blk-head"]


def test_projection_data_bound_visual_includes_binding_fields():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-chart"])
    out = _focused_ctx(dispatch, store)
    obj = out["editorFocus"]["selectedObjects"][0]
    assert obj["type"] == "chart_view"
    assert obj["modelId"] == "mdl-1"
    assert obj["dataSourceId"] == "ds-1"


def test_projection_kpi_and_table_types():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-kpi", "blk-table"])
    out = _focused_ctx(dispatch, store)
    focus = out["editorFocus"]
    assert focus["selectionState"] == "AMBIGUOUS"
    types = {o["id"]: o["type"] for o in focus["selectedObjects"]}
    assert types == {"blk-kpi": "kpi_view", "blk-table": "table_view"}
    assert focus["selectedObjects"][0]["bindingField"] == "valor"


def test_projection_no_focus_record_omits_editor_focus():
    dispatch = _dispatch(_writes())
    store = EditorFocusStore(ttl_seconds=90)
    out = _focused_ctx(dispatch, store)
    assert "editorFocus" not in out


def test_projection_selected_objects_are_compact_not_full_blocks():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    out = _focused_ctx(dispatch, store)
    obj = out["editorFocus"]["selectedObjects"][0]
    forbidden = {"content", "style", "nativeConfig", "resolved", "contentRuns"}
    assert not (forbidden & set(obj))


def test_projection_focus_from_other_playlist_ignored():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"], playlist_id=str(uuid4()))
    out = _focused_ctx(dispatch, store)
    assert "editorFocus" not in out


# ------------------------------------------------------------------
# suggest_change focus fallback
# ------------------------------------------------------------------


def _suggest(dispatch, store, *, message, host, uid: str = "u1", can_read=True):
    patches = _ctx(dispatch, store, uid=uid, can_read=can_read)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        return dispatch.suggest_change(
            user=_user(uid),
            message=message,
            host_context=host,
            authorization=None,
        )


def _captured_host(dispatch, store, *, message, host):
    captured = {}
    real_plan = PresentationCommandPlannerService.plan

    def _capture(*, message, host_context, authorization=None, user=None):
        captured["host"] = dict(host_context or {})
        return real_plan(
            message=message,
            host_context=host_context,
            authorization=authorization,
            user=user,
        )

    patches = _ctx(dispatch, store)
    with (
        patches[0], patches[1], patches[2], patches[3], patches[4],
        patch.object(
            PresentationCommandPlannerService, "plan", side_effect=_capture
        ),
    ):
        dispatch.suggest_change(
            user=_user("u1"),
            message=message,
            host_context=host,
            authorization=None,
        )
    return captured["host"]


def test_suggest_omitted_selection_uses_focus_fallback():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    delete = next(op for op in result["ops"] if op.get("op") == "delete_block")
    assert delete["blockId"] == "blk-head"


def test_suggest_fallback_injects_slide_id_when_omitted():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    host = _captured_host(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert host["slideId"] == SLIDE_ID
    assert host["selectedBlockIds"] == ["blk-head"]
    assert host["selectedBlockTypes"] == ["heading"]


def test_suggest_explicit_host_context_wins():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={
            "playlistId": PLAYLIST_ID,
            "slideId": SLIDE_ID,
            "selectedBlockIds": ["explicit-blk"],
        },
    )
    delete = next(op for op in result["ops"] if op.get("op") == "delete_block")
    assert delete["blockId"] == "explicit-blk"


def test_suggest_explicit_empty_selection_does_not_resurrect_focus():
    # OMITTED != EMPTY — an explicit [] means the host deliberately
    # reports no selection; server focus must not fill it.
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID, "selectedBlockIds": []},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_no_focus_no_selection_clarifies():
    dispatch = _dispatch(_writes())
    store = EditorFocusStore(ttl_seconds=90)
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_create_remains_create_with_focus():
    # Selection present (fallback) + CREATE intent — typed create, no ALTER.
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store,
        message="Crie um novo bloco de texto",
        host={"playlistId": PLAYLIST_ID},
    )
    assert result["ops"] == [{"op": "create_block", "type": "text"}]
    assert all(op.get("op") != "upsert_block" for op in result["ops"])


def test_suggest_alter_targets_focus_heading_same_object():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store,
        message="Aumente a fonte do título para 56",
        host={"playlistId": PLAYLIST_ID},
    )
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    assert upsert["blockId"] == "blk-head"
    assert upsert["block"].get("createIfMissing") is not True
    assert upsert["block"]["type"] == "heading"


def test_suggest_stale_focus_reresolves_surviving_objects():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"], stale=True)
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    delete = next(op for op in result["ops"] if op.get("op") == "delete_block")
    assert delete["blockId"] == "blk-head"


def test_suggest_deleted_target_no_fallback():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-gone"])
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_explicit_slide_scope_not_retargeted():
    # Focus on slide A but explicit slideId=B — fallback must not move scope.
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"], slide_id=SLIDE_ID)
    result = _suggest(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID, "slideId": OTHER_SLIDE_ID},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_focus_user_isolation():
    # Focus recorded for u1 must not become grounding for u2.
    dispatch = _dispatch(_writes())
    store = _store_with(uid="u1", selected=["blk-head"])
    result = _suggest(
        dispatch, store, uid="u2",
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_unreadable_playlist_no_fallback():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    result = _suggest(
        dispatch, store, can_read=False,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSelection"


def test_suggest_multi_selection_fallback_injects_all_resolved():
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head", "blk-text", "blk-gone"])
    host = _captured_host(
        dispatch, store,
        message="apague o bloco",
        host={"playlistId": PLAYLIST_ID},
    )
    assert host["selectedBlockIds"] == ["blk-head", "blk-text"]
    assert "blk-gone" not in host["selectedBlockIds"]
    assert host["selectedBlockTypes"] == ["heading", "text"]


def test_suggest_no_playlist_id_no_fallback():
    # Without playlist scope there is no approved target scope to ground in.
    dispatch = _dispatch(_writes())
    store = _store_with(selected=["blk-head"])
    host = _captured_host(
        dispatch, store,
        message="apague o bloco",
        host={},
    )
    assert host == {}
