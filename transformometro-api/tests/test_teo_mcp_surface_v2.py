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
    TEO_MCP_SURFACE,
    TOOL_CLASS,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp.tool_bridge import (
    tool_commit_proposal,
    tool_prepare_record_change,
)


def test_surface_budget_and_taxonomy() -> None:
    assert TEO_MCP_SURFACE == "CAPABILITY_GOVERNED_V2"
    assert MCP_SURFACE_BUDGET["before_total"] == 33
    assert MCP_SURFACE_BUDGET["after_total"] == 20
    assert len(MCP_TOOL_NAMES) == 20
    assert TOOL_CLASS["prepare_record_change"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"
    assert sum(1 for v in TOOL_CLASS.values() if v == "READ") == 10
    assert sum(1 for v in TOOL_CLASS.values() if v == "ANALYSIS") == 1
    assert sum(1 for v in TOOL_CLASS.values() if v == "PREPARE") == 8
    assert sum(1 for v in TOOL_CLASS.values() if v == "ACT") == 1
    for name in MCP_LEGACY_REMOVED_TOOLS:
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
        assert result.isError is False
        prep.assert_called_once()
        kwargs = prep.call_args.kwargs
        assert kwargs["entity"] == "process_document"
        assert kwargs["operation"] == "create"
        data = result.structuredContent["data"]
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
    try:
        result = tool_commit_proposal("any.handle", confirmation=False)
        assert result.isError is True
        msg = (result.structuredContent or {}).get("message", "")
        assert "confirmation" in msg.lower() or "CONFIRMATION" in str(
            result.structuredContent
        )
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)


def test_specialized_prepares_still_registered() -> None:
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    for required in (
        "prepare_activate_revision",
        "prepare_improvement_package",
        "prepare_manage_evidence",
        "prepare_meeting_minute_workflow",
        "prepare_meeting_minute_manage",
        "prepare_adjust_shared_resource_cost",
        "prepare_recalculate_dashboard",
        "search_records",
        "get_record",
        "get_process_context",
        "analyze",
    ):
        assert required in names
