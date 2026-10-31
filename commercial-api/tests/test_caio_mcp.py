"""CAIO semantic MCP surface — six tools, registry, governance.

Mirrors the EVA semantic tests at the Commercial owner: human
principal + commercial permission required, typed (entity, action)
allowlist dispatch only, deny-by-default for writes in v1 — never a
generic proxy, never authorization from personality or metadata.
"""

from __future__ import annotations

import asyncio
import hashlib
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.errors import mcp_tool_result

from commercial_app.application.caio.semantic_registry import (
    SEMANTIC_ACTIONS,
    SEMANTIC_TOOL_NAMES,
    actions_for_entity,
    semantic_action,
)
from commercial_app.interface.mcp import semantic_bridge as sem
from commercial_app.interface.mcp import tool_bridge as bridge
from commercial_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    SEMANTIC_TOOL_CLASS,
    TOOL_CLASS,
)
from commercial_app.interface.mcp.server import create_mcp_server


def _human_user(permissions=("commercial.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


# --- surface contract -------------------------------------------------------


def test_exactly_six_semantic_tools():
    assert SEMANTIC_TOOL_NAMES == (
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    )
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    assert [t.name for t in tools] == list(SEMANTIC_TOOL_NAMES)


def test_tool_classes_and_annotations():
    assert SEMANTIC_TOOL_CLASS["delete"] == "ACT"
    assert SEMANTIC_TOOL_CLASS["read"] == "READ"
    assert TOOL_CLASS == SEMANTIC_TOOL_CLASS
    assert "delete" in DESTRUCTIVE_ACT_TOOLS
    server = create_mcp_server()
    by_name = {t.name: t for t in asyncio.run(server.list_tools())}
    assert by_name["read"].annotations.read_only_hint is True
    assert by_name["delete"].annotations.destructive_hint is True
    for tool in by_name.values():
        assert getattr(tool, "securitySchemes", None)


def test_registry_unique_pairs_and_proven_dispatch():
    pairs = [(a.entity, a.action) for a in SEMANTIC_ACTIONS]
    assert len(pairs) == len(set(pairs))
    for a in SEMANTIC_ACTIONS:
        assert a.tool in SEMANTIC_TOOL_NAMES
        assert a.status in {"proven", "planned", "not_implemented"}


def test_deletes_are_always_destructive_and_phased():
    delete = [a for a in SEMANTIC_ACTIONS if a.tool == "delete"]
    assert delete
    for a in delete:
        assert a.destructive
        assert a.phases == ("prepare", "commit")


# --- AuthZ gate -------------------------------------------------------------


def test_require_commercial_human_no_context():
    with pytest.raises(PermissionError):
        bridge._require_commercial_human()


def test_require_commercial_human_rejects_service_principal():
    _set_context(_human_user(principal_type="service"))
    with pytest.raises(PermissionError):
        bridge._require_commercial_human()


def test_require_commercial_human_rejects_missing_permission():
    _set_context(_human_user(permissions=["other.scope"]))
    with pytest.raises(PermissionError):
        bridge._require_commercial_human()


def test_require_commercial_human_accepts_access_and_manage():
    _set_context(_human_user(permissions=["commercial.access"]))
    assert bridge._require_commercial_human().user.id == "user-1"
    _set_context(_human_user(permissions=["commercial.manage"]))
    assert bridge._require_commercial_human().user.id == "user-1"


def test_unauthenticated_get_context_is_401_result():
    result = sem.tool_get_context()
    payload = result.structured_content
    assert result.is_error is True
    assert payload["status_code"] == 401
    assert payload["error_code"] == "unauthenticated"


# --- get_context ------------------------------------------------------------


def test_get_context_returns_semantic_surface():
    _set_context(_human_user())
    result = sem.tool_get_context()
    payload = result.structured_content
    assert result.is_error is False
    assert payload["success"] is True
    data = payload["data"]
    assert [t["name"] for t in data["semantic_tools"]] == list(
        SEMANTIC_TOOL_NAMES
    )
    assert data["commercial_capabilities"]["access"] is True
    assert data["act_enabled"] is True
    assert any(
        e["entity"] == "open_order" for e in data["entities"]
    )


def test_get_context_unknown_entity_errors():
    _set_context(_human_user())
    result = sem.tool_get_context(entity="nope")
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


# --- read dispatch ----------------------------------------------------------


def test_read_unknown_entity_is_validation_error():
    _set_context(_human_user())
    result = sem.tool_read(entity="nope", action="list")
    payload = result.structured_content
    assert result.is_error is True
    assert payload["error_code"] == "not_implemented"
    assert payload["status_code"] == 400


def test_read_execute_only_action_is_tool_mismatch():
    _set_context(_human_user())
    result = sem.tool_read(entity="portfolio", action="create")
    payload = result.structured_content
    assert result.is_error is True
    assert payload["status_code"] == 400


def test_read_rejects_undeclared_filter_fields():
    _set_context(_human_user())
    result = sem.tool_read(
        entity="customer",
        action="list",
        filters={"arbitrary_sql": "DROP TABLE"},
    )
    payload = result.structured_content
    assert result.is_error is True
    assert payload["error_code"] == "validation"
    assert "arbitrary_sql" in payload["message"]


def test_read_dispatches_to_official_handler():
    _set_context(_human_user())
    expected = mcp_tool_result(
        {"success": True, "message": "ok", "data": {"items": [1]}},
        is_error=False,
    )
    with patch.object(
        bridge, "tool_customer_list", return_value=expected
    ) as handler:
        result = sem.tool_read(
            entity="customer",
            action="list",
            filters={"portfolio_id": "p-1"},
        )
    handler.assert_called_once_with(portfolio_id="p-1")
    payload = result.structured_content
    assert result.is_error is False
    assert payload["entity"] == "customer"
    assert payload["action"] == "list"
    assert payload["data"] == {"items": [1]}


def test_read_portfolio_me_calls_official_use_case():
    _set_context(_human_user())

    class _FakeUseCase:
        def get_me_portfolios(self, user_id):
            assert user_id == "user-1"
            return ["p1"]

        def serialize_portfolios(self, portfolios):
            return [{"id": pid} for pid in portfolios]

    with patch.object(
        bridge,
        "build_manage_seller_portfolio_use_case",
        return_value=_FakeUseCase(),
    ):
        result = bridge.tool_portfolio_me()
    payload = result.structured_content
    assert result.is_error is False
    assert payload["data"]["user_id"] == "user-1"
    assert payload["data"]["portfolios"] == [{"id": "p1"}]


# --- analyze ----------------------------------------------------------------


def test_analyze_unknown_type_is_not_implemented():
    _set_context(_human_user())
    result = sem.tool_analyze(analysis_type="nope.deep")
    payload = result.structured_content
    assert result.is_error is True
    assert payload["status_code"] == 501
    assert "portfolio.open_summary" in payload["data"]["available"]


def test_analyze_rejects_undeclared_parameters():
    _set_context(_human_user())
    result = sem.tool_analyze(
        analysis_type="portfolio.open_summary",
        parameters={"evil": "param"},
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


def test_analyze_open_summary_delegates_to_official_use_case():
    _set_context(_human_user())
    expected = mcp_tool_result(
        {"success": True, "message": "ok", "data": {"x": 1}},
        is_error=False,
    )
    with patch.object(
        bridge, "analyze_open_portfolio_summary", return_value=expected
    ) as handler:
        result = sem.tool_analyze(
            analysis_type="portfolio.open_summary",
            question="saldo?",
            parameters={"scope_mode": "membership"},
        )
    handler.assert_called_once()
    kwargs = handler.call_args.kwargs
    assert kwargs["scope_mode"] == "membership"
    assert kwargs["question"] == "saldo?"
    assert result.is_error is False


# --- knowledge --------------------------------------------------------------


def test_knowledge_returns_versioned_guidance():
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="caio.usage")
    payload = result.structured_content
    assert result.is_error is False
    assert payload["data"]["topic"] == "caio.usage"
    assert payload["data"]["knowledge_version"] == "3.2"


def test_knowledge_unknown_topic_is_not_found():
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="nope")
    payload = result.structured_content
    assert result.is_error is True
    assert payload["status_code"] == 404


def test_knowledge_products_guide_is_implemented():
    """CAIO 3.0 ampliação: products.guide left the planned state —
    the topic now returns the implemented guidance."""
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="products.guide")
    payload = result.structured_content
    assert result.is_error is False
    assert payload["data"]["status"] == "implemented"


