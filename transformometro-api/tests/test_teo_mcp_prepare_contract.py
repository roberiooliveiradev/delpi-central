"""TÉO MCP PREPARE/ACT contract — PREPARE must never invoke ACT.

Owner contract invariant (ARCH-DRIFT-TEO-MCP-PREPARE-ACT-CONTRACT-01):
under SEMANTIC_V3_ONLY the internal prepare_* bridge functions remain
materially side-effect-free — they seal a proposal and return
``persisted=False``; material execution exists only through the
ACT-class ``execute``/``delete`` tools. ``commit_now``/``idempotency_key``
are a separate GPT-Actions-HTTP additive contract and must never reach
the MCP boundary.
"""

from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.interface.mcp import tool_bridge as bridge
from tm_app.interface.mcp.constants import TOOL_CLASS
from tm_app.interface.mcp.server import create_mcp_server

# Fields that collapse PREPARE into ACT on the GPT Actions HTTP contract.
# Tested structurally (schema + signature + act call count), not by name
# alone — see TestNoActDuringPrepare for the behavior-level assertion.
ACT_COLLAPSE_FIELDS = frozenset({"commit_now", "confirmation", "idempotency_key"})


def _tools():
    return {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}


def _auth(**kwargs):
    user = SimpleNamespace(
        id=kwargs.get("id", "u1"),
        email="teo@example.com",
        name="Téo",
        roles=[],
        groups=[],
        permissions=kwargs.get("permissions", ["transformometro.access"]),
        is_superadmin=False,
    )
    return set_current_user(user), set_request_authorization("Bearer test")


@pytest.fixture(autouse=True)
def _clean_proposals():
    from tm_app.application.governed_writes.proposal_store import (
        reset_proposal_store_for_tests,
    )

    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


class TestPrepareSchemasArePure:
    def test_no_prepare_tools_on_public_surface(self):
        # SEMANTIC_V3_ONLY: PREPARE collapses into the typed ``execute``/
        # ``delete`` contract — no public tool may carry toolClass=PREPARE.
        prepare_tools = [n for n, c in TOOL_CLASS.items() if c == "PREPARE"]
        assert prepare_tools == []

    def test_execute_schema_has_no_act_collapse_fields(self):
        # ``confirmation`` is a legitimate V3 field (commits a pending
        # proposal after the canonical policy gate); the HTTP-additive
        # commit_now/idempotency_key fields must never reach the surface.
        tools = _tools()
        for name in ("execute", "delete"):
            props = set(tools[name].input_schema.get("properties") or {})
            leaked = props & {"commit_now", "idempotency_key"}
            assert not leaked, f"{name} exposes ACT-collapse fields: {leaked}"

    def test_prepare_tool_count_matches_registry(self):
        tools = _tools()
        for name, cls in TOOL_CLASS.items():
            assert name in tools, f"{name} not registered"
            meta = tools[name].meta or {}
            assert meta.get("delpi/toolClass") == cls
        assert tools["execute"].meta["delpi/toolClass"] == "ACT"
        assert tools["delete"].meta["delpi/toolClass"] == "ACT"

    def test_execute_schema_carries_proposal_commit_fields(self):
        # Proposal resumption rides inside ``execute``/``delete``:
        # proposal_handle OR proposal_id identify the sealed proposal;
        # confirmation is never globally required (auto_act needs none).
        for name in ("execute", "delete"):
            schema = _tools()[name].input_schema
            assert "confirmation" not in (schema.get("required") or [])
            props = set(schema.get("properties") or {})
            assert {"proposal_handle", "proposal_id", "confirmation"} <= props

    def test_bridge_prepare_signatures_have_no_act_collapse_params(self):
        fns = {
            name: fn
            for name, fn in vars(bridge).items()
            if name.startswith("tool_prepare_") and callable(fn)
        }
        fns["_prepare"] = bridge._prepare
        for name, fn in fns.items():
            params = set(inspect.signature(fn).parameters)
            leaked = params & ACT_COLLAPSE_FIELDS
            assert not leaked, f"{name} accepts ACT-collapse params: {leaked}"


