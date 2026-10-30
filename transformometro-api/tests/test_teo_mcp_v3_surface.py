"""TÉO Semantic MCP V3 — six semantic tools over governed capabilities.

Contract, routing parity, execution-policy gating, destructive-delete
classification and multi-action orchestration — all over the canonical
orchestrator/policy modules (no parallel authority).
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

from tm_app.application.governed_writes.confirmation_policy import (
    delete_operations,
    is_destructive_delete,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.interface.mcp.constants import (
    MCP_TOOL_NAMES,
    TOOL_CLASS,
    V3_SEMANTIC_TOOL_NAMES,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp import tool_bridge_v3 as v3


def _auth_context():
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
    return user_token, auth_token


def _cleanup(tokens):
    user_token, auth_token = tokens
    reset_request_authorization(auth_token)
    reset_current_user(user_token)
    reset_proposal_store_for_tests()


# --- Registration / taxonomy -------------------------------------------------


def test_v3_tools_registered_semantic_only() -> None:
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    assert V3_SEMANTIC_TOOL_NAMES <= names
    assert len(names) == len(MCP_TOOL_NAMES) == 6
    assert TOOL_CLASS["get_context"] == "DISCOVERY"
    assert TOOL_CLASS["read"] == "READ"
    assert TOOL_CLASS["analyze"] == "ANALYSIS"
    assert TOOL_CLASS["knowledge"] == "READ"
    assert TOOL_CLASS["execute"] == "ACT"
    assert TOOL_CLASS["delete"] == "ACT"


def test_v3_analyze_is_single_unified_tool() -> None:
    names = [t.name for t in asyncio.run(create_mcp_server().list_tools())]
    assert names.count("analyze") == 1


def test_delete_operations_closed_set() -> None:
    assert is_destructive_delete("delete_record")
    assert is_destructive_delete("manage_evidence", "delete")
    assert is_destructive_delete("helpdesk_delete_ticket")
    assert is_destructive_delete("delete_interaction_room")
    # Consequential-but-not-delete ops stay on execute.
    assert not is_destructive_delete("cancel_task")
    assert not is_destructive_delete("remove_room_participant")
    assert not is_destructive_delete("helpdesk_reject_solution")
    assert not is_destructive_delete("meeting_minute_workflow", "cancel")
    assert not is_destructive_delete("nonexistent_capability")
    assert {c for c, _ in delete_operations()} == {
        "delete_record",
        "manage_evidence",
        "delete_interaction_message",
        "delete_interaction_room",
        "helpdesk_delete_ticket",
        "helpdesk_unlink_glpi_session",
    }


# --- get_context ---------------------------------------------------------------


def test_get_context_sections() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._user_context.get_my_context",
            return_value={"name": "Téo"},
        ), patch(
            "tm_app.interface.mcp.tool_bridge._workspace_context.get_workspace_context",
            return_value={"process_id": "p1"},
        ):
            result = v3.tool_get_context()
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["self"] == {"name": "Téo"}
            assert data["workspace"] == {"process_id": "p1"}
            assert "catalog" in data["discovery_hint"]

        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.get_catalog",
            return_value={"entities": []},
        ):
            result = v3.tool_get_context(section="catalog")
            assert result.is_error is False

        result = v3.tool_get_context(section="bogus")
        assert result.is_error is True
        assert result.structured_content["status_code"] == 400
    finally:
        _cleanup(tokens)


# --- read ------------------------------------------------------------------------


def test_read_domain_record_routes_to_record_read() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.record_read",
            return_value={"items": [{"id": "i1"}]},
        ) as rec:
            result = v3.tool_read(
                "instance", "search", {"status_instancia": "aberta"}
            )
            assert result.is_error is False
            assert rec.call_args.kwargs["action"] == "search"
            assert (
                rec.call_args.kwargs["status_instancia"] == "aberta"
            )
    finally:
        _cleanup(tokens)


def test_read_specialized_entity_routes() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._helpdesk.read_helpdesk",
            return_value={"tickets": []},
        ) as hd:
            result = v3.tool_read("helpdesk", "tickets", {"status": "1"})
            assert result.is_error is False
            assert hd.call_args.kwargs["action"] == "tickets"
            assert hd.call_args.kwargs["status"] == "1"

        with patch(
            "tm_app.interface.mcp.tool_bridge._process_context.get_context",
            return_value={"process": {}},
        ) as pc:
            result = v3.tool_read(
                "process_context", "get", {"process_id": "p1"}
            )
            assert result.is_error is False
            assert pc.call_args.kwargs["process_id"] == "p1"
    finally:
        _cleanup(tokens)


def test_read_unknown_entity_and_action_fail_typed() -> None:
    tokens = _auth_context()
    try:
        r = v3.tool_read("nonsense", "get")
        assert r.is_error is True
        assert r.structured_content["data"]["error_kind"] == "validation"

        r = v3.tool_read("helpdesk", "delete_everything")
        assert r.is_error is True
        assert "Allowed" in r.structured_content["message"]
    finally:
        _cleanup(tokens)


# --- analyze / knowledge ---------------------------------------------------------


def test_analyze_view_and_transcript() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.analyze",
            return_value={"view": "summary"},
        ) as an:
            result = v3.tool_analyze(
                "summary", {"filial_id": "f1"}
            )
            assert result.is_error is False
            assert an.call_args.kwargs["filial_id"] == "f1"

        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.manage_meeting_minute",
            return_value={"draft": "ok"},
        ) as mm:
            result = v3.tool_analyze(
                "meeting_minute_transcript",
                {"data": {"transcript": "..."}},
            )
            assert result.is_error is False
            assert (
                mm.call_args.kwargs["action"] == "generate_from_transcript"
            )
            assert mm.call_args.kwargs["read_only"] is True
    finally:
        _cleanup(tokens)


def test_knowledge_sources() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.get_methodology_guide",
            return_value={"guide": "v2"},
        ) as mg:
            result = v3.tool_knowledge(
                "methodology", {"method": "sipoc"}
            )
            assert result.is_error is False
            assert mg.call_args.kwargs["method"] == "sipoc"

        result = v3.tool_knowledge("wiki")
        assert result.is_error is True
    finally:
        _cleanup(tokens)


# --- execute ----------------------------------------------------------------------


def _fake_prepare(**overrides):
    base = {
        "proposal_handle": "h-1",
        "proposal_id": "gp_1",
        "capability": "create_task",
        "resource_type": "task",
        "resource_id": None,
        "exact_change": {"action": "create_task", "title": "T"},
        "execution_policy": "auto_act",
        "confirmation_requirement": {"explicit_user_confirmation": False},
        "expected_postcondition": {},
        "expires_at": "2099-01-01",
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
    }
    base.update(overrides)
    return base


def test_execute_auto_act_executes_in_one_call() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(),
        ) as prep, patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            return_value={
                "capability": "create_task",
                "proposal_id": "gp_1",
                "data": {"task_id": "t1"},
                "verified": True,
            },
        ) as act:
            result = v3.tool_execute(
                capability="create_task",
                args={"title": "T", "processo_id": "p1"},
            )
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["outcome"] == "executed_verified"
            assert data["data"] == {"task_id": "t1"}
            assert prep.call_args.kwargs["capability"] == "create_task"
            act.assert_called_once()
    finally:
        _cleanup(tokens)


def test_execute_confirm_before_act_returns_pending_proposal() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(
                capability="cancel_task",
                execution_policy="confirm_before_act",
            ),
        ), patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act"
        ) as act:
            result = v3.tool_execute(
                capability="cancel_task", args={"task_id": "t1"}
            )
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["outcome"] == "proposal_pending_confirmation"
            assert data["proposal"]["proposal_id"] == "gp_1"
            act.assert_not_called()
    finally:
        _cleanup(tokens)


def test_execute_entity_operation_form() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(capability="create_record"),
        ) as prep, patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            return_value={"verified": True, "data": {"id": "r1"}},
        ):
            result = v3.tool_execute(
                entity="process_document",
                operation="create",
                changes={"titulo": "Doc"},
            )
            assert result.is_error is False
            assert prep.call_args.kwargs["capability"] == "create_record"
            assert prep.call_args.kwargs["args"]["entity"] == (
                "process_document"
            )
            assert prep.call_args.kwargs["args"]["data"] == {
                "titulo": "Doc"
            }
    finally:
        _cleanup(tokens)


def test_execute_unknown_capability_fails_closed() -> None:
    tokens = _auth_context()
    try:
        result = v3.tool_execute(
            capability="drop_database", args={}
        )
        assert result.is_error is True
        assert result.structured_content["status_code"] == 400

        result = v3.tool_execute(
            entity="process_diagram", operation="create"
        )
        assert result.is_error is True
        assert "does not support" in result.structured_content["message"]
    finally:
        _cleanup(tokens)


def test_execute_family_action_alias_resolves_capability() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(capability="open_interaction_room"),
        ) as prep, patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            return_value={"verified": True, "data": {"room_id": "r1"}},
        ):
            result = v3.tool_execute(
                capability="open_room", args={"processo_id": "p1"}
            )
            assert result.is_error is False
            assert (
                prep.call_args.kwargs["capability"]
                == "open_interaction_room"
            )
    finally:
        _cleanup(tokens)


def test_execute_commit_flow_requires_confirmation_for_confirm_policy() -> None:
    tokens = _auth_context()
    try:
        proposal = SimpleNamespace(
            capability="cancel_task",
            exact_change={"action": "cancel_task", "task_id": "t1"},
            execution_policy="confirm_before_act",
        )
        with patch(
            "tm_app.interface.mcp.tool_bridge_v3.resolve_proposal_handle",
            return_value="h-1",
        ), patch(
            "tm_app.interface.mcp.tool_bridge_v3.load_valid_proposal",
            return_value=proposal,
        ), patch(
            "tm_app.interface.mcp.tool_bridge_v3._actor",
            return_value=("u1", None),
        ):
            r = v3.tool_execute(proposal_id="gp_1")
            assert r.is_error is True
            assert "confirmation" in r.structured_content["message"].lower()

            with patch(
                "tm_app.interface.mcp.tool_bridge._orchestrator.act",
                return_value={
                    "verified": True,
                    "data": {"ok": 1},
                    "capability": "cancel_task",
                    "proposal_id": "gp_1",
                },
            ):
                r = v3.tool_execute(
                    proposal_id="gp_1", confirmation=True
                )
                assert r.is_error is False
                assert (
                    r.structured_content["data"]["outcome"]
                    == "executed_verified"
                )
    finally:
        _cleanup(tokens)


# --- multi-action -------------------------------------------------------------------


def test_execute_ops_runs_sequence_and_resolves_refs() -> None:
    tokens = _auth_context()
    try:
        prepares = []
        acts = []

        def fake_prepare(request, *, capability, args):
            prepares.append((capability, dict(args)))
            return _fake_prepare(capability=capability)

        def fake_act(request, *, capability, proposal_handle):
            acts.append(capability)
            return {
                "capability": capability,
                "proposal_id": f"gp_{len(acts)}",
                "data": {"created_id": f"id-{len(acts)}"},
                "verified": True,
            }

        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            side_effect=fake_prepare,
        ), patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            side_effect=fake_act,
        ):
            result = v3.tool_execute(
                ops=[
                    {"capability": "create_task", "args": {"title": "T"}},
                    {
                        "capability": "post_message",
                        "args": {
                            "room_id": "$ops.0.data.created_id",
                            "content": "hi",
                        },
                    },
                ]
            )
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["status"] == "completed"
            assert len(data["results"]) == 2
            # Second op consumed the first op's read-back id — no invented id.
            assert prepares[1][1]["room_id"] == "id-1"
    finally:
        _cleanup(tokens)


def test_execute_ops_stops_on_failure() -> None:
    tokens = _auth_context()
    try:
        calls = []

        def fake_prepare(request, *, capability, args):
            calls.append(capability)
            if capability == "bad_cap":
                from tm_app.application.governed_writes.errors import (
                    GovernedWriteError,
                )

                raise GovernedWriteError(
                    "nope", code="validation", status_code=400
                )
            return _fake_prepare(capability=capability)

        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            side_effect=fake_prepare,
        ), patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            return_value={
                "verified": True,
                "data": {"id": "x"},
                "capability": "create_task",
            },
        ):
            result = v3.tool_execute(
                ops=[
                    {"capability": "create_task", "args": {}},
                    {"capability": "bad_cap", "args": {}},
                    {"capability": "complete_task", "args": {}},
                ]
            )
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["status"] == "partial_failed"
            assert len(data["completed"]) == 1
            # Downstream op never attempted; unknown capability is
            # rejected at the resolution gate (fail-closed).
            assert calls == ["create_task"]
            assert data["failed"]["op"]["capability"] == "bad_cap"
            assert len(data["remaining"]) == 1
    finally:
        _cleanup(tokens)


def test_execute_ops_pauses_on_pending_confirmation() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            side_effect=lambda request, *, capability, args: _fake_prepare(
                capability=capability,
                execution_policy=(
                    "confirm_before_act"
                    if capability == "cancel_task"
                    else "auto_act"
                ),
            ),
        ), patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act",
            return_value={"verified": True, "data": {}},
        ) as act:
            result = v3.tool_execute(
                ops=[
                    {"capability": "create_task", "args": {}},
                    {"capability": "cancel_task", "args": {}},
                    {"capability": "complete_task", "args": {}},
                ]
            )
            data = result.structured_content["data"]
            assert data["status"] == "pending_confirmation"
            assert data["current"]["outcome"] == (
                "proposal_pending_confirmation"
            )
            assert len(data["remaining"]) == 1
            # Only the auto_act op executed.
            assert act.call_count == 1
    finally:
        _cleanup(tokens)


# --- delete -------------------------------------------------------------------------


def test_delete_entity_path_returns_pending_proposal() -> None:
    tokens = _auth_context()
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(
                capability="delete_record",
                execution_policy="confirm_before_act",
            ),
        ) as prep, patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.act"
        ) as act:
            result = v3.tool_delete(
                entity="process_document", record_id="d1"
            )
            assert result.is_error is False
            data = result.structured_content["data"]
            assert data["outcome"] == "proposal_pending_confirmation"
            assert prep.call_args.kwargs["capability"] == "delete_record"
            assert prep.call_args.kwargs["args"]["id"] == "d1"
            act.assert_not_called()
    finally:
        _cleanup(tokens)


def test_delete_rejects_non_delete_capabilities() -> None:
    tokens = _auth_context()
    try:
        for cap in ("cancel_task", "remove_room_participant",
                    "helpdesk_reject_solution", "create_task"):
            result = v3.tool_delete(capability=cap, args={})
            assert result.is_error is True, cap
            assert "not a destructive-delete" in (
                result.structured_content["message"]
            )
    finally:
        _cleanup(tokens)


def test_delete_evidence_requires_delete_operation() -> None:
    tokens = _auth_context()
    try:
        result = v3.tool_delete(
            capability="manage_evidence",
            args={"operation": "create_link"},
        )
        assert result.is_error is True
        with patch(
            "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
            return_value=_fake_prepare(capability="manage_evidence"),
        ):
            result = v3.tool_delete(
                capability="manage_evidence",
                args={
                    "operation": "delete",
                    "scope": "revision",
                    "parent_id": "r1",
                },
            )
            assert result.is_error is False
    finally:
        _cleanup(tokens)


def test_delete_commit_rejects_non_delete_proposal() -> None:
    tokens = _auth_context()
    try:
        proposal = SimpleNamespace(
            capability="cancel_task",
            exact_change={"action": "cancel_task"},
            execution_policy="confirm_before_act",
        )
        with patch(
            "tm_app.interface.mcp.tool_bridge_v3.resolve_proposal_handle",
            return_value="h-1",
        ), patch(
            "tm_app.interface.mcp.tool_bridge_v3.load_valid_proposal",
            return_value=proposal,
        ), patch(
            "tm_app.interface.mcp.tool_bridge_v3._actor",
            return_value=("u1", None),
        ):
            r = v3.tool_delete(proposal_id="gp_1", confirmation=True)
            assert r.is_error is True
            assert "not a destructive-delete" in (
                r.structured_content["message"]
            )
    finally:
        _cleanup(tokens)


# --- unauthenticated -----------------------------------------------------------------


def test_v3_tools_fail_closed_without_identity() -> None:
    reset_proposal_store_for_tests()
    for fn, kwargs in (
        (v3.tool_get_context, {}),
        (v3.tool_read, {"entity": "process", "action": "get"}),
        (v3.tool_execute, {"capability": "create_task", "args": {}}),
        (v3.tool_delete, {"entity": "process", "record_id": "x"}),
    ):
        result = fn(**kwargs)
        assert result.is_error is True
        assert result.structured_content["status_code"] == 401
