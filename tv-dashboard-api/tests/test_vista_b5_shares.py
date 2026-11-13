"""B5 — playlist shares, edit invites & revokes via the six verbs.

read.playlist.list_shares (manage), execute.playlist.share /
create_edit_invite / accept_edit_invite, delete.playlist_share /
delete.edit_invite (sealed proposal + A5 consent).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from test_vista_mcp_write_surface import (
    _ctx,
    _editor,
    _governed_dispatch,
    _viewer,
    reset_proposal_store_for_tests,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES

SHARE_SVC = "tv_app.application.services.playlist_share_service"
ACCESS_SVC = (
    "tv_app.application.services.playlist_share_service."
    "PlaylistAccessService"
)


def _manage_access():
    svc = MagicMock()
    svc.resolve.return_value = MagicMock(
        can_manage=True,
        can_edit=True,
        can_read=True,
    )
    return svc


def _no_access():
    svc = MagicMock()
    svc.resolve.return_value = MagicMock(
        can_manage=False,
        can_edit=False,
        can_read=True,
    )
    return svc


def _consent_mock():
    import time

    c = MagicMock()
    c.issue_for_proposal.return_value = {
        "challenge_id": "chal-1",
        "status": "PENDING",
        "action": "delete.playlist_share",
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
# read.playlist.list_shares
# ---------------------------------------------------------------------------


def test_list_shares_manage_ok():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    repo = MagicMock()
    repo.list_shares.return_value = [{"userId": "u2", "role": "editor"}]
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_read(
            entity="playlist", action="list_shares", ref=pid)
    assert r.is_error is False
    assert r.structured_content["data"]["count"] == 1


def test_list_shares_denied_without_manage():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_no_access()):
        r = tool_bridge.tool_read(
            entity="playlist", action="list_shares", ref=pid)
    assert r.is_error is True


def test_list_shares_requires_ref():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_read(entity="playlist", action="list_shares")
    assert r.is_error is True
    assert r.structured_content["code"] == "ARGUMENT_VALIDATION"


# ---------------------------------------------------------------------------
# execute.playlist.share / invites
# ---------------------------------------------------------------------------


def test_share_upsert_ok():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    repo = MagicMock()
    repo.upsert_share.return_value = {"userId": "u9", "role": "editor"}
    repo.get_by_id.return_value = {"id": pid, "name": "P"}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo), \
            patch(f"{SHARE_SVC}.notify_playlist_share_granted"), \
            patch(f"{SHARE_SVC}.notify_playlist_library_changed"):
        r = tool_bridge.tool_execute(
            entity="playlist", action="share",
            target={"playlistId": pid},
            operations=[{"targetUserId": "u9", "role": "editor"}])
    assert r.is_error is False
    assert r.structured_content["data"]["share"]["userId"] == "u9"


def test_share_self_blocked():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    actor = "editor-1"
    with _ctx(_editor(actor)), patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch(ACCESS_SVC, return_value=_manage_access()):
        r = tool_bridge.tool_execute(
            entity="playlist", action="share",
            target={"playlistId": pid},
            operations=[{"targetUserId": actor, "role": "editor"}])
    assert r.is_error is True


def test_create_edit_invite():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    repo = MagicMock()
    repo.create_edit_invite.return_value = {
        "id": "inv1", "token": "tok", "role": "editor"}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_execute(
            entity="playlist", action="create_edit_invite",
            target={"playlistId": pid},
            operations=[{"role": "editor"}])
    assert r.is_error is False
    data = r.structured_content["data"]
    assert data["invite"]["token"] == "tok"
    assert "redeemPath" in data["invite"]


def test_accept_edit_invite_actor_bound():
    dispatch, _, _ = _governed_dispatch()
    repo = MagicMock()
    repo.redeem_edit_invite.return_value = {
        "playlistId": "p1", "role": "editor"}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_execute(
            entity="playlist", action="accept_edit_invite",
            operations=[{"token": "tok-9"}])
    assert r.is_error is False
    kw = repo.redeem_edit_invite.call_args.kwargs
    assert kw["redeemed_by"]


def test_accept_invite_invalid():
    dispatch, _, _ = _governed_dispatch()
    repo = MagicMock()
    repo.redeem_edit_invite.return_value = None
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_execute(
            entity="playlist", action="accept_edit_invite",
            operations=[{"token": "bad"}])
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 404


# ---------------------------------------------------------------------------
# delete.playlist_share / delete.edit_invite — sealed + consent
# ---------------------------------------------------------------------------


def test_revoke_share_prepare_commit():
    reset_proposal_store_for_tests()
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid = str(uuid4())
    repo = MagicMock()
    repo.list_shares.return_value = [{"userId": "u2", "role": "editor"}]
    repo.revoke_share.return_value = True
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        p = tool_bridge.tool_delete(
            entity="playlist_share", phase="prepare",
            target={"playlistId": pid, "targetUserId": "u2"})
        assert p.is_error is False
        handle = p.structured_content["data"]["proposal_handle"]
        r = tool_bridge.tool_delete(
            entity="playlist_share", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1", target_echo="u2")
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    assert repo.revoke_share.called
    reset_proposal_store_for_tests()


def test_revoke_share_missing_target_user():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid = str(uuid4())
    repo = MagicMock()
    repo.list_shares.return_value = [{"userId": "u2"}]
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_delete(
            entity="playlist_share", phase="prepare",
            target={"playlistId": pid})
    assert r.is_error is True
    assert r.structured_content["code"] == "ARGUMENT_VALIDATION"


def test_revoke_edit_invites_bulk():
    reset_proposal_store_for_tests()
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    pid = str(uuid4())
    repo = MagicMock()
    repo.list_shares.return_value = []
    repo.revoke_edit_invites.return_value = 3
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        p = tool_bridge.tool_delete(
            entity="edit_invite", phase="prepare",
            target={"playlistId": pid})
        assert p.is_error is False
        handle = p.structured_content["data"]["proposal_handle"]
        r = tool_bridge.tool_delete(
            entity="edit_invite", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1", target_echo=pid)
    assert r.is_error is False
    assert r.structured_content["data"]["result"]["revoked"] == 3
    reset_proposal_store_for_tests()


def test_list_shares_real_access_property():
    """Regression: can_manage is a @property — assert_can_manage must not
    call it with parens (previous TypeError produced HTTP 500)."""
    from tv_app.application.services.playlist_access_service import (
        PlaylistAccess,
    )
    from tv_app.application.services.playlist_share_service import (
        assert_can_manage,
    )
    import pytest

    svc = MagicMock()
    svc.resolve.return_value = PlaylistAccess(level="editor")
    with patch(f"{SHARE_SVC}.PlaylistAccessService", return_value=svc):
        with pytest.raises(PermissionError):
            assert_can_manage(uuid4(), _editor())
    svc.resolve.return_value = PlaylistAccess(level="owner")
    with patch(f"{SHARE_SVC}.PlaylistAccessService", return_value=svc):
        assert_can_manage(uuid4(), _editor())  # no raise
    svc.resolve.return_value = PlaylistAccess(level="none")
    with patch(f"{SHARE_SVC}.PlaylistAccessService", return_value=svc):
        with pytest.raises(PermissionError):
            assert_can_manage(uuid4(), _editor())


def test_revoke_share_no_consent_channel():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = None
    pid = str(uuid4())
    repo = MagicMock()
    repo.list_shares.return_value = [{"userId": "u2"}]
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(ACCESS_SVC, return_value=_manage_access()), \
            patch(f"{SHARE_SVC}.PlaylistRepository", return_value=repo):
        r = tool_bridge.tool_delete(
            entity="playlist_share", phase="prepare",
            target={"playlistId": pid, "targetUserId": "u2"})
    assert r.is_error is True
    assert r.structured_content["code"] == "CONFIRMATION_UNAVAILABLE"
