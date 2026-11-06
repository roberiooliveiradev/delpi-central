"""DAVI-V2-WAVE-001 — semantic tools get_context + knowledge.

Covers: registration + closed schemas, get_context context/catalog/schema
actions (bounded, availability honesty, no permission grant), knowledge
sources/search/get through the governed catalog pipeline (backend AuthZ
boundary, approved projection, provenance), typed errors and unchanged
broker compatibility.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_ANALYZE,
    MCP_TOOL_GET_CONTEXT,
    MCP_TOOL_KNOWLEDGE,
    MCP_TOOL_READ,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.context_service import (
    davi_get_context,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    davi_analyze,
    davi_read,
)
from app.application.external_capabilities.dynamic_information.errors import (
    ARGUMENT_VALIDATION_CODE,
    CAPABILITY_NOT_ALLOWED_CODE,
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.knowledge_service import (
    KNOWLEDGE_ACTION_ID,
    davi_knowledge,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)
from app.interface.mcp.server import create_mcp_server

_API_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()


def _actions():
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(
            encoding="utf-8"
        )
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _seed_actions():
    actions = _actions()
    set_actions_for_tests(actions)
    return actions


class _StubExecutor:
    """Test double for the request-bound CatalogActionExecutorPort."""

    def __init__(
        self,
        *,
        outcome: str = "ok",
        payload: Any = None,
        error_message: str | None = None,
    ) -> None:
        self._result = CatalogActionExecutionResult(
            outcome=outcome, payload=payload, error_message=error_message
        )
        self.calls: list[dict[str, Any]] = []

    def execute(self, *, action_id, validated_arguments):
        self.calls.append(
            {
                "action_id": action_id,
                "validated_arguments": dict(validated_arguments or {}),
            }
        )
        return self._result


_KNOWLEDGE_PAYLOAD = {
    "success": True,
    "data": {
        "knowledge_kind": "GUIDANCE",
        "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
        "trust_level": "UNTRUSTED_DOCUMENT_CONTENT",
        "content_format": "plain_text",
        "topic": "inventory_adjustments",
        "corpus_id": "davi-governed-knowledge",
        "corpus_version": 2,
        "manifest_identity": "manifest-sha",
        "source_path": "api-delpi/docs/api/supplies-inventory-adjustments.md",
        "source_git_sha": "gitsha",
        "source_sha256": "docsha",
        "items": [
            {
                "section": "s0001",
                "heading": "Objetivo",
                "heading_path": "Objetivo",
                "line_start": 1,
                "line_end": 10,
                "chunk": 1,
                "text": "Orientação governada.",
                "sanitized": True,
                "relevance": 0.91,
                "injected_field": "DROP",
            }
        ],
        "page": 1,
        "page_size": 3,
        "total": 1,
        "has_more": False,
        "coverage": "COMPLETE_SELECTION",
        "selection": "subject",
        "subject": "RE0",
        "matched_terms": ["re0"],
        "unmatched_terms": [],
        "unapproved_field": "DROP",
    },
    "meta": {},
}


# ---------------------------------------------------------------------------
# Registration / wire contract
# ---------------------------------------------------------------------------


def test_surface_registers_six_tools_with_closed_schemas():
    tools = asyncio.run(create_mcp_server().list_tools())
    by_name = {t.name: t for t in tools}
    assert list(by_name) == [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
        MCP_TOOL_GET_CONTEXT,
        MCP_TOOL_KNOWLEDGE,
        MCP_TOOL_READ,
        MCP_TOOL_ANALYZE,
    ]
    az = by_name[MCP_TOOL_ANALYZE]
    assert az.input_schema["additionalProperties"] is False
    assert set(az.input_schema["properties"]) == {"capability", "arguments"}
    assert az.output_schema is not None
    assert az.annotations.read_only_hint is True
    ctx = by_name[MCP_TOOL_GET_CONTEXT]
    assert ctx.input_schema["additionalProperties"] is False
    assert set(ctx.input_schema["properties"]) == {"action", "capability"}
    assert ctx.output_schema is not None
    assert ctx.output_schema["additionalProperties"] is False
    kn = by_name[MCP_TOOL_KNOWLEDGE]
    assert kn.input_schema["additionalProperties"] is False
    assert kn.input_schema["required"] == ["action"]
    assert kn.output_schema is not None
    # Owner-typed classes on the wire — metadata, never permission.
    assert ctx.meta["delpi/toolClass"] == "DISCOVERY"
    assert kn.meta["delpi/toolClass"] == "READ"
    assert ctx.annotations.read_only_hint is True
    assert kn.annotations.read_only_hint is True
    assert ctx.securitySchemes == kn.securitySchemes


# ---------------------------------------------------------------------------
# get_context
# ---------------------------------------------------------------------------


def test_get_context_context_reports_identity_actor_and_no_permission_grant():
    _seed_actions()
    data = davi_get_context(action="context", actor_id="u1")
    assert data["status"] == "ok"
    assert data["identity"]["server"] == "api-delpi"
    assert data["actor"] == {"authenticated": True, "id": "u1"}
    assert data["authority"]["catalog_is_not_permission"] is True
    available = [t["name"] for t in data["tools"]["available"]]
    assert available == [
        "get_context",
        "knowledge",
        "read",
        "analyze",
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    unavailable = {t["name"]: t["status"] for t in data["tools"]["unavailable"]}
    assert unavailable == {
        "execute": "PLANNED_NOT_IMPLEMENTED",
        "delete": "PLANNED_NOT_IMPLEMENTED",
    }
    assert data["versions"]["catalog_allowlist"]
    assert data["versions"]["agent_intelligence"]
    assert data["versions"]["knowledge_corpus_latest"] >= 1
    assert data["limits"]["discover_max_top_k"] == 10
    assert "agent_directives" in data["capability_surface"]
    # Actor projection carries presence only — never permissions/scopes.
    assert set(data["actor"]) == {"authenticated", "id"}


def test_get_context_context_unauthenticated_actor_is_honest():
    data = davi_get_context(action="context", actor_id=None)
    assert data["actor"] == {"authenticated": False, "id": None}


def test_get_context_catalog_lists_only_eligible_capabilities():
    actions = _seed_actions()
    data = davi_get_context(action="catalog")
    eligible_ids = {a.action_id for a in actions if a.executable}
    assert data["eligible_action_count"] == len(eligible_ids)
    listed = {a["action_id"] for a in data["actions"]}
    assert listed == eligible_ids
    assert "search_products" in listed
    assert KNOWLEDGE_ACTION_ID in listed
    # Bounded but non-executable capabilities stay out of the catalog.
    assert "execute_readonly_sql" not in listed
    for entry in data["actions"]:
        assert set(entry) == {"action_id", "description", "entity", "shape", "tags"}


def test_get_context_schema_on_demand_for_eligible_capability():
    _seed_actions()
    data = davi_get_context(
        action="schema", capability=KNOWLEDGE_ACTION_ID
    )
    cap = data["capability"]
    assert cap["available"] is True
    assert cap["id"] == KNOWLEDGE_ACTION_ID
    assert cap["argument_schema"]["additionalProperties"] is False
    assert "topic" in cap["required_arguments"]
    assert set(cap["argument_schema"]["properties"]) <= {
        "topic",
        "section",
        "subject",
        "corpus_version",
        "page",
        "page_size",
    }


def test_get_context_schema_reports_unavailable_and_unknown_capabilities():
    _seed_actions()
    bounded = davi_get_context(action="schema", capability="execute_readonly_sql")
    assert bounded["capability"]["available"] is False
    assert bounded["capability"]["davi_status"] == "NEEDS_BOUNDED_EXECUTION"
    unknown = davi_get_context(action="schema", capability="not_a_real_action")
    assert unknown["capability"]["available"] is False
    assert unknown["capability"]["davi_status"] == "UNKNOWN"


def test_get_context_invalid_inputs_fail_closed():
    with pytest.raises(GovernedExecutionError) as missing:
        davi_get_context(action="schema")
    assert missing.value.code == ARGUMENT_VALIDATION_CODE
    with pytest.raises(GovernedExecutionError) as bad_action:
        davi_get_context(action="bogus")
    assert bad_action.value.code == ARGUMENT_VALIDATION_CODE


# ---------------------------------------------------------------------------
# knowledge — governed catalog pipeline
# ---------------------------------------------------------------------------


def test_knowledge_search_executes_governed_catalog_action_with_provenance():
    _seed_actions()
    executor = _StubExecutor(payload=_KNOWLEDGE_PAYLOAD)
    out = davi_knowledge(
        action="search",
        topic="inventory_adjustments",
        subject="RE0",
        catalog_action_executor=executor,
    )
    assert out["status"] == "ok"
    assert out["action_id"] == KNOWLEDGE_ACTION_ID
    call = executor.calls[0]
    assert call["action_id"] == KNOWLEDGE_ACTION_ID
    args = call["validated_arguments"]
    assert args["topic"] == "inventory_adjustments"
    assert args["subject"] == "RE0"
    assert args["page"] == 1
    data = out["knowledge"]["data"]
    assert data["topic"] == "inventory_adjustments"
    assert data["trust_level"] == "UNTRUSTED_DOCUMENT_CONTENT"
    assert data["authority"] == "GUIDANCE_NOT_DOMAIN_TRUTH"
    assert data["corpus_version"] == 2
    assert data["manifest_identity"] == "manifest-sha"
    # Approved projection only — owner-side extras never leak.
    assert "unapproved_field" not in data
    assert "injected_field" not in data["items"][0]


def test_knowledge_get_requires_section_and_binds_it():
    _seed_actions()
    with pytest.raises(GovernedExecutionError) as exc:
        davi_knowledge(
            action="get",
            topic="inventory_adjustments",
            catalog_action_executor=_StubExecutor(),
        )
    assert exc.value.code == ARGUMENT_VALIDATION_CODE
    executor = _StubExecutor(payload=_KNOWLEDGE_PAYLOAD)
    out = davi_knowledge(
        action="get",
        topic="inventory_adjustments",
        section="s0001",
        catalog_action_executor=executor,
    )
    assert out["status"] == "ok"
    assert executor.calls[0]["validated_arguments"]["section"] == "s0001"


def test_knowledge_requires_topic_for_search_and_get():
    _seed_actions()
    for action in ("search", "get"):
        with pytest.raises(GovernedExecutionError) as exc:
            davi_knowledge(
                action=action, catalog_action_executor=_StubExecutor()
            )
        assert exc.value.code == ARGUMENT_VALIDATION_CODE


def test_knowledge_only_sends_approved_arguments_to_owner():
    """The tool builds owner arguments from its own closed parameter set —
    transport/smuggling names can never be injected by the caller."""
    _seed_actions()
    executor = _StubExecutor(payload=_KNOWLEDGE_PAYLOAD)
    out = davi_knowledge(
        action="search",
        topic="inventory_adjustments",
        catalog_action_executor=executor,
    )
    sent = executor.calls[0]["validated_arguments"]
    assert not ({"url", "path", "method", "operationId", "authorization"} & set(sent))
    assert set(sent) <= {"topic", "section", "subject", "corpus_version", "page", "page_size"}
    assert out["status"] == "ok"


def test_knowledge_sources_reports_corpus_index_and_provenance():
    provider = lambda: [
        {
            "id": "inventory_adjustments",
            "title": "Ajustes de inventário",
            "aliases": ["RE0", "DE0"],
            "intent": "CONCEPTUAL_GUIDANCE_ONLY",
            "status": "FROZEN_V1",
        }
    ]
    out = davi_knowledge(action="sources", sources_provider=provider)
    assert out["status"] == "ok"
    assert out["corpus"]["corpus_id"] == "davi-governed-knowledge"
    assert out["corpus"]["available"] is True
    assert out["corpus"]["latest_version"] >= 1
    assert out["topic_count"] == 1
    assert out["topics"][0]["topic"] == "inventory_adjustments"
    assert out["topics"][0]["status"] == "FROZEN_V1"


def test_knowledge_sources_empty_corpus_is_honest_unavailable():
    out = davi_knowledge(action="sources", sources_provider=lambda: [])
    assert out["corpus"]["available"] is False
    assert out["topic_count"] == 0
    assert out["topics"] == []


def test_knowledge_authz_outcomes_propagate_as_permission_errors():
    _seed_actions()
    with pytest.raises(PermissionError) as unauth:
        davi_knowledge(
            action="search",
            topic="inventory_adjustments",
            catalog_action_executor=_StubExecutor(outcome="unauthorized"),
        )
    assert str(unauth.value) == "Unauthorized"
    with pytest.raises(PermissionError) as forb:
        davi_knowledge(
            action="search",
            topic="inventory_adjustments",
            catalog_action_executor=_StubExecutor(outcome="forbidden"),
        )
    assert str(forb.value) == "Forbidden"


def test_knowledge_upstream_error_is_typed_owner_error():
    _seed_actions()
    executor = _StubExecutor(
        outcome="error",
        payload={"error": {"code": "NOT_FOUND"}},
        error_message="Upstream error status=404: code=NOT_FOUND",
    )
    with pytest.raises(GovernedExecutionError) as exc:
        davi_knowledge(
            action="search",
            topic="inventory_adjustments",
            catalog_action_executor=executor,
        )
    assert exc.value.code == "OWNER_EXECUTION_ERROR"


def test_knowledge_unavailable_capability_fails_closed():
    # No knowledge action in the catalog → CAPABILITY_NOT_ALLOWED.
    set_actions_for_tests([])
    with pytest.raises(GovernedExecutionError) as exc:
        davi_knowledge(
            action="search",
            topic="inventory_adjustments",
            catalog_action_executor=_StubExecutor(),
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_CODE


def test_knowledge_unknown_action_fails_closed():
    with pytest.raises(GovernedExecutionError) as exc:
        davi_knowledge(action="bogus", catalog_action_executor=_StubExecutor())
    assert exc.value.code == ARGUMENT_VALIDATION_CODE


# ---------------------------------------------------------------------------
# Wire-level behaviour (call_tool)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_context_wire_context_action():
    result = await create_mcp_server().call_tool("get_context", {})
    assert result.is_error is False
    content = result.structured_content
    assert content["action"] == "context"
    assert content["status"] == "ok"
    assert content["identity"]["server"] == "api-delpi"


@pytest.mark.asyncio
async def test_get_context_wire_rejects_extra_arguments():
    result = await create_mcp_server().call_tool(
        "get_context", {"action": "context", "bogus": 1}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "ARGUMENT_VALIDATION"
    assert "pydantic" not in str(result).lower()


@pytest.mark.asyncio
async def test_knowledge_wire_requires_authentication():
    result = await create_mcp_server().call_tool(
        "knowledge", {"action": "search", "topic": "inventory_adjustments"}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_knowledge_wire_validation_is_typed():
    result = await create_mcp_server().call_tool("knowledge", {"action": "bogus"})
    assert result.is_error is True
    assert result.structured_content["code"] == "ARGUMENT_VALIDATION"
    result = await create_mcp_server().call_tool(
        "knowledge", {"action": "search"}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "ARGUMENT_VALIDATION"


# ---------------------------------------------------------------------------
# Existing broker compatibility (unchanged external contract)
# ---------------------------------------------------------------------------


def test_broker_tools_remain_unchanged_on_the_wire():
    tools = asyncio.run(create_mcp_server().list_tools())
    by_name = {t.name: t for t in tools}
    discover = by_name[MCP_TOOL_DISCOVER_DELPI_INFORMATION]
    assert set(discover.input_schema["properties"]) == {"query", "top_k"}
    assert discover.input_schema["required"] == ["query"]
    execute = by_name[MCP_TOOL_EXECUTE_DELPI_INFORMATION]
    assert set(execute.input_schema["properties"]) == {
        "candidate_token",
        "arguments",
    }
    assert execute.input_schema["required"] == ["candidate_token"]


# ---------------------------------------------------------------------------
# read — semantic façade over the governed catalog (Wave 002 pilot)
# ---------------------------------------------------------------------------


def test_read_executes_eligible_catalog_capability():
    _seed_actions()
    executor = _StubExecutor(
        payload={"success": True, "data": {"items": [{"product_code": "P1"}], "total": 1}}
    )
    out = davi_read(
        capability=KNOWLEDGE_ACTION_ID,
        arguments={"topic": "inventory_adjustments"},
        catalog_action_executor=executor,
    )
    assert out["status"] == "ok"
    assert out["capability"] == KNOWLEDGE_ACTION_ID
    assert executor.calls[0]["action_id"] == KNOWLEDGE_ACTION_ID


def test_read_rejects_unavailable_and_unknown_capabilities():
    _seed_actions()
    for capability in ("execute_readonly_sql", "not_a_real_action"):
        with pytest.raises(GovernedExecutionError) as exc:
            davi_read(capability=capability, catalog_action_executor=_StubExecutor())
        assert exc.value.code == CAPABILITY_NOT_ALLOWED_CODE


def test_read_rejects_missing_and_invalid_arguments():
    _seed_actions()
    with pytest.raises(GovernedExecutionError) as exc:
        davi_read(capability="  ", catalog_action_executor=_StubExecutor())
    assert exc.value.code == ARGUMENT_VALIDATION_CODE
    with pytest.raises(GovernedExecutionError) as exc:
        davi_read(
            capability="search_products",
            arguments={"bogus_arg": 1},
            catalog_action_executor=_StubExecutor(),
        )
    assert exc.value.code == ARGUMENT_VALIDATION_CODE


def test_read_search_products_uses_approved_capability_runner():
    _seed_actions()
    called = {}

    def runner(**kwargs):
        called.update(kwargs)
        return {"items": [{"product_code": "10080010", "description": "D", "group_category": "G", "customer_reference": "X"}]}

    out = davi_read(
        capability="search_products",
        arguments={"code": "10080010"},
        catalog_action_executor=_StubExecutor(),
        search_products_runner=runner,
    )
    assert out["status"] == "ok"
    assert called["enforce_authz"] is True
    assert called["tool_name"] == "read"
    assert "customer_reference" not in str(out["data"])


def test_read_authz_outcomes_propagate():
    _seed_actions()
    with pytest.raises(PermissionError):
        davi_read(
            capability=KNOWLEDGE_ACTION_ID,
            arguments={"topic": "inventory_adjustments"},
            catalog_action_executor=_StubExecutor(outcome="forbidden"),
        )


@pytest.mark.asyncio
async def test_read_wire_requires_authentication():
    result = await create_mcp_server().call_tool(
        "read", {"capability": "search_products", "arguments": {"code": "1"}}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_read_wire_validation_is_typed():
    result = await create_mcp_server().call_tool("read", {"capability": ""})
    assert result.is_error is True
    assert result.structured_content["code"] == "ARGUMENT_VALIDATION"


# ---------------------------------------------------------------------------
# analyze — governed analytic façade over backend-computed reports (Wave 003)
# ---------------------------------------------------------------------------

_REPORT_PAYLOAD = {
    "success": True,
    "data": {
        "period": {"from": "2026-10-01", "to": "2026-10-31"},
        "totals": {"appointments": 42, "produced_qty": 1280.5},
    },
    "meta": {},
}


def test_analyze_executes_analytic_shape_capability():
    _seed_actions()
    executor = _StubExecutor(payload=_REPORT_PAYLOAD)
    out = davi_analyze(
        capability="get_production_appointments_summary",
        arguments={"start_date": "2026-10-01", "end_date": "2026-10-31"},
        catalog_action_executor=executor,
    )
    assert out["status"] == "ok"
    assert out["action"] == "analyze"
    assert out["capability"] == "get_production_appointments_summary"
    assert out["facts"]["shape"] == "playbook_report"
    assert out["provenance"]["calculation_authority"] == "backend"
    assert executor.calls[0]["action_id"] == "get_production_appointments_summary"


def test_analyze_rejects_non_analytic_capabilities():
    _seed_actions()
    # eligible but non-analytic shape (single_product_snapshot)
    with pytest.raises(GovernedExecutionError) as exc:
        davi_analyze(
            capability="get_product_stock",
            catalog_action_executor=_StubExecutor(),
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_CODE
    for capability in ("execute_readonly_sql", "not_a_real_action"):
        with pytest.raises(GovernedExecutionError) as exc:
            davi_analyze(capability=capability, catalog_action_executor=_StubExecutor())
        assert exc.value.code == CAPABILITY_NOT_ALLOWED_CODE


def test_analyze_argument_validation_fail_closed():
    _seed_actions()
    with pytest.raises(GovernedExecutionError) as exc:
        davi_analyze(capability="", catalog_action_executor=_StubExecutor())
    assert exc.value.code == ARGUMENT_VALIDATION_CODE
    with pytest.raises(GovernedExecutionError) as exc:
        davi_analyze(
            capability="get_production_appointments_summary",
            arguments={"bogus_arg": 1},
            catalog_action_executor=_StubExecutor(),
        )
    assert exc.value.code == ARGUMENT_VALIDATION_CODE


def test_analyze_authz_outcomes_propagate():
    _seed_actions()
    for outcome, msg in (("unauthorized", "Unauthorized"), ("forbidden", "Forbidden")):
        with pytest.raises(PermissionError) as exc:
            davi_analyze(
                capability="get_production_appointments_summary",
                arguments={"start_date": "2026-10-01", "end_date": "2026-10-31"},
                catalog_action_executor=_StubExecutor(outcome=outcome),
            )
        assert str(exc.value) == msg


@pytest.mark.asyncio
async def test_analyze_wire_requires_authentication():
    result = await create_mcp_server().call_tool(
        "analyze", {"capability": "get_production_appointments_summary"}
    )
    assert result.is_error is True
    assert result.structured_content["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_analyze_wire_validation_is_typed():
    result = await create_mcp_server().call_tool("analyze", {"capability": ""})
    assert result.is_error is True
    assert result.structured_content["code"] == "ARGUMENT_VALIDATION"

# ---------------------------------------------------------------------------
# Wave 004 — analytic coverage proof over the full eligible catalog
# ---------------------------------------------------------------------------


def test_analyze_gate_admits_all_eligible_analytic_actions():
    """Every executable playbook_report/composite_analysis action is admitted
    by the analyze shape gate — expansion proven, no reimplementation."""
    from app.application.external_capabilities.dynamic_information.execute_service import (
        ANALYZE_ELIGIBLE_SHAPES,
    )

    actions = _seed_actions()
    eligible = [a for a in actions if a.executable]
    analytic = [a for a in eligible if (a.shape or "") in ANALYZE_ELIGIBLE_SHAPES]
    non_analytic = [a for a in eligible if (a.shape or "") not in ANALYZE_ELIGIBLE_SHAPES]
    assert len(analytic) >= 20  # coverage floor — do not shrink silently
    assert len(analytic) < len(eligible)  # gate is selective, not pass-through
    for a in analytic:
        executor = _StubExecutor(payload={"success": True, "data": {}})
        try:
            davi_analyze(capability=a.action_id, arguments={}, catalog_action_executor=executor)
        except GovernedExecutionError as exc:
            assert exc.code == ARGUMENT_VALIDATION_CODE, (
                f"{a.action_id}: analytic eligible action must not fail at the "
                f"shape gate ({exc.code})"
            )
    for a in non_analytic:
        with pytest.raises(GovernedExecutionError) as exc:
            davi_analyze(capability=a.action_id, arguments={}, catalog_action_executor=_StubExecutor())
        assert exc.value.code == CAPABILITY_NOT_ALLOWED_CODE


def test_read_covers_every_eligible_capability_parity():
    """Broker parity: every executable catalog action resolves through read
    (argument errors ok — the capability gate itself must admit them)."""
    actions = _seed_actions()
    eligible = [a for a in actions if a.executable]
    assert len(eligible) >= 90  # parity floor vs broker surface
    for a in eligible:
        try:
            davi_read(capability=a.action_id, arguments={}, catalog_action_executor=_StubExecutor())
        except GovernedExecutionError as exc:
            assert exc.code in (ARGUMENT_VALIDATION_CODE, "OWNER_EXECUTION_ERROR"), (
                f"{a.action_id} rejected at the capability gate: {exc.code}"
            )
        except PermissionError:
            pass


# ---------------------------------------------------------------------------
# Wave 005 — semantic selection substrate parity (NL needs → catalog+schema)
# ---------------------------------------------------------------------------

_NL_NEEDS = {
    "produto por código": "search_products",
    "estoque do produto": "get_product_stock",
    "estrutura do produto": "get_product_structure",
    "apontamentos de produção": "get_production_appointments_summary",
    "faltas de matéria-prima": "get_product_raw_material_set_shortages",
    "detalhe do produto": "get_product_detail",
    "conhecimento técnico documentado": "read_governed_technical_knowledge",
}


def test_semantic_substrate_covers_nl_needs_without_broker():
    """For each real DELPI need, the catalog publishes the capability with
    the same selection metadata discover returns (description, entity,
    shape, tags) and get_context(schema) yields args+required — the model
    gets an equivalent substrate without discover/candidate_token."""
    actions = _seed_actions()
    eligible_ids = {a.action_id for a in actions if a.executable}
    data = davi_get_context(action="catalog")
    catalog = {a["action_id"]: a for a in data["actions"]}
    for need, capability in _NL_NEEDS.items():
        assert capability in eligible_ids, f"{need}: {capability} not eligible"
        entry = catalog[capability]
        assert entry["description"] and entry["entity"] and entry["shape"]
        schema = davi_get_context(action="schema", capability=capability)["capability"]
        assert schema["available"] is True
        assert schema["argument_schema"]["additionalProperties"] is False
        assert "required_arguments" in schema

# ---------------------------------------------------------------------------
# Wave 006 — semantic-only cutover flag (DAVI_LEGACY_BROKER_TOOLS_ENABLED)
# ---------------------------------------------------------------------------


def test_legacy_broker_flag_off_exposes_semantic_only_surface(monkeypatch):
    """Eval/cutover mode: broker hidden from tools/list and rejected on call —
    the four semantic tools keep working against the same governed pipeline."""
    from app.config import settings as _settings

    monkeypatch.setattr(_settings, "DAVI_LEGACY_BROKER_TOOLS_ENABLED", False)
    tools = asyncio.run(create_mcp_server().list_tools())
    names = sorted(t.name for t in tools)
    assert names == ["analyze", "get_context", "knowledge", "read"]

    async def _call():
        res = await create_mcp_server().call_tool(
            "discover_delpi_information", {"query": "produto"}
        )
        return res

    result = asyncio.run(_call())
    assert result.is_error is True
    assert result.structured_content["code"] == "CAPABILITY_NOT_ALLOWED"


def test_legacy_broker_flag_default_keeps_six_tools(monkeypatch):
    from app.config import settings as _settings

    monkeypatch.setattr(_settings, "DAVI_LEGACY_BROKER_TOOLS_ENABLED", True)
    tools = asyncio.run(create_mcp_server().list_tools())
    assert len(tools) == 6
