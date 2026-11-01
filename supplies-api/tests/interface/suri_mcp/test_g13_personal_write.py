"""SURI-MCP V14 G13 — session/users governed write dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge, personal_execute


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
    pref = MagicMock()
    pref.patch.return_value = {
        "userId": "actor-1", "defaultBranch": "01"}
    prof = MagicMock()
    prof.patch.return_value = {"userId": "actor-1"}
    with patch.object(personal_execute, "_PREFERENCES", pref), \
         patch.object(personal_execute, "_PROFILE", prof), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield pref, prof


def test_preferences_update_confirmed(env):
    pref, _ = env
    r = tool_bridge.tool_execute(
        "session", "preferences_update",
        [{"defaultBranch": "01", "tableDensity": "compact"}])
    assert _ok(r), r
    pref.patch.assert_called_once()
    body = pref.patch.call_args.args[1]
    assert body["defaultBranch"] == "01"


def test_profile_update_confirmed(env):
    _, prof = env
    r = tool_bridge.tool_execute(
        "users", "profile_update",
        [{"user_id": "actor-1", "tableDensity": "compact"}])
    assert _ok(r), r
    prof.patch.assert_called_once()
    assert prof.patch.call_args.args[1] == "actor-1"


def test_profile_update_rejects_wrong_key(env):
    r = tool_bridge.tool_execute(
        "users", "profile_update",
        [{"user_id": "actor-1", "bogus": 1}])
    assert not _ok(r)


def test_preferences_update_rejects_user_id(env):
    r = tool_bridge.tool_execute(
        "session", "preferences_update",
        [{"user_id": "other", "tableDensity": "compact"}])
    assert not _ok(r)


def test_personal_unknown_action(env):
    r = tool_bridge.tool_execute(
        "session", "delete", [{"tableDensity": "x"}])
    assert not _ok(r)
