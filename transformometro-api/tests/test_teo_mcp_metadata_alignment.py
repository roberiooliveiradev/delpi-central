"""TÉO MCP metadata / response-copy alignment — contract tests.

TEO-MCP-METADATA-RESPONSE-FINAL-ALIGNMENT-06: descriptions, PREPARE
response copy and catalog metadata must describe the canonical
execution_policy — never a universal "always confirm" rule and never
legacy ACT tool names. Metadata describes the policy; it is not policy.
"""

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

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp.tool_bridge import (
    _prepared_message,
    tool_prepare_record_change,
)


def _tool_descriptions() -> dict[str, str]:
    tools = asyncio.run(create_mcp_server().list_tools())
    return {t.name: (t.description or "") for t in tools}


def test_r1_prepare_record_change_description_is_policy_aware() -> None:
    desc = _tool_descriptions()["prepare_record_change"]
    assert "after confirmation" not in desc
    assert "execution_policy" in desc
    assert "auto_act" in desc and "confirm_before_act" in desc


def test_r2_adjust_shared_resource_cost_is_auto_act() -> None:
    # Family tool: execution_policy is per action; adjust_shared_resource_cost
    # stays auto_act inside prepare_governed_operation.
    desc = _tool_descriptions()["prepare_governed_operation"]
    assert "after confirmation" not in desc
    assert "auto_act" in desc
    assert "adjust_shared_resource_cost" in desc


def test_r3_create_diagnostic_is_auto_act() -> None:
    desc = _tool_descriptions()["prepare_diagnostic_change"]
    assert "auto_act" in desc


def test_r4_manage_diagnostic_is_confirm_before_act() -> None:
    desc = _tool_descriptions()["prepare_diagnostic_change"]
    assert "confirm_before_act" in desc
    assert "explicit" in desc and "confirmation" in desc


def test_r5_no_legacy_act_tool_names_in_active_metadata() -> None:
    blob = " ".join(_tool_descriptions().values())
    assert "act_meeting_minute_manage" not in blob
    assert "act_create_record" not in blob
    assert "act_update_record" not in blob
    assert "act_delete_record" not in blob
    assert "act_duplicate_record" not in blob


def _prepare_with_policy(execution_policy: str, explicit: bool):
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
                "persisted": False,
                "proposal": {
                    "handle": "opaque.handle",
                    "act_allowed": True,
                    "execution_policy": execution_policy,
                    "confirmation_requirement": {
                        "explicit_user_confirmation": explicit
                    },
                },
            },
        ):
            return tool_prepare_record_change(
                entity="process_document",
                operation="create",
                changes={"title": "Doc"},
            )
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
        reset_proposal_store_for_tests()


def test_r6_auto_act_prepare_message_never_asks_confirmation() -> None:
    result = _prepare_with_policy("auto_act", explicit=False)
    data = result.structured_content["data"]
    assert data["persisted"] is False
    assert data["proposal"]["execution_policy"] == "auto_act"
    msg = result.structured_content["message"].lower()
    assert "confirm with" not in msg
    assert "confirmation is required" not in msg
    assert "no additional user confirmation" in msg


def test_r6_confirm_before_act_prepare_message_requires_confirmation() -> None:
    result = _prepare_with_policy("confirm_before_act", explicit=True)
    msg = result.structured_content["message"].lower()
    assert "explicit user confirmation" in msg
    assert "required" in msg


def test_prepared_message_defaults_safe_without_policy() -> None:
    msg = _prepared_message({"proposal": {"handle": "h", "act_allowed": True}})
    assert "confirmation is required" in msg.lower()


def test_r7_diagnostic_aggregate_metadata_is_per_capability() -> None:
    for transport in ("gpt_actions", "mcp"):
        catalog = build_capability_surface_catalog(transport)
        diag = next(
            c for c in catalog["mcp_only_capabilities"] if c["id"] == "diagnostic_v1"
        )
        assert diag["execution_policy"] == {
            "create_diagnostic": "auto_act",
            "manage_diagnostic": "confirm_before_act",
        }
        assert diag["confirmation_requirement"] != True  # noqa: E712
        assert diag["confirmation_requirement"] == "mixed"


