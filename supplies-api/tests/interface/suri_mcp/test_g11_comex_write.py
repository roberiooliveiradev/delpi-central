"""SURI-MCP V12 G11 — comex governed write dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge, comex_execute


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "actor-1"

    def has_permission(self, code):
        return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    cmx = MagicMock()
    cmx.request_ncm.return_value = {
        "governance_id": "g1", "status": "pending_fiscal_review"}
    cmx.transition.return_value = {
        "governance_id": "g1", "status": "approved"}
    cmx.create_view.return_value = {"view_id": "v1", "name": "V"}
    cmx.update_view.return_value = {"view_id": "v1", "name": "V"}
    with patch.object(comex_execute, "_COMEX", cmx), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield cmx


def test_ncm_request_confirmed(env):
    r = tool_bridge.tool_execute(
        "comex", "ncm_request",
        [{"ncm_code": "12345678", "idempotency_key": None}])
    assert _ok(r), r
    env.request_ncm.assert_called_once()
    kw = env.request_ncm.call_args.kwargs
    assert kw["ncm_code"] == "12345678"


def test_ncm_transition_confirmed(env):
    r = tool_bridge.tool_execute(
        "comex", "ncm_transition",
        [{"governance_id": "g1", "to_status": "approved",
          "expected_revision": 2}])
    assert _ok(r), r
    env.transition.assert_called_once()
    kw = env.transition.call_args.kwargs
    assert kw["to_status"] == "approved"
    assert kw["expected_revision"] == 2


def test_view_create_confirmed(env):
    r = tool_bridge.tool_execute(
        "comex", "view_create",
        [{"name": "My view", "granularity": "month"}])
    assert _ok(r), r
    env.create_view.assert_called_once()
    body = env.create_view.call_args.kwargs["body"]
    assert body["name"] == "My view"


def test_view_update_confirmed(env):
    r = tool_bridge.tool_execute(
        "comex", "view_update",
        [{"view_id": "v1", "name": "My view"}])
    assert _ok(r), r
    env.update_view.assert_called_once()
    assert env.update_view.call_args.args[0] == "v1"


def test_comex_unknown_action_rejected(env):
    r = tool_bridge.tool_execute("comex", "view_delete", [{"name": "x"}])
    assert not _ok(r)


def test_comex_unknown_key_rejected(env):
    r = tool_bridge.tool_execute(
        "comex", "ncm_request",
        [{"ncm_code": "12345678", "bogus": 1}])
    assert not _ok(r)


def test_ncm_request_rejects_view_key(env):
    r = tool_bridge.tool_execute(
        "comex", "ncm_request",
        [{"ncm_code": "12345678", "view_id": "v1"}])
    assert not _ok(r)


def test_view_create_rejects_transition_key(env):
    r = tool_bridge.tool_execute(
        "comex", "view_create",
        [{"name": "v", "governance_id": "g1"}])
    assert not _ok(r)
