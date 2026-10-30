"""CLARA-MCP-SEMANTIC-001 (doc 119) — superfície semântica (não-PG).

Cobre:
- registry (entity, action) → handler: ações válidas despacham nos
  mesmos handlers legados (paridade), ações inválidas falham tipado
  (`not_implemented`/`validation_error`) — nunca dispatch dinâmico.
- get_context: topics summary/catalog/schema/persona — schema por
  action sob demanda, catálogo versionado.
- execute/delete: PREPARE → commit via handle; `direct`/`immediate`
  rejeitados pela política vigente; delete restrito a capabilities
  `destructive`; batch delega ao orchestrator.
- AuthZ fail-closed: identidade indisponível → erro tipado.
- Fuzz: entity/action malformados, injection-like, payloads
  gigantes, campos arbitrários — sem exceção não capturada.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from unittest.mock import MagicMock

from mcp.types import CallToolResult

from controllership_finance_app.interface.mcp import semantic_bridge as sb
from controllership_finance_app.interface.mcp import tool_bridge
from controllership_finance_app.interface.mcp.server import (
    clara_mcp_server,
)


def _payload(result: CallToolResult) -> dict:
    return result.structured_content or json.loads(
        result.content[0].text
    )


@pytest.fixture()
def actor(monkeypatch):
    """Identidade autenticada mínima para os handlers semânticos."""
    user = MagicMock()
    user.id = "3f8f3e9b-8d8c-4b3a-9a77-0f6a2a4b9c11"
    user.name = "Usuária Teste"
    user.email = "user@delpi.com.br"
    user.is_superadmin = False
    monkeypatch.setattr(
        sb, "_user_and_access",
        lambda: (MagicMock(), user),
    )
    monkeypatch.setattr(
        tool_bridge, "_user_and_access",
        lambda: (MagicMock(), user),
    )
    monkeypatch.setattr(sb, "actor_subject", lambda _u: "sub-1")
    return user


# ------------------------------------------------------------------
# Superfície — seis tools, schemas explícitos
# ------------------------------------------------------------------


def test_wire_surface_is_exactly_six_tools():
    tools = asyncio.new_event_loop().run_until_complete(
        clara_mcp_server.list_tools()
    )
    assert {t.name for t in tools} == {
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    }
    assert len(tools) == 6


def test_schemas_are_explicit_and_constructible():
    tools = {t.name: t for t in asyncio.new_event_loop()
             .run_until_complete(clara_mcp_server.list_tools())}
    for name in ("read", "analyze", "knowledge", "execute", "delete"):
        schema = tools[name].input_schema
        assert schema["type"] == "object"
        assert schema["properties"], name
    read_schema = tools["read"].input_schema
    assert "entity" in read_schema["required"]
    assert "action" in read_schema["required"]
    assert "filters" in read_schema["properties"]


# ------------------------------------------------------------------
# get_context
# ------------------------------------------------------------------


def test_get_context_summary(actor):
    res = sb.tool_get_context()
    assert res.is_error is False
    data = _payload(res)["data"]
    assert data["catalog_version"] == sb.SEMANTIC_CATALOG_VERSION
    assert data["action_counts"]["read"] == len(sb.READ_ACTIONS)
    assert data["actor"] is not None


def test_get_context_catalog_lists_all_actions(actor):
    res = sb.tool_get_context(topic="catalog")
    data = _payload(res)["data"]
    catalog = data["catalog"]
    read_pairs = {(e["entity"], e["action"])
                  for e in catalog["actions"]["read"]}
    assert ("pendency", "list") in read_pairs
    assert ("report", "stock_inventory") in read_pairs
    assert ("received", "document") in read_pairs
    governed = {g["capability"] for g in catalog["actions"]["governed"]}
    assert "document.cancel" in governed
    destructive = {g["capability"] for g in catalog["actions"]["governed"]
                   if g["destructive"]}
    assert "document.cancel" in destructive


def test_get_context_schema_on_demand(actor):
    res = sb.tool_get_context(
        topic="schema", entity="pendency", action="list"
    )
    data = _payload(res)["data"]
    assert data["tool"] == "read"
    assert "period" in data["required_params"]
    # Governed action schema
    res2 = sb.tool_get_context(
        topic="schema", entity="document", action="cancel"
    )
    data2 = _payload(res2)["data"]
    assert data2["tool"] == "delete"
    assert data2["destructive"] is True
    assert "prepare" in data2["phase_policy"]


def test_get_context_schema_unknown_action(actor):
    res = sb.tool_get_context(
        topic="schema", entity="foo", action="bar"
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "not_implemented"


def test_get_context_schema_requires_entity_and_action(actor):
    res = sb.tool_get_context(topic="schema")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_get_context_unknown_topic(actor):
    res = sb.tool_get_context(topic="bogus")
    assert res.is_error is True


# ------------------------------------------------------------------
# read — dispatch no registry
# ------------------------------------------------------------------


def test_read_dispatches_to_same_handler(monkeypatch, actor):
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return tool_bridge._ok({"items": []})

    monkeypatch.setitem(
        sb.READ_ACTIONS, ("pendency", "list"),
        {"handler": fake, "ref_param": None,
         "required": ("period",), "allowed": ("state",)},
    )
    res = sb.tool_read(
        entity="pendency", action="list", period="2026-09",
        filters={"state": "OPEN"},
    )
    assert res.is_error is False
    assert seen == {"state": "OPEN", "period": "2026-09"}
    data = _payload(res)
    assert data["entity"] == "pendency"
    assert data["action"] == "list"


def test_read_ref_maps_to_action_param(monkeypatch, actor):
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return tool_bridge._ok({})

    monkeypatch.setitem(
        sb.READ_ACTIONS, ("document", "get"),
        {"handler": fake, "ref_param": "document_id",
         "required": ("period", "document_id"),
         "allowed": ()},
    )
    res = sb.tool_read(
        entity="document", action="get",
        ref="doc-42", period="2026-09",
    )
    assert res.is_error is False
    assert seen["document_id"] == "doc-42"


def test_read_unknown_entity_action_fails_closed(actor):
    res = sb.tool_read(entity="shell", action="exec")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "not_implemented"


def test_read_missing_required_param(actor):
    res = sb.tool_read(entity="competence", action="get")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_read_rejects_unknown_filter(actor):
    res = sb.tool_read(
        entity="pendency", action="list", period="2026-09",
        filters={"drop_table": "x"},
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_read_page_size_capped(actor):
    res = sb.tool_read(
        entity="report", action="settlements",
        filters={"side": "PAYABLE", "start_date": "2026-09-01",
                 "end_date": "2026-09-30"},
        page_size=10_000,
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_read_fuzz_entity_action(actor):
    for entity, action in (
        ("", ""),
        (None, None),
        ("pendency'; DROP TABLE--", "list"),
        ("<script>", "get"),
        ("x" * 4096, "list"),
    ):
        res = sb.tool_read(entity=entity, action=action)
        assert res.is_error is True
        assert _payload(res)["data"]["error_code"] in (
            "not_implemented", "validation_error"
        )


# ------------------------------------------------------------------
# analyze / knowledge
# ------------------------------------------------------------------


def test_analyze_dispatches(monkeypatch, actor):
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return tool_bridge._ok({"findings": []})

    monkeypatch.setitem(
        sb.ANALYZE_ACTIONS, "closing_blockers",
        {"handler": fake, "required": ("period",),
         "allowed": (), "description": "x"},
    )
    res = sb.tool_analyze("closing_blockers", period="2026-09")
    assert res.is_error is False
    assert seen["period"] == "2026-09"


def test_analyze_unknown_type(actor):
    res = sb.tool_analyze("sentiment_analysis")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "not_implemented"


def test_knowledge_actions_dispatch(monkeypatch, actor):
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return tool_bridge._ok({"items": []})

    monkeypatch.setitem(
        sb.KNOWLEDGE_ACTIONS, "search",
        {"handler": fake, "required": ("query",),
         "allowed": ("topic", "report_id", "business_step", "limit")},
    )
    res = sb.tool_knowledge(
        "search", query="competência", limit=5
    )
    assert res.is_error is False
    assert seen["query"] == "competência"
    assert seen["limit"] == 5


def test_knowledge_requires_query_for_search(actor):
    res = sb.tool_knowledge("search")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_knowledge_unknown_action(actor):
    res = sb.tool_knowledge("delete_everything")
    assert res.is_error is True


# ------------------------------------------------------------------
# execute / delete — fluxo governado
# ------------------------------------------------------------------


@pytest.fixture()
def governed(monkeypatch, actor):
    gw = MagicMock()
    gw._capability_table.return_value = {
        "pendency.create": {
            "resource_type": "pendency",
            "required_params": ("period", "kind", "title"),
            "gate": "access",
            "destructive": False,
        },
        "document.cancel": {
            "resource_type": "document",
            "required_params": ("period", "document_id", "reason"),
            "gate": "manage",
            "destructive": True,
        },
    }
    gw.capabilities.return_value = []
    gw.prepare.return_value = {
        "proposal_handle": "h1",
        "confirmation_url": "https://portal/consent/1",
        "operation": {},
    }
    gw.commit.return_value = {"outcome": "VERIFIED"}
    gw._identity.return_value = {"is_manage": True, "is_dre": False}
    monkeypatch.setattr(sb, "_governed_writes", lambda: gw)
    return gw


def test_execute_prepare_delegates(governed):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params={"period": "2026-09", "kind": "K", "title": "T"},
    )
    assert res.is_error is False
    governed.prepare.assert_called_once_with(
        capability="pendency.create",
        params={"period": "2026-09", "kind": "K", "title": "T"},
        actor_sub="sub-1",
    )
    data = _payload(res)["data"]
    assert data["proposal_handle"] == "h1"


def test_execute_commit_uses_exact_handle(governed):
    res = sb.tool_execute(
        phase="commit", proposal_handle="h1"
    )
    assert res.is_error is False
    governed.commit.assert_called_once_with(
        handle="h1", actor_sub="sub-1"
    )


def test_execute_direct_phase_rejected_by_policy(governed):
    for phase in ("direct", "immediate"):
        res = sb.tool_execute(
            entity="pendency", action="create",
            params={"period": "2026-09", "kind": "K", "title": "T"},
            phase=phase,
        )
        assert res.is_error is True
        assert _payload(res)["data"]["error_code"] == (
            "consent_required"
        )
    governed.prepare.assert_not_called()


def test_execute_commit_requires_handle(governed):
    res = sb.tool_execute(phase="commit")
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "validation_error"


def test_execute_unknown_operation_fails_closed(governed):
    res = sb.tool_execute(
        entity="database", action="truncate",
        params={},
    )
    assert res.is_error is True
    assert _payload(res)["data"]["error_code"] == "not_implemented"


def test_execute_missing_required_params(governed):
    res = sb.tool_execute(
        entity="pendency", action="create",
        params={"period": "2026-09"},
    )
    assert res.is_error is True
    governed.prepare.assert_not_called()


def test_delete_only_destructive_capabilities(governed):
    res = sb.tool_delete(
        entity="pendency", action="create",
        params={"period": "2026-09", "kind": "K", "title": "T"},
    )
    assert res.is_error is True
    governed.prepare.assert_not_called()


def test_delete_target_ref_maps_to_key_param(governed):
    res = sb.tool_delete(
        entity="document", action="cancel",
        target_ref="doc-9",
        params={"period": "2026-09", "reason": "dup"},
    )
    assert res.is_error is False
    args = governed.prepare.call_args.kwargs
    assert args["capability"] == "document.cancel"
    assert args["params"]["document_id"] == "doc-9"
    assert args["params"]["reason"] == "dup"


def test_delete_commit_same_governed_path(governed):
    res = sb.tool_delete(
        phase="commit", proposal_handle="h1"
    )
    assert res.is_error is False
    governed.commit.assert_called_once_with(
        handle="h1", actor_sub="sub-1"
    )


def test_execute_batch_delegates(monkeypatch, actor, governed):
    orch = MagicMock()
    orch.prepare_batch.return_value = {"batch_id": "b1"}
    monkeypatch.setattr(sb, "_batch_orchestrator", lambda: orch)
    res = sb.tool_execute(
        batch={
            "phase": "prepare",
            "operations": [
                {"entity": "pendency", "action": "create",
                 "params": {"period": "2026-09", "kind": "K",
                            "title": "T"}},
                {"capability": "document.post_message",
                 "params": {"period": "2026-09", "document_id": "d",
                            "body": "x"},
                 "depends_on": "0"},
            ],
        }
    )
    assert res.is_error is False
    ops = orch.prepare_batch.call_args.kwargs["operations"]
    assert ops[0]["capability"] == "pendency.create"
    assert ops[1]["capability"] == "document.post_message"
    assert ops[1]["depends_on"] == "0"


def test_execute_batch_confirm_and_execute(monkeypatch, actor, governed):
    orch = MagicMock()
    orch.confirm_batch.return_value = {"state": "CONFIRMED"}
    orch.execute_batch.return_value = {"state": "DONE"}
    monkeypatch.setattr(sb, "_batch_orchestrator", lambda: orch)
    res = sb.tool_execute(
        batch={"phase": "confirm", "batch_handle": "b1",
               "plan_hash": "ph"}
    )
    assert res.is_error is False
    orch.confirm_batch.assert_called_once_with(
        handle="b1", actor_sub="sub-1", plan_hash="ph"
    )
    res = sb.tool_execute(
        batch={"phase": "execute", "batch_handle": "b1"}
    )
    assert res.is_error is False


def test_execute_batch_phases_require_handle(monkeypatch, actor, governed):
    orch = MagicMock()
    monkeypatch.setattr(sb, "_batch_orchestrator", lambda: orch)
    res = sb.tool_execute(batch={"phase": "confirm"})
    assert res.is_error is True


# ------------------------------------------------------------------
# AuthZ fail-closed
# ------------------------------------------------------------------


def test_unauthenticated_maps_to_401(monkeypatch):
    def _deny():
        raise PermissionError("Unauthorized")

    monkeypatch.setattr(sb, "_user_and_access", _deny)
    monkeypatch.setattr(tool_bridge, "_user_and_access", _deny)
    for call in (
        # get_context/execute: gate semântico (sb._user_and_access)
        lambda: sb.tool_get_context(),
        lambda: sb.tool_execute(entity="pendency", action="create"),
        # read: a AuthZ acontece dentro do handler legado, que usa
        # tool_bridge._user_and_access — mesmo gate da rota Portal.
        lambda: sb.tool_read(entity="pendency", action="list",
                             period="2026-09"),
    ):
        try:
            call()
            raise AssertionError("esperava PermissionError")
        except PermissionError:
            pass


def test_no_model_supplied_handler(actor):
    """Entity/action nunca podem injetar handler, path ou método."""
    res = sb.tool_read(
        entity="tool_bridge.tool_get_document",
        action="__call__",
    )
    assert res.is_error is True
    res2 = sb.tool_execute(
        entity="https://evil.internal", action="GET",
        params={},
    )
    assert res2.is_error is True
