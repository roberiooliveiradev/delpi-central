"""Portal Transforma+ ↔ TÉO capability parity — tasks + interaction room.

TRANSFORMÔMETRO — TÉO/PORTAL CAPABILITY PARITY:
- Same canonical use cases as the Portal HTTP routes (no duplicated rules).
- Governed PREPARE → commit_proposal ACT per capability execution_policy.
- Catalog exposure_classification replaces the generic NOT_EXPOSED bucket.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
)
from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    CONFIRM_BEFORE_ACT,
    execution_policy_for_capability,
)
from tm_app.application.governed_writes.orchestrator import (
    INTERACTION_ROOM_ACTION_TO_CAPABILITY,
    INTERACTION_ROOM_CAPABILITIES,
    TASK_ACTION_TO_CAPABILITY,
    TASK_CAPABILITIES,
    WRITE_CAPABILITIES,
)
from tm_app.application.intelligence.capability_registry import (
    CAPABILITY_BINDINGS,
    actions_parity,
)
from tm_app.application.use_cases.manage_interaction_rooms import (
    InteractionRoomUseCases,
)
from tm_app.application.use_cases.manage_transformometro_tasks import (
    TaskCommandUseCases,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.interface.http.routes import interaction_room_routes, task_routes
from tm_app.interface.mcp.constants import (
    MCP_TOOL_NAMES,
    PREPARE_TOOL_CAPABILITY,
    TOOL_CLASS,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp import tool_bridge


# ---------------------------------------------------------------- policy


def test_task_execution_policy_classification() -> None:
    assert execution_policy_for_capability("create_task") == AUTO_ACT
    assert execution_policy_for_capability("update_task") == AUTO_ACT
    assert execution_policy_for_capability("complete_task") == AUTO_ACT
    assert execution_policy_for_capability("cancel_task") == CONFIRM_BEFORE_ACT


def test_interaction_room_execution_policy_classification() -> None:
    for cap in (
        "open_interaction_room",
        "post_interaction_message",
        "edit_interaction_message",
        "toggle_interaction_reaction",
        "pin_interaction_message",
        "unpin_interaction_message",
        "mark_interaction_read",
    ):
        assert execution_policy_for_capability(cap) == AUTO_ACT, cap
    assert (
        execution_policy_for_capability("delete_interaction_message")
        == CONFIRM_BEFORE_ACT
    )


def test_new_capabilities_are_governed_write_capabilities() -> None:
    assert TASK_CAPABILITIES <= WRITE_CAPABILITIES
    assert INTERACTION_ROOM_CAPABILITIES <= WRITE_CAPABILITIES
    assert set(TASK_ACTION_TO_CAPABILITY.values()) == TASK_CAPABILITIES
    assert (
        set(INTERACTION_ROOM_ACTION_TO_CAPABILITY.values())
        == INTERACTION_ROOM_CAPABILITIES
    )


# ---------------------------------------------------------------- registry


def test_registry_bindings_cover_task_and_room() -> None:
    by_id = {b.id: b for b in CAPABILITY_BINDINGS}
    assert by_id["task.read"].actions_operation == "gpt_task_read"
    assert by_id["task.change.prepare"].actions_operation == "gpt_prepare_task"
    assert (
        by_id["interaction_room.read"].actions_operation
        == "gpt_interaction_room_read"
    )
    assert (
        by_id["interaction_room.change.prepare"].actions_operation
        == "gpt_prepare_interaction_room"
    )
    parity = actions_parity()
    assert parity["gpt_task_read"] == ("task_read",)
    assert parity["gpt_prepare_task"] == ("prepare_task",)
    assert parity["gpt_interaction_room_read"] == ("interaction_room_read",)
    assert parity["gpt_prepare_interaction_room"] == (
        "prepare_interaction_room",
    )


def test_mcp_tool_registration_and_classes() -> None:
    assert "task_read" in MCP_TOOL_NAMES
    assert "prepare_task" in MCP_TOOL_NAMES
    assert "interaction_room_read" in MCP_TOOL_NAMES
    assert "prepare_interaction_room" in MCP_TOOL_NAMES
    assert TOOL_CLASS["task_read"] == "READ"
    assert TOOL_CLASS["prepare_task"] == "PREPARE"
    assert TOOL_CLASS["interaction_room_read"] == "READ"
    assert TOOL_CLASS["prepare_interaction_room"] == "PREPARE"
    assert "prepare_task" in PREPARE_TOOL_CAPABILITY
    assert "prepare_interaction_room" in PREPARE_TOOL_CAPABILITY
    tools = asyncio.run(create_mcp_server().list_tools())
    names = {t.name for t in tools}
    assert {
        "task_read",
        "prepare_task",
        "interaction_room_read",
        "prepare_interaction_room",
    } <= names
    assert len(names) == len(MCP_TOOL_NAMES)


def test_no_generic_proxy_tools() -> None:
    forbidden = {
        "execute_capability",
        "invoke_tool",
        "run_action",
        "call_any",
        "generic_http",
        "sql",
        "call_any_route",
        "http_proxy",
    }
    assert not (forbidden & set(MCP_TOOL_NAMES))
    assert not (forbidden & set(GPT_ACTIONS_OPERATION_IDS))


def test_actions_openapi_contains_new_operations() -> None:
    doc = build_gpt_actions_openapi()
    op_ids = {
        op.get("operationId")
        for methods in doc["paths"].values()
        for op in methods.values()
    }
    assert {
        "gpt_task_read",
        "gpt_prepare_task",
        "gpt_interaction_room_read",
        "gpt_prepare_interaction_room",
    } <= op_ids


# ---------------------------------------------------------------- catalog


def test_catalog_exposure_classification() -> None:
    for transport in ("gpt_actions", "mcp"):
        catalog = build_capability_surface_catalog(transport)
        ec = catalog["exposure_classification"]
        exposed = {item["id"] for item in ec["exposed"]}
        assert {"tm_task", "interaction_room"} <= exposed
        nna = {item["id"] for item in ec["intentionally_not_applicable"]}
        assert "process_workspace" in nna
        blocked = {item["id"] for item in ec["platform_blocked"]}
        assert "interaction_room.attachment_binary" in blocked
        token_flow = {item["id"] for item in ec["public_token_flow"]}
        assert "public_meeting_minute_signing" in token_flow
        assert "not_exposed_by_design" not in catalog
        wf = {w["id"]: w for w in catalog["workflows"]}
        assert wf["manage_task"]["execution_policy"]["cancel_task"] == (
            "confirm_before_act"
        )
        assert wf["manage_task"]["confirmation_requirement"] == "mixed"
        assert wf["interaction_room"]["execution_policy"][
            "delete_interaction_message"
        ] == "confirm_before_act"


# ------------------------------------------------------------ authority


def test_portal_and_teo_share_same_use_case_classes() -> None:
    """TÉO dispatch delegates to the SAME canonical use-case classes the
    Portal routes instantiate — no parallel implementation."""
    assert isinstance(task_routes._commands, TaskCommandUseCases)
    assert isinstance(interaction_room_routes._rooms, InteractionRoomUseCases)
    dispatch = GptActionsDispatchService()
    assert type(dispatch._tasks) is type(task_routes._commands)
    assert type(dispatch._rooms) is type(interaction_room_routes._rooms)


# ------------------------------------------------------- PREPARE / ACT


def _user_context(*, permissions: list[str] | None = None):
    user_token = set_current_user(
        SimpleNamespace(
            id="u1",
            email="teo@example.com",
            name="Téo",
            roles=[],
            groups=[],
            permissions=(
                permissions
                if permissions is not None
                else ["transformometro.access"]
            ),
            is_superadmin=False,
        )
    )
    auth_token = set_request_authorization("Bearer test")
    return user_token, auth_token


def _reset_context(tokens) -> None:
    user_token, auth_token = tokens
    reset_request_authorization(auth_token)
    reset_current_user(user_token)
    reset_proposal_store_for_tests()


def _payload(result):
    return result.structured_content


def test_task_create_auto_act_prepare_commit_chain() -> None:
    tokens = _user_context()
    try:
        created = {"id": "task-1", "title": "Follow up", "status": "pending"}
        with patch.object(
            tool_bridge._dispatch, "task_write", return_value=created
        ) as write, patch.object(
            tool_bridge._dispatch, "get_task", return_value=created
        ):
            prep = tool_bridge.tool_prepare_task(
                action="create", title="Follow up"
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert data["proposal"]["execution_policy"] == "auto_act"
            handle = data["proposal"]["handle"]
            committed = tool_bridge.tool_commit_proposal(
                handle, confirmation=False
            )
            result = _payload(committed)
            assert result["success"] is True
            write.assert_called_once()
        assert _payload(committed)["data"]["persisted"] is True
        assert _payload(committed)["data"]["postcondition"]["verified"] is True
    finally:
        _reset_context(tokens)


def test_task_cancel_requires_explicit_confirmation() -> None:
    tokens = _user_context()
    try:
        current = {"id": "task-1", "status": "pending"}
        cancelled = {"id": "task-1", "status": "cancelled"}
        with patch.object(
            tool_bridge._dispatch, "get_task", return_value=current
        ), patch.object(
            tool_bridge._dispatch, "task_write", return_value=cancelled
        ):
            prep = tool_bridge.tool_prepare_task(
                action="cancel", task_id="task-1"
            )
            data = _payload(prep)["data"]
            assert data["proposal"]["execution_policy"] == "confirm_before_act"
            handle = data["proposal"]["handle"]
            denied = tool_bridge.tool_commit_proposal(
                handle, confirmation=False
            )
            assert _payload(denied)["success"] is False
            assert (
                _payload(denied)["data"].get("error_code")
                == "CONFIRMATION_REQUIRED"
            )
    finally:
        _reset_context(tokens)


def test_task_prepare_negative_authz() -> None:
    tokens = _user_context(permissions=[])
    try:
        result = tool_bridge.tool_prepare_task(action="create", title="x")
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] in (401, 403)
    finally:
        _reset_context(tokens)


def test_interaction_room_post_message_auto_act_chain() -> None:
    tokens = _user_context()
    try:
        room = {"id": "room-1", "processo_id": "p1", "unread_count": 0}
        message = {"id": "m1", "room_id": "room-1", "content": "hi"}
        with patch.object(
            tool_bridge._dispatch, "get_room", return_value=room
        ), patch.object(
            tool_bridge._dispatch, "room_write", return_value=message
        ) as write:
            prep = tool_bridge.tool_prepare_interaction_room(
                action="post_message", room_id="room-1", content="hi"
            )
            data = _payload(prep)["data"]
            assert data["persisted"] is False
            assert data["proposal"]["execution_policy"] == "auto_act"
            committed = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            assert _payload(committed)["success"] is True
            write.assert_called_once()
    finally:
        _reset_context(tokens)


def test_interaction_room_delete_message_requires_confirmation() -> None:
    tokens = _user_context()
    try:
        message = {"id": "m1", "room_id": "room-1", "content": "hi"}
        with patch.object(
            tool_bridge._dispatch, "get_room_message", return_value=message
        ), patch.object(
            tool_bridge._dispatch,
            "room_write",
            return_value={"id": "m1", "deleted_at": "2026-01-01T00:00:00"},
        ):
            prep = tool_bridge.tool_prepare_interaction_room(
                action="delete_message", room_id="room-1", message_id="m1"
            )
            data = _payload(prep)["data"]
            assert data["proposal"]["execution_policy"] == "confirm_before_act"
            denied = tool_bridge.tool_commit_proposal(
                data["proposal"]["handle"], confirmation=False
            )
            assert _payload(denied)["success"] is False
    finally:
        _reset_context(tokens)


def test_interaction_room_prepare_rejects_unknown_action() -> None:
    tokens = _user_context()
    try:
        result = tool_bridge.tool_prepare_interaction_room(
            action="upload_attachment", room_id="r1"
        )
        payload = _payload(result)
        assert payload["success"] is False
        assert payload["status_code"] == 400
    finally:
        _reset_context(tokens)


def test_task_read_routes_to_canonical_dispatch() -> None:
    tokens = _user_context()
    try:
        with patch.object(
            tool_bridge._dispatch,
            "list_my_tasks",
            return_value={"items": [], "total": 0},
        ) as read:
            result = tool_bridge.tool_task_read(action="mine")
            assert _payload(result)["success"] is True
            read.assert_called_once()
        missing = tool_bridge.tool_task_read(action="get")
        assert _payload(missing)["success"] is False
        assert _payload(missing)["status_code"] == 400
    finally:
        _reset_context(tokens)


def test_agent_intelligence_flows_reference_real_tools() -> None:
    content = json.load(
        open("tm_app/content/teo_agent_intelligence.json", encoding="utf-8")
    )
    mcp_names = set(MCP_TOOL_NAMES)
    actions_names = set(GPT_ACTIONS_OPERATION_IDS)
    for flow_id in ("tasks", "interaction_room"):
        flow = content["flows"][flow_id]
        assert set(flow["mcp_tools"]) <= mcp_names, flow_id
        assert set(flow["gpt_operations"]) <= actions_names, flow_id
    assert "tasks" not in content["not_exposed"]
    assert "interaction_room" not in content["not_exposed"]
