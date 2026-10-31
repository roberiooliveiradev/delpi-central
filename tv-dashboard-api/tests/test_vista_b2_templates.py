"""B2 — slide_template lifecycle through the six semantic verbs.

read.slide_template (list/get), execute.slide_template
(create/update/clone/publish/unpublish/archive) and
delete.slide_template (sealed proposal + A5 consent artifact).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from test_vista_mcp_write_surface import (
    _access_patches,
    _ctx,
    _editor,
    _governed_dispatch,
    _viewer,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES

SVC = (
    "tv_app.application.services.slide_template_library_service."
    "SlideTemplateLibraryService"
)


def _manager(user_id="mgr-1"):
    u = _editor(user_id)
    u.permissions = [
        "tv-dashboard.read", "tv-dashboard.write",
        "tv-dashboard.templates.manage",
    ]
    return u


def _svc(**kw):
    svc = MagicMock()
    for k, v in kw.items():
        getattr(svc, k).return_value = v
    return svc


def test_surface_still_six_tools():
    assert MCP_TOOL_NAMES == (
        "get_context", "read", "analyze", "knowledge", "execute", "delete")


# ---------------------------------------------------------------------------
# read.slide_template
# ---------------------------------------------------------------------------


def test_read_template_published_list():
    dispatch, _, _ = _governed_dispatch()
    svc = _svc(list_published=[{"id": "t1", "status": "published"}])
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_read(
            entity="slide_template", action="list",
            filters={"status": "published"})
    assert r.is_error is False
    assert r.structured_content["data"]["count"] == 1


def test_read_template_library_requires_manage():
    dispatch, _, _ = _governed_dispatch()
    svc = _svc(list_library=[{"id": "t2", "status": "draft"}])
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_read(
            entity="slide_template", action="list",
            filters={"status": "draft"})
    assert r.is_error is False
    assert r.structured_content["data"]["count"] == 1


def test_read_template_library_denied_without_manage():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_read(
            entity="slide_template", action="list",
            filters={"status": "draft"})
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 403


def test_read_template_get():
    dispatch, _, _ = _governed_dispatch()
    tid = str(uuid4())
    svc = _svc(get={"id": tid, "status": "published", "label": "T"})
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_read(
            entity="slide_template", action="get", ref=tid)
    assert r.is_error is False
    assert r.structured_content["data"]["item"]["id"] == tid


def test_read_template_get_requires_ref():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_read(entity="slide_template", action="get")
    assert r.is_error is True
    assert r.structured_content["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# execute.slide_template
# ---------------------------------------------------------------------------


def test_execute_template_create():
    dispatch, _, _ = _governed_dispatch()
    tid = str(uuid4())
    svc = _svc(create={"id": tid, "label": "Novo", "status": "draft"})
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="create",
            operations=[{"label": "Novo", "description": "d"}])
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    assert svc.create.call_args.kwargs["label"] == "Novo"


def test_execute_template_publish():
    dispatch, _, _ = _governed_dispatch()
    tid = str(uuid4())
    svc = _svc(publish={"id": tid, "status": "published"})
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="publish",
            target={"templateId": tid})
    assert r.is_error is False
    assert r.structured_content["data"]["item"]["status"] == "published"


def test_execute_template_lifecycle_actions():
    dispatch, _, _ = _governed_dispatch()
    tid = str(uuid4())
    svc = MagicMock()
    for action in ("update", "clone", "unpublish", "archive"):
        getattr(svc, action).return_value = {"id": tid, "op": action}
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="archive",
            target={"templateId": tid})
        assert r.is_error is False
        r2 = tool_bridge.tool_execute(
            entity="slide_template", action="clone",
            target={"templateId": tid})
        assert r2.is_error is False
        r3 = tool_bridge.tool_execute(
            entity="slide_template", action="update",
            target={"templateId": tid},
            operations=[{"label": "Renomeado"}])
        assert r3.is_error is False
        assert svc.update.call_args.kwargs["label"] == "Renomeado"


def test_execute_template_denied_without_manage():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="create",
            operations=[{"label": "X"}])
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 403


def test_execute_template_unknown_action():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="explode")
    assert r.is_error is True


# ---------------------------------------------------------------------------
# delete.slide_template — sealed proposal + consent
# ---------------------------------------------------------------------------


def _consent_mock():
    import time

    c = MagicMock()
    c.issue_for_proposal.return_value = {
        "challenge_id": "chal-1",
        "status": "PENDING",
        "action": "delete.slide_template",
        "target_ref": "tpl-1",
        "origin": "mcp",
        "created_at": time.time(),
        "approved_at": None,
        "expires_at": time.time() + 600,
    }
    c.verify_for_commit.return_value = {
        "challenge_id": "chal-1", "status": "APPROVED"}
    return c


def test_delete_template_prepare_commit():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    tid = str(uuid4())
    svc = _svc(get={"id": tid, "status": "draft"},
               delete={"id": tid, "deleted": True})
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        p = tool_bridge.tool_delete(
            entity="slide_template", phase="prepare",
            target={"templateId": tid})
        assert p.is_error is False
        data = p.structured_content["data"]
        assert data["status"] == "consent_required"
        handle = data["proposal_handle"]

        r = tool_bridge.tool_delete(
            entity="slide_template", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1",
            target_echo=tid)
        assert r.is_error is False
        assert r.structured_content["data"]["status"] == "VERIFIED"
        assert svc.delete.called


def test_delete_template_wrong_echo_rejected():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = _consent_mock()
    tid = str(uuid4())
    svc = _svc(get={"id": tid, "status": "draft"})
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        p = tool_bridge.tool_delete(
            entity="slide_template", phase="prepare",
            target={"templateId": tid})
        handle = p.structured_content["data"]["proposal_handle"]
        r = tool_bridge.tool_delete(
            entity="slide_template", phase="commit",
            proposal_handle=handle,
            consent_artifact="chal-1",
            target_echo=str(uuid4()))
    assert r.is_error is True
    assert r.structured_content["code"] in (
        "CONFIRMATION_MISMATCH", "CONSENT_MISMATCH")
    assert not svc.delete.called


def test_delete_template_requires_consent_channel():
    dispatch, _, _ = _governed_dispatch()
    dispatch._consent = None
    tid = str(uuid4())
    svc = _svc(get={"id": tid, "status": "draft"})
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(SVC, return_value=svc):
        r = tool_bridge.tool_delete(
            entity="slide_template", phase="prepare",
            target={"templateId": tid})
    assert r.is_error is True
    assert r.structured_content["code"] in (
        "CONFIRMATION_UNAVAILABLE",)