class TestNoActDuringPrepare:
    """PREPARE call → orchestrator.prepare runs, orchestrator.act never."""

    def _prepare_env(self):
        act = patch.object(
            bridge._orchestrator, "act", side_effect=AssertionError(
                "orchestrator.act() invoked during MCP PREPARE"
            )
        )
        return act

    def test_prepare_capability_path_never_acts(self):
        user_token, auth_token = _auth()
        try:
            with self._prepare_env() as act_mock, patch.object(
                bridge._orchestrator,
                "prepare",
                return_value={
                    "proposal_handle": "h",
                    "ready": True,
                    "act_allowed": True,
                    "capability": "adjust_shared_resource_cost",
                },
            ) as prep:
                result = bridge.tool_prepare_adjust_shared_resource_cost(
                    recurso_compartilhado_id="r1",
                    valor_mensal=10.0,
                    vigente_desde="2026-01-01",
                )
            assert result.is_error is False
            prep.assert_called_once()
            act_mock.assert_not_called()
            data = result.structured_content["data"]
            assert data["status"] == "proposal_ready"
            assert data["persisted"] is False
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_prepare_record_change_never_acts(self):
        user_token, auth_token = _auth()
        try:
            with self._prepare_env() as act_mock, patch.object(
                bridge._governed,
                "prepare_record_change",
                return_value={
                    "status": "proposal_ready",
                    "persisted": False,
                    "proposal": {"handle": "opaque.handle", "act_allowed": True},
                },
            ) as prep:
                result = bridge.tool_prepare_record_change(
                    entity="process_document",
                    operation="create",
                    changes={"titulo": "Doc"},
                )
            assert result.is_error is False
            prep.assert_called_once()
            assert "commit_now" not in prep.call_args.kwargs
            act_mock.assert_not_called()
            data = result.structured_content["data"]
            assert data["persisted"] is False
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_prepare_improvement_package_never_acts(self):
        user_token, auth_token = _auth()
        try:
            with self._prepare_env() as act_mock, patch.object(
                bridge._orchestrator,
                "prepare",
                return_value={
                    "proposal_handle": "h",
                    "ready": False,
                    "act_allowed": False,
                    "validation_result": {"ready": False, "missing": ["x"]},
                },
            ):
                result = bridge.tool_prepare_improvement_package(
                    process={"nome": "X"},
                    activate_scenario=True,
                    recalculate=True,
                )
            assert result.is_error is False
            act_mock.assert_not_called()
            assert result.structured_content["data"]["persisted"] is False
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)


class TestOldFieldsRejected:
    def test_commit_now_kwarg_rejected_by_bridge(self):
        with pytest.raises(TypeError):
            bridge.tool_prepare_record_change(
                entity="process_document",
                operation="create",
                changes={},
                commit_now=True,
            )

    def test_confirmation_and_idempotency_kwargs_rejected(self):
        for kwargs in (
            {"confirmation": True},
            {"idempotency_key": "k1"},
        ):
            with pytest.raises(TypeError):
                bridge.tool_prepare_improvement_package(
                    process={}, **kwargs
                )
            with pytest.raises(TypeError):
                bridge.tool_prepare_adjust_shared_resource_cost(
                    recurso_compartilhado_id="r1",
                    valor_mensal=1.0,
                    vigente_desde="2026-01-01",
                    **kwargs,
                )


class TestCommitProposalRemainsAct:
    def test_act_exactly_once_after_confirmation(self):
        user_token, auth_token = _auth()
        try:
            with patch.object(
                bridge._governed,
                "commit_proposal",
                return_value={
                    "status": "ok",
                    "postcondition": {"verified": True},
                    "data": {},
                },
            ) as commit:
                result = bridge.tool_commit_proposal(
                    "handle", confirmation=True
                )
            assert result.is_error is False
            commit.assert_called_once()
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)
