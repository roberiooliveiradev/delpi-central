"""SURI-MCP V11 G8 — session + users read dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import UsersRelatedFilters


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
    cap = MagicMock(); cap.resolve.return_value = {"permissions": []}
    pref = MagicMock(); pref.get.return_value = {"prefs": {}}
    prof = MagicMock()
    prof.get.return_value = {"id": "u1"}
    prof.photo.return_value = (b"img", "image/jpeg", "p.jpg")
    prof.related_purchase_requests.return_value = {"items": []}
    with patch.object(tool_bridge, "_CAPABILITY_SERVICE", cap), \
         patch.object(tool_bridge, "_PREFERENCES_SERVICE", pref), \
         patch.object(tool_bridge, "_USER_PROFILE_SERVICE", prof), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield cap, pref, prof


def test_session_capabilities(env):
    cap, _, _ = env
    r = tool_bridge.tool_read("session", "capabilities", {})
    assert _ok(r), r
    cap.resolve.assert_called_once()


def test_session_preferences(env):
    _, pref, _ = env
    r = tool_bridge.tool_read("session", "preferences", {})
    assert _ok(r), r
    pref.get.assert_called_once()


def test_session_rejects_identity(env):
    r = tool_bridge.tool_read(
        "session", "capabilities", {}, {"user_id": "x"})
    assert not _ok(r)


def test_users_profile(env):
    _, _, prof = env
    r = tool_bridge.tool_read(
        "users", "profile", None, {"user_id": "u1"})
    assert _ok(r), r
    prof.get.assert_called_once()
    assert prof.get.call_args.args[1] == "u1"


def test_users_photo_base64(env):
    _, _, prof = env
    r = tool_bridge.tool_read(
        "users", "photo", None, {"user_id": "u1"})
    assert _ok(r), r
    prof.photo.assert_called_once()


def test_users_related_requests(env):
    _, _, prof = env
    m = UsersRelatedFilters.model_validate(
        {"branch": ["01"], "page": 2, "page_size": 10})
    r = tool_bridge.tool_read(
        "users", "related_requests", m, {"user_id": "u1"})
    assert _ok(r), r
    kw = prof.related_purchase_requests.call_args.kwargs
    assert kw["branches"] == ["01"] and kw["page"] == 2


def test_users_rejects_extra_key(env):
    r = tool_bridge.tool_read(
        "users", "related_requests",
        {"bogus": 1}, {"user_id": "u1"})
    assert not _ok(r)


def test_users_missing_user_id(env):
    r = tool_bridge.tool_read("users", "profile", None, {})
    assert not _ok(r)


def test_users_unknown_action(env):
    r = tool_bridge.tool_read("users", "delete", None, {"user_id": "x"})
    assert not _ok(r)
