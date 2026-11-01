"""SURI-MCP V15 G14 — comex view_delete confirmation semantics."""
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
    with patch.object(comex_execute, "_COMEX", cmx), \
         patch.object(comex_execute, "_claim_or_replay",
                      lambda *a, **k: (None, None)), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield cmx


def test_view_delete_confirmed(env):
    r = tool_bridge.tool_execute(
        "comex", "view_delete",
        [{"view_id": "v1",
          "confirmation": {"view_id": "v1", "acknowledged": True}}])
    assert _ok(r), r
    env.delete_view.assert_called_once()
    assert env.delete_view.call_args.args[0] == "v1"


def test_view_delete_requires_confirmation(env):
    r = tool_bridge.tool_execute(
        "comex", "view_delete", [{"view_id": "v1"}])
    env.delete_view.assert_not_called()
    t = str(getattr(r, "content", r))
    assert "confirmation_unavailable" in t


def test_view_delete_rejects_mismatched_id(env):
    r = tool_bridge.tool_execute(
        "comex", "view_delete",
        [{"view_id": "v1",
          "confirmation": {"view_id": "v2", "acknowledged": True}}])
    env.delete_view.assert_not_called()
    assert "confirmation_unavailable" in str(getattr(r, "content", r))


def test_view_delete_rejects_unacknowledged(env):
    r = tool_bridge.tool_execute(
        "comex", "view_delete",
        [{"view_id": "v1",
          "confirmation": {"view_id": "v1", "acknowledged": False}}])
    env.delete_view.assert_not_called()
    assert "confirmation_unavailable" in str(getattr(r, "content", r))


def test_view_delete_rejects_extra_key(env):
    r = tool_bridge.tool_execute(
        "comex", "view_delete",
        [{"view_id": "v1", "bogus": 1,
          "confirmation": {"view_id": "v1", "acknowledged": True}}])
    assert not _ok(r)
