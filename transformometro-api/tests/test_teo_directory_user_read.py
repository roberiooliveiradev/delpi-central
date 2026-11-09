"""TÉO directory identity search — Core-owned, TM Bearer-forward facade.

Semantics under test:
- AuthZ fail-closed (no transformometro.access → 403);
- q < 2 → validation;
- unique match → ambiguity=false + canonical user_id;
- multi-match → ambiguity=true (never silently pick one);
- empty → guidance to refine;
- only safe fields projected (no tokens/groups/permissions);
- Bearer forwarded verbatim to Core gateway.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tm_app.application.directory.directory_users_read_service import (
    DirectoryUsersReadService,
)
from tm_app.application.gpt_actions.errors import GptActionsError


class _FakeGateway:
    def __init__(self, items: list[dict] | None = None) -> None:
        self.items = list(items or [])
        self.calls: list[dict] = []

    def search_users(self, authorization: str, **kwargs):
        self.calls.append({"authorization": authorization, **kwargs})
        return list(self.items)


class _AllowAuthz:
    def has_access(self, user):
        return user is not None


class _DenyAuthz:
    def has_access(self, user):
        return False


def _user():
    return SimpleNamespace(id="actor-1", permissions=["transformometro.access"])


def test_unique_match_returns_canonical_identity() -> None:
    gw = _FakeGateway(
        [{"id": "u-joici", "name": "Joici Motta", "email": "j***@delpi.com.br"}]
    )
    svc = DirectoryUsersReadService(gateway=gw, authz=_AllowAuthz())
    result = svc.search(_user(), "Bearer tok", q="Joici Motta", limit=10)
    assert result["schema"] == "directory_user_search_v1"
    assert result["total"] == 1
    assert result["ambiguity"] is False
    assert result["items"][0]["user_id"] == "u-joici"
    assert result["items"][0]["display_name"] == "Joici Motta"
    assert result["items"][0]["eligible"] is True
    assert "Unique match" in result["guidance"]
    assert gw.calls[0]["authorization"] == "Bearer tok"
    assert gw.calls[0]["q"] == "Joici Motta"


def test_ambiguity_never_collapses_to_one() -> None:
    gw = _FakeGateway(
        [
            {"id": "u-1", "name": "João Silva", "email": "a***@x.com"},
            {"id": "u-2", "name": "João Silva", "email": "b***@x.com"},
        ]
    )
    svc = DirectoryUsersReadService(gateway=gw, authz=_AllowAuthz())
    result = svc.search(_user(), "Bearer t", q="João Silva")
    assert result["ambiguity"] is True
    assert result["total"] == 2
    assert "disambiguate" in result["guidance"].lower()
    assert {i["user_id"] for i in result["items"]} == {"u-1", "u-2"}


def test_empty_result_guidance() -> None:
    svc = DirectoryUsersReadService(gateway=_FakeGateway([]), authz=_AllowAuthz())
    result = svc.search(_user(), "Bearer t", q="xyzzy-nobody")
    assert result["total"] == 0
    assert result["ambiguity"] is False
    assert "No match" in result["guidance"]


def test_query_too_short() -> None:
    svc = DirectoryUsersReadService(gateway=_FakeGateway(), authz=_AllowAuthz())
    with pytest.raises(GptActionsError) as exc:
        svc.search(_user(), "Bearer t", q="J")
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "QUERY_TOO_SHORT"


def test_authz_denied() -> None:
    svc = DirectoryUsersReadService(gateway=_FakeGateway(), authz=_DenyAuthz())
    with pytest.raises(GptActionsError) as exc:
        svc.search(_user(), "Bearer t", q="Joici")
    assert exc.value.status_code == 403
    assert exc.value.data["error_kind"] == "authz"


def test_unauthenticated() -> None:
    svc = DirectoryUsersReadService(gateway=_FakeGateway(), authz=_AllowAuthz())
    with pytest.raises(GptActionsError) as exc:
        svc.search(None, "Bearer t", q="Joici")
    assert exc.value.status_code == 401


def test_items_without_id_are_dropped() -> None:
    gw = _FakeGateway(
        [
            {"id": "", "name": "Ghost", "email": "g***@x.com"},
            {"id": "u-ok", "name": "Ok User", "email": "o***@x.com"},
        ]
    )
    svc = DirectoryUsersReadService(gateway=gw, authz=_AllowAuthz())
    result = svc.search(_user(), "Bearer t", q="User")
    assert result["total"] == 1
    assert result["items"][0]["user_id"] == "u-ok"


def test_projected_fields_are_minimal() -> None:
    gw = _FakeGateway(
        [
            {
                "id": "u-1",
                "name": "Robério Teixeira de Oliveira",
                "email": "r***@delpi.com.br",
                "groups": ["secret"],
                "permissions": ["admin"],
                "token": "leak",
            }
        ]
    )
    svc = DirectoryUsersReadService(gateway=gw, authz=_AllowAuthz())
    item = svc.search(_user(), "Bearer t", q="Robério")["items"][0]
    assert set(item.keys()) == {
        "user_id",
        "display_name",
        "email_masked",
        "eligible",
    }
    assert "groups" not in item
    assert "token" not in item
    assert "permissions" not in item


def test_openapi_exposes_directory_user_read() -> None:
    from tm_app.application.gpt_actions.openapi_builder import (
        GPT_ACTIONS_OPERATION_IDS,
        build_gpt_actions_openapi,
    )

    assert "gpt_directory_user_read" in GPT_ACTIONS_OPERATION_IDS
    doc = build_gpt_actions_openapi()
    path = doc["paths"]["/transformometro/gpt-actions/v1/directory-users"]["get"]
    assert path["operationId"] == "gpt_directory_user_read"
    assert path["parameters"][0]["schema"]["enum"] == ["search"]


def test_mcp_v3_maps_directory_user_to_read() -> None:
    from tm_app.application.intelligence.capability_registry import (
        MCP_TO_V3_TOOL,
        actions_to_v3_parity,
    )

    assert MCP_TO_V3_TOOL["directory_user_read"] == "read"
    assert actions_to_v3_parity()["gpt_directory_user_read"] == ("read",)
