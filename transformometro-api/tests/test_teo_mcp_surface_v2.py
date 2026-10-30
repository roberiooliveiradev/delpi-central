"""TÉO MCP Surface V2 — capability-driven registration and no generic proxy."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.governed_writes.proposal_store import reset_proposal_store_for_tests
from tm_app.interface.mcp.constants import (
    MCP_LEGACY_REMOVED_TOOLS,
    MCP_SURFACE_BUDGET,
    MCP_TOOL_NAMES,
    MCP_V2_REMOVED_TOOLS,
    TEO_MCP_SURFACE,
    TOOL_CLASS,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp.tool_bridge import (
    tool_commit_proposal,
    tool_prepare_record_change,
)


def test_surface_budget_and_taxonomy() -> None:
    # Semantic V3 ONLY (issue #124 — final cutover): the six semantic
    # tools are the entire public surface; the V2 family names are
    # tombstoned (bridge functions remain internal adapters).
    assert TEO_MCP_SURFACE == "SEMANTIC_V3_ONLY"
    assert MCP_SURFACE_BUDGET["before_total"] == 33
    assert MCP_SURFACE_BUDGET["after_total"] == 6
    assert len(MCP_TOOL_NAMES) == 6
    assert TOOL_CLASS["get_context"] == "DISCOVERY"
    assert TOOL_CLASS["read"] == "READ"
    assert TOOL_CLASS["analyze"] == "ANALYSIS"
    assert TOOL_CLASS["knowledge"] == "READ"
    assert TOOL_CLASS["execute"] == "ACT"
    assert TOOL_CLASS["delete"] == "ACT"
    assert sum(1 for v in TOOL_CLASS.values() if v == "DISCOVERY") == 1
    assert sum(1 for v in TOOL_CLASS.values() if v == "READ") == 2
    assert sum(1 for v in TOOL_CLASS.values() if v == "ANALYSIS") == 1
    assert sum(1 for v in TOOL_CLASS.values() if v == "PREPARE") == 0
    assert sum(1 for v in TOOL_CLASS.values() if v == "ACT") == 2
    for name in MCP_LEGACY_REMOVED_TOOLS:
        assert name not in TOOL_CLASS
    for name in MCP_V2_REMOVED_TOOLS:
        assert name not in TOOL_CLASS


def test_no_generic_proxy_tools_registered() -> None:
    banned = {
        "execute_capability",
        "invoke_tool",
        "run_action",
        "call_any",
        "generic_http",
        "sql",
        "call_any_route",
    }
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    assert banned.isdisjoint(names)
    assert MCP_LEGACY_REMOVED_TOOLS.isdisjoint(names)
    assert MCP_V2_REMOVED_TOOLS.isdisjoint(names)


def test_prepare_record_change_delegates_to_shared_facade() -> None:
    reset_proposal_store_for_tests()
    user_token = set_current_user(
        SimpleNamespace(
            id="u1",
            email="teo@example.com",
            name="Téo",
            roles=[],
            groups=[],
            permissions=["transformometro.access"],
            is_superadmin=False,
        )
    )
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._governed.prepare_record_change",
            return_value={
                "status": "proposal_ready",
                "proposal": {
                    "handle": "opaque.handle",
                    "act_allowed": True,
                    "capability": "create_record",
                },
            },
        ) as prep:
            result = tool_prepare_record_change(
                entity="process_document",
                operation="create",
                changes={"titulo": "Doc"},
            )
        assert result.is_error is False
        prep.assert_called_once()
        kwargs = prep.call_args.kwargs
        assert kwargs["entity"] == "process_document"
        assert kwargs["operation"] == "create"
        data = result.structured_content["data"]
        assert data["status"] == "proposal_ready"
        assert data["proposal"]["handle"] == "opaque.handle"
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
        reset_proposal_store_for_tests()


def test_commit_proposal_rejects_confirmation_false() -> None:
    user_token = set_current_user(
        SimpleNamespace(
            id="u1",
            email="teo@example.com",
            name="Téo",
            roles=[],
            groups=[],
            permissions=["transformometro.access"],
            is_superadmin=False,
        )
    )
    auth_token = set_request_authorization("Bearer test")
    reset_proposal_store_for_tests()
    try:
        # CONFIRM_BEFORE_ACT proposals still require explicit confirmation.
        # Prepare a real destructive proposal (delete_record) so the
        # canonical execution_policy sealed on the proposal is exercised.
        import tm_app.interface.mcp.tool_bridge as bridge

        with (
            patch.object(bridge._governed._dispatch, "_require_capability"),
            patch(
                "tm_app.interface.http.branch_access_http."
                "require_transformometro_view_access",
                return_value=None,
            ),
            patch.object(
                bridge._governed._dispatch,
                "get_record",
                return_value={"id": "doc-1", "processo_id": "p1"},
            ),
        ):
            prepared = bridge.tool_prepare_delete_record(
                entity="process_document", id="doc-1"
            )
        pdata = prepared.structured_content["data"]
        handle = pdata["proposal"]["handle"]
        assert pdata["proposal"]["execution_policy"] == "confirm_before_act"

        result = tool_commit_proposal(handle, confirmation=False)
        assert result.is_error is True
        msg = (result.structured_content or {}).get("message", "")
        assert "confirmation" in msg.lower() or "CONFIRMATION" in str(
            result.structured_content
        )
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
        reset_proposal_store_for_tests()


def test_semantic_v3_tools_registered() -> None:
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    assert names == {
        "get_context", "read", "analyze", "knowledge",
        "execute", "delete",
    }


def _read_tool():
    tools = asyncio.run(create_mcp_server().list_tools())
    return next(t for t in tools if t.name == "read")


def test_read_publishes_per_parameter_descriptions() -> None:
    """The Semantic V3 ``read`` tool publishes field-level semantics for
    its typed routing arguments; entity-specific filter fields travel
    inside ``params`` (described in prose + the live catalog)."""
    tool = _read_tool()
    props = tool.input_schema.get("properties", {})
    expected = {"entity", "action", "params"}
    assert expected <= set(props)
    for name in expected:
        description = props[name].get("description")
        assert isinstance(description, str) and description.strip(), (
            f"read.{name} publishes no field description"
        )
