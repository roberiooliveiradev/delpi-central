"""TÉO MCP methodology guide — READ-only playbooks, not domain truth."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.responses import JSONResponse

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.application.methodology.guide import (
    list_method_ids,
    query_methodology_guide,
)
from tm_app.interface.mcp.constants import (
    GPT_TO_MCP_TOOLS,
    MCP_NATIVE_TOOLS,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp.tool_bridge import tool_get_methodology_guide

_REQUIRED_KEYS = {
    "id",
    "name",
    "purpose",
    "when_to_use",
    "when_not_to_use",
    "required_inputs",
    "questions",
    "steps",
    "outputs",
    "evidence_rules",
    "common_mistakes",
    "transformometro_mapping",
}

_EXPECTED_METHODS = {
    "macroprocess",
    "key_process",
    "end_to_end",
    "sipoc",
    "lean",
    "ishikawa",
    "five_whys",
    "ctp",
    "tdr",
    "kpi",
    "swot",
    "as_is",
    "to_be",
}


def test_method_catalog_matches_canonical_playbook_projection() -> None:
    assert set(list_method_ids()) == _EXPECTED_METHODS
    assert MCP_NATIVE_TOOLS == frozenset()
    assert GPT_TO_MCP_TOOLS["gpt_get_methodology_guide"] == ("get_methodology_guide",)
    assert TOOL_CLASS["get_methodology_guide"] == "READ"
    assert len(MCP_TOOL_NAMES) == 33


@pytest.mark.parametrize(
    "method_id",
    ["sipoc", "ishikawa", "five_whys", "lean", "kpi"],
)
def test_specific_method_is_compact_and_read_only(method_id: str) -> None:
    data = query_methodology_guide(method=method_id)
    method = data["method"]
    assert data["read_only"] is True
    assert data["writes"] is False
    assert data["authority"] == "GUIDANCE_NOT_SOURCE_OF_TRUTH"
    assert method["id"] == method_id
    assert method["persists"] is False
    assert method["authorizes"] is False
    assert _REQUIRED_KEYS <= set(method)
    assert "INFERRED != FACT" in data["invariants"]
    assert "TO-BE != PRODUCTION STATE" in data["invariants"]
    blob = json.dumps(data)
    assert "transformometro.view" not in blob
    assert "client_secret" not in blob
    assert "BEGIN " not in blob
    assert "get_catalog.diagram_catalog" in blob
    assert "start_event" not in blob


def test_router_lists_methods_without_dumping_full_steps() -> None:
    data = query_methodology_guide()
    assert data["selection"] == "router"
    assert {item["id"] for item in data["methods"]} == _EXPECTED_METHODS
    assert "steps" not in data["methods"][0]
    assert "CHOOSE MINIMUM METHOD" in data["conversational_flow"]


def test_task_diagnose_recommends_cause_methods_not_writes() -> None:
    data = query_methodology_guide(task="diagnose")
    assert data["recommended_method_ids"] == ["ishikawa", "five_whys", "lean"]
    assert data["writes"] is False


def test_portuguese_alias_resolves_to_canonical_id() -> None:
    data = query_methodology_guide(method="processos_chave")
    assert data["method"]["id"] == "key_process"


def test_unknown_method_is_governed_validation() -> None:
    with pytest.raises(ValueError, match="Unknown methodology method"):
        query_methodology_guide(method="get_any_prompt")


def test_unknown_task_is_governed_validation() -> None:
    with pytest.raises(ValueError, match="Unknown methodology task"):
        query_methodology_guide(task="authorize_write")


def test_tool_registered_read_only_and_not_an_act() -> None:
    mcp = create_mcp_server()
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    assert len(tools) == 33
    guide = tools["get_methodology_guide"]
    assert guide.annotations is not None
    assert guide.annotations.readOnlyHint is True
    assert guide.annotations.destructiveHint is False
    assert "proposal_handle" not in (guide.description or "")


def _user():
    return SimpleNamespace(
        id="u1",
        email="teo@example.com",
        name="Téo",
        roles=[],
        groups=[],
        permissions=["transformometro.view"],
        is_superadmin=False,
    )


def test_bridge_requires_authentication() -> None:
    result = tool_get_methodology_guide(method="sipoc")
    assert result.isError is True
    assert result.structuredContent["status_code"] == 401


def test_bridge_forbidden_does_not_return_playbook() -> None:
    user_token = set_current_user(_user())
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=JSONResponse({"message": "denied"}, status_code=403),
        ):
            result = tool_get_methodology_guide(method="lean")
        assert result.isError is True
        assert result.structuredContent["status_code"] == 403
        assert "purpose" not in json.dumps(result.structuredContent)
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)


def test_bridge_returns_sipoc_without_write_fields() -> None:
    user_token = set_current_user(_user())
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=None,
        ):
            result = tool_get_methodology_guide(method="sipoc")
        assert result.isError is False
        data = result.structuredContent["data"]
        assert data["method"]["id"] == "sipoc"
        assert data["writes"] is False
        assert "act_" not in json.dumps(data["method"]["steps"])
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