# --- execute / delete (deny-by-default) --------------------------------------


def test_execute_manage_gate_blocks_access_only_user():
    _set_context(_human_user())
    result = sem.tool_execute(
        entity="portfolio",
        action="create",
        payload={"display_name": "x"},
    )
    payload = result.structured_content
    assert result.is_error is True
    assert payload["status_code"] == 403


def test_execute_rejects_undeclared_payload_field():
    _set_context(_human_user(permissions=["commercial.manage"]))
    result = sem.tool_execute(
        entity="portfolio",
        action="create",
        payload={"not_a_field": "x"},
    )
    payload = result.structured_content
    assert result.is_error is True
    assert payload["error_code"] == "validation"
    assert "display_name" in str(payload)


def test_delete_requires_target_ref():
    _set_context(_human_user())
    result = sem.tool_delete(entity="task", target_ref="")
    payload = result.structured_content
    assert result.is_error is True
    assert payload["error_code"] == "validation"


def test_delete_unknown_action_is_validation_error():
    _set_context(_human_user())
    result = sem.tool_delete(
        entity="portfolio", action="explode", target_ref="p-1"
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 400


def test_execute_unknown_entity_is_validation_error():
    _set_context(_human_user())
    result = sem.tool_execute(entity="nope", action="drop")
    assert result.is_error is True
    assert result.structured_content["status_code"] == 400
