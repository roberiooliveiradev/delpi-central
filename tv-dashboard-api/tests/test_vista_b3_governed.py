"""B3 — governed deletes & history restore via the six semantic verbs.

delete.playlist (sealed proposal + A5 consent), delete.data_model
(sealed presentation pipeline, confirm policy), and
execute.playlist_history.restore (CAS-guarded canonical workflow).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from test_vista_mcp_write_surface import (
    _access_patches,
    _ctx,
    _editor,
    _governed_dispatch,
    _preview_result,
    _viewer,
    reset_proposal_store_for_tests,
)
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchService,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES

LIFECYCLE = "tv_app.application.services.playlist_lifecycle_service"


def _consent_mock():
    import time

    c = MagicMock()
    c.issue_for_proposal.return_value = {
        "challenge_id": "chal-1",
        "status": "PENDING",
        "action": "delete.playlist",
        "target_ref": "p1",
        "origin": "mcp",
        "created_at": time.time(),
        "approved_at": None,
        "expires_at": time.time() + 600,
    }
    c.verify_for_commit.return_value = {
        "challenge_id": "chal-1", "status": "APPROVED"}
    return c


def test_surface_still_six_tools():
    assert MCP_TOOL_NAMES == (
        "get_context", "read", "analyze", "knowledge", "execute", "delete")


# ---------------------------------------------------------------------------
# delete.playlist
# ---------------------------------------------------------------------------


def test_delete_playlist_prepare_commit_verified():
    reset_proposal_store_for_tests()
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid = str(uuid4())
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": pid, "name": "P"}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistRepository", return_value=repo), \
            patch(f"{LIFECYCLE}.notify_presentation_changed"):
        p = tool_bridge.tool_delete(
            entity="playlist", phase="prepare",
            target={"playlistId": pid})
        assert p.is_error is False
        data = p.structured_content["data"]
        assert data["status"] == "consent_required"
        handle = data["proposal_handle"]
        r = tool_bridge.tool_delete(
            entity="playlist", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1", target_echo=pid)
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    assert repo.delete.called
    reset_proposal_store_for_tests()


def test_delete_playlist_wrong_echo_rejected():
    reset_proposal_store_for_tests()
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid = str(uuid4())
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": pid}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistRepository", return_value=repo), \
            patch(f"{LIFECYCLE}.notify_presentation_changed"):
        p = tool_bridge.tool_delete(
            entity="playlist", phase="prepare",
            target={"playlistId": pid})
        handle = p.structured_content["data"]["proposal_handle"]
        r = tool_bridge.tool_delete(
            entity="playlist", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1", target_echo=str(uuid4()))
    assert r.is_error is True
    assert r.structured_content["code"] == "CONFIRMATION_MISMATCH"
    assert not repo.delete.called
    reset_proposal_store_for_tests()


def test_delete_playlist_not_found():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    repo = MagicMock()
    repo.get_by_id.return_value = None
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_delete(
            entity="playlist", phase="prepare",
            target={"playlistId": str(uuid4())})
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 404


def test_delete_playlist_no_consent_channel():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = None
    pid = str(uuid4())
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": pid}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_delete(
            entity="playlist", phase="prepare",
            target={"playlistId": pid})
    assert r.is_error is True
    assert r.structured_content["code"] == "CONFIRMATION_UNAVAILABLE"


# ---------------------------------------------------------------------------
# delete.data_model — sealed presentation pipeline (confirm policy)
# ---------------------------------------------------------------------------


def test_delete_data_model_in_delete_vocab():
    from tv_app.application.gpt_actions.capability_surface import (
        DELETE_ENTITIES,
    )
    assert DELETE_ENTITIES.get("data_model") == "delete_data_model"


def test_data_model_op_requires_consent():
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )
    spec = PresentationOpsContentService.operations()["delete_data_model"]
    assert spec["confirmationPolicy"] == "confirm"


# ---------------------------------------------------------------------------
# execute.playlist_history.restore
# ---------------------------------------------------------------------------


def test_restore_history_commits_with_cas():
    dispatch, _, _ = _governed_dispatch()
    pid, hid = str(uuid4()), str(uuid4())
    hist = MagicMock()
    hist.restore.return_value = 7
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": pid}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistHistoryRepository", \
                  return_value=hist), \
            patch(f"{LIFECYCLE}.PlaylistRepository", return_value=repo), \
            patch(f"{LIFECYCLE}.notify_presentation_changed"):
        r = tool_bridge.tool_execute(
            entity="playlist_history", action="restore",
            target={"playlistId": pid, "historyId": hid,
                    "expectedRevision": 3})
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    kw = hist.restore.call_args.kwargs
    assert kw["expected_revision"] == 3
    assert kw["actor_user_id"]


def test_restore_history_conflict_409():
    from tv_app.application.errors.playlist_persistence import (
        PlaylistRevisionConflictError,
    )
    dispatch, _, _ = _governed_dispatch()
    pid, hid = str(uuid4()), str(uuid4())
    hist = MagicMock()
    hist.restore.side_effect = PlaylistRevisionConflictError(
        current_revision=9)
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{LIFECYCLE}.PlaylistHistoryRepository", \
                  return_value=hist):
        r = tool_bridge.tool_execute(
            entity="playlist_history", action="restore",
            target={"playlistId": pid, "historyId": hid,
                    "expectedRevision": 3})
    assert r.is_error is True
    assert r.structured_content["code"] == "REVISION_CONFLICT"


def test_restore_history_requires_write():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="playlist_history", action="restore",
            target={"playlistId": str(uuid4()),
                    "historyId": str(uuid4())})
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 403


def test_restore_history_requires_refs():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="playlist_history", action="restore",
            target={"playlistId": str(uuid4())})
    assert r.is_error is True
    assert r.structured_content["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# R1/D-8 — delete_data_model impact preview (CANON 2026-10-31)
# ---------------------------------------------------------------------------


def test_d8_prepare_shows_conclusive_impact():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid, sid = str(uuid4()), str(uuid4())
    ops = [{"op": "delete_data_model", "modelId": "m1"}]
    cfg = {
        "blocks": [
            {
                "id": "b1",
                "type": "kpi",
                "dataSourceId": "m1",
                "textProjection": {"dataRef": {"field": "vendas"}},
            }
        ]
    }
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService, "preview",
        return_value=_preview_result(
            orderedOps=ops,
            appliedOps=["delete_data_model"],
            nativeConfig=cfg,
        ),
    ):
        r = tool_bridge.tool_delete(
            entity="data_model", phase="prepare",
            target={"playlistId": pid, "slideId": sid, "modelId": "m1"})
    assert r.is_error is False
    data = r.structured_content["data"]
    impact = data["dependencyImpact"][0]
    assert impact["modelId"] == "m1"
    assert impact["verificationStatus"] == "CONCLUSIVE"
    assert impact["confirmationPolicy"] == "confirm"
    assert isinstance(impact["consumerBlocks"], int)


def test_d8_prepare_failclosed_when_discovery_inconclusive():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid, sid = str(uuid4()), str(uuid4())
    ops = [{"op": "delete_data_model", "modelId": "m1"}]
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService, "preview",
        return_value=_preview_result(
            orderedOps=ops,
            appliedOps=["delete_data_model"],
            nativeConfig=None,
        ),
    ):
        r = tool_bridge.tool_delete(
            entity="data_model", phase="prepare",
            target={"playlistId": pid, "slideId": sid, "modelId": "m1"})
    assert r.is_error is True
    assert r.structured_content["code"] == "DEPENDENCY_UNRESOLVED"
    assert r.structured_content["httpStatus"] == 409