def test_r8_write_flow_mcp_does_not_require_confirmation_flag() -> None:
    import json

    content = json.load(
        open("tm_app/content/teo_agent_intelligence.json", encoding="utf-8")
    )
    commit = content["write_flow_mcp"]["commit"]
    assert "protocol ack" not in commit
    assert "confirmation=true" not in commit
    assert "auto_act" in commit and "confirm_before_act" in commit


def test_r9_meeting_minute_read_metadata_matches_canonical_read_set() -> None:
    """CONTRACT-DRIFT regression: tool description, canonical set and
    runtime vocabulary must be identical for meeting_minute_read."""
    from tm_app.application.governed_writes.orchestrator import (
        MEETING_MINUTE_READ_ACTIONS,
    )

    desc = _tool_descriptions()["meeting_minute_read"]
    for action in MEETING_MINUTE_READ_ACTIONS:
        assert action in desc, f"{action} missing from tool description"
    for write_action in (
        "resend",
        "create_version",
        "set_participants",
        "set_signers",
        "send",
        "finalize",
        "cancel",
    ):
        assert write_action not in desc, (
            f"write action {write_action} must not appear in READ metadata"
        )


def test_r11_meeting_minute_read_inputschema_enum_is_canonical() -> None:
    """MCP inputSchema.action.enum must equal the canonical READ set —
    same source as catalog, OpenAPI and runtime validation."""
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )
    from tm_app.application.gpt_actions.openapi_builder import (
        build_gpt_actions_openapi,
    )
    from tm_app.application.gpt_actions.parity_capabilities_service import (
        MEETING_MINUTE_READ_ACTION_VALUES,
    )
    from tm_app.application.governed_writes.orchestrator import (
        MEETING_MINUTE_READ_ACTIONS,
    )

    canonical = set(MEETING_MINUTE_READ_ACTION_VALUES)
    assert set(MEETING_MINUTE_READ_ACTIONS) == canonical

    # Generated MCP inputSchema (the real contract the client receives).
    tools = asyncio.run(create_mcp_server().list_tools())
    tool = next(t for t in tools if t.name == "meeting_minute_read")
    schema = getattr(tool, "input_schema", None) or getattr(
        tool, "inputSchema"
    )
    mcp_enum = set(schema["properties"]["action"]["enum"])
    assert mcp_enum == canonical

    # OpenAPI projection.
    doc = build_gpt_actions_openapi()
    openapi_enum = set(
        doc["components"]["schemas"]["GptMeetingMinuteReadBody"]["properties"][
            "action"
        ]["enum"]
    )
    assert openapi_enum == canonical

    # Catalog projection.
    catalog = build_capability_surface_catalog()
    minute = next(
        c
        for c in catalog["workflows"]
        if isinstance(c, dict) and c.get("id") == "meeting_minute_manage"
    )
    assert set(minute["read_actions"]) == canonical

    # WRITE actions must not leak into the READ enum.
    for write_action in (
        "send",
        "finalize",
        "cancel",
        "resend",
        "create_version",
        "set_participants",
        "set_signers",
    ):
        assert write_action not in mcp_enum


def test_r10_meeting_minute_read_rejects_write_actions() -> None:
    """meeting_minute_read must fail-closed on write/unknown actions and
    never reach the dispatch layer."""
    from tm_app.interface.mcp import tool_bridge

    with patch.object(tool_bridge._dispatch, "manage_meeting_minute") as disp:
        for action in (
            "resend",
            "create_version",
            "set_participants",
            "set_signers",
            "send",
            "finalize",
            "cancel",
            "bogus",
        ):
            result = tool_bridge.tool_meeting_minute_read(
                action=action, minute_id="m1", data={}
            )
            assert result.is_error, f"{action} must be rejected"
            text = result.content[0].text
            assert "prepare_meeting_minute_change" in text or "READ" in text
        disp.assert_not_called()
