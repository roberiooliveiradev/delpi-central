"""INT-1 — B1/B2/B3 provider-request boundary integrity (no LLM egress).

Closes Doc 306 ``PROVIDER_WIRE_PAYLOAD=TO_INVENTORY`` at the supported
Pydantic AI boundary:

```text
B1 owner MCP tools/list
→ B2 RenamedToolset + EnvelopeHint (+ FunctionToolset)
→ B3 FunctionModel AgentInfo.function_tools
```

Does not claim HTTP wire bytes. Does not rewrite Agent/instructions.
"""

from __future__ import annotations

import asyncio

from app.application.interaction.turn_budget import TurnDeadline
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
    _EnvelopeHintedToolset,
)
from fastmcp import Client
from pydantic_ai.models.function import FunctionModel
from tests.support.capability_fixtures import (
    FakeProvider,
    _cap,
    _group,
    _outcome,
)
from tests.support.native_mcp_fixtures import (
    native_toolset_stub,
    owner_tool_server,
)
from tests.support.provider_request_boundary import (
    CAPTURE_MECHANISM,
    HTTP_WIRE_BYTES,
    PYDANTIC_AI_PROVIDER_BOUNDARY,
    boundary_snapshot,
    capture_b3_from_agent_info,
    compare_boundaries,
    fingerprint_from_mcp_tool,
    fingerprint_from_tool_definition,
    request_fingerprint,
)
from tests.test_pydantic_ai_semantic_rework import _final_answer, _gates


G1 = "Mostre a árvore de componentes e relações do item 90260921."
P1 = "Qual é a estrutura do produto 90260921?"
M1 = (
    "Mostre a árvore de componentes e relações que compõem "
    "o produto 90260921."
)

_TEO_READ_DESC = (
    "Semantic read — never writes. entity + typed action + params "
    "object. Domain entities (process, instance, revision, "
    "measurement, investment, shared_resource, resource_cost, "
    "resource_link, meeting_minute, process_document, "
    "decomposition_tree (process WBS/decomposition tree; "
    "id=processo_id — hierarchical process mapeamento macro, "
    "not a materials/product bill-of-materials), "
    "instance_decomposition_scope, "
    "revision_decomposition_overlay, process_diagram): "
    "action=search|get — search lists records; get fetches ONE "
    "record and requires params.id."
)

_DAVI_READ_DESC = (
    "Read DELPI business data through one governed capability. "
    "capability: id published by get_context action=catalog/schema "
    "(e.g. search_products, get_product_structure, get_product_stock). "
    "arguments: object whose keys come from that capability's "
    "argument_schema (for example {\"code\": \"<product-code>\"}) — never "
    "place those business fields as top-level siblings of capability. "
    "Prefer get_context action=schema for the selected capability "
    "before the first read when the argument contract is unclear. "
    "Only currently eligible capabilities execute — unknown or "
    "unavailable ids fail closed. Does not accept URL, path, method, "
    "operationId lookup outside the catalog, or SQL. Backend AuthZ "
    "remains authoritative."
)

_DAVI_GET_CONTEXT_DESC = (
    "DAVI entry point. action=context: specialist identity, actor "
    "context, tool availability, catalog/intelligence/corpus versions, "
    "limits and live agent directives (context is not authorization). "
    "action=catalog: compact list of eligible governed read "
    "capabilities. action=schema: governed argument schema for one "
    "capability via 'capability'. After selecting a capability, call "
    "the live semantic tools read or analyze (or knowledge for "
    "governed documentation). Write-class execute/delete remain "
    "not implemented on this surface."
)

_TEO_GET_CONTEXT_DESC = (
    "TÉO context/catalog entry — process intelligence surface; "
    "decomposition_tree is process WBS (processo_id), not product BOM."
)


def _davi_teo_providers():
    davi = FakeProvider(
        "davi",
        [
            _group(
                "davi",
                "davi",
                [
                    _cap(
                        "davi",
                        "davi",
                        "get_context",
                        schema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string"},
                                "capability": {"type": "string"},
                            },
                        },
                    ),
                    _cap(
                        "davi",
                        "davi",
                        "read",
                        schema={
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "arguments": {"type": "object"},
                            },
                            "required": ["capability"],
                        },
                    ),
                ],
            )
        ],
        outcomes={
            ("davi", "get_context"): _outcome("ctx"),
            ("davi", "read"): _outcome("read"),
        },
    )
    teo = FakeProvider(
        "teo",
        [
            _group(
                "teo",
                "teo",
                [
                    _cap(
                        "teo",
                        "teo",
                        "get_context",
                        schema={
                            "type": "object",
                            "properties": {
                                "section": {"type": "string"},
                            },
                        },
                    ),
                    _cap(
                        "teo",
                        "teo",
                        "read",
                        schema={
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "action": {"type": "string"},
                                "params": {"type": "object"},
                            },
                            "required": ["entity", "action"],
                        },
                    ),
                ],
            )
        ],
        outcomes={
            ("teo", "get_context"): _outcome("teo-ctx"),
            ("teo", "read"): _outcome("teo-read"),
        },
    )
    return [davi, teo]


def _davi_teo_servers():
    return {
        "davi": owner_tool_server(
            "davi",
            {
                "get_context": _DAVI_GET_CONTEXT_DESC,
                "read": _DAVI_READ_DESC,
            },
        ),
        "teo": owner_tool_server(
            "teo",
            {
                "get_context": _TEO_GET_CONTEXT_DESC,
                "read": _TEO_READ_DESC,
            },
        ),
    }


async def _list_owner_tools(servers: dict) -> dict:
    tools = []
    order = 0
    for group_id in sorted(servers):
        async with Client(servers[group_id]) as client:
            listed = await client.list_tools()
            for tool in listed:
                tools.append(
                    fingerprint_from_mcp_tool(
                        tool,
                        order=order,
                        name_prefix=f"{group_id}.",
                    )
                )
                order += 1
    return boundary_snapshot(boundary="owner_mcp_tools_list", tools=tools)


async def _compose_b2_envelope(b1: dict) -> dict:
    import dataclasses as dc

    @dc.dataclass
    class _Def:
        name: str
        description: str
        parameters_json_schema: dict
        kind: str = "function"

    @dc.dataclass
    class _Tool:
        tool_def: _Def

    class _Wrapped:
        def __init__(self, mapping):
            self._mapping = mapping

        async def get_tools(self, ctx):
            return self._mapping

    mapping = {}
    for name, fp in (b1.get("tools_by_name") or {}).items():
        mapping[name] = _Tool(
            _Def(
                name=name,
                description=str(fp.get("description") or ""),
                parameters_json_schema=dict(
                    fp.get("parameters_json_schema") or {}
                ),
            )
        )
    hinted = await _EnvelopeHintedToolset(_Wrapped(mapping)).get_tools(None)
    tools = [
        fingerprint_from_tool_definition(tt.tool_def, order=i)
        for i, (_n, tt) in enumerate(sorted(hinted.items()))
    ]
    by_name = {t["name"]: t for t in tools}
    ordered = []
    for name in b1.get("tool_order") or []:
        if name in by_name:
            fp = dict(by_name[name])
            fp["tool_order"] = len(ordered)
            ordered.append(fp)
    for name, fp in by_name.items():
        if name not in {t["name"] for t in ordered}:
            fp = dict(fp)
            fp["tool_order"] = len(ordered)
            ordered.append(fp)
    return boundary_snapshot(
        boundary="delia_composed_toolset_envelope_hint",
        tools=ordered,
    )


def _capture_b3_for_question(question: str) -> dict:
    captures: list[dict] = []

    def _fn(messages, info):
        if not captures:
            captures.append(capture_b3_from_agent_info(info, messages))
        return _final_answer("done", status="insufficient")

    gates = _gates(providers=_davi_teo_providers())
    with native_toolset_stub(_davi_teo_servers()):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        engine.attempt(question)
    assert captures, "FunctionModel must observe at least one request"
    return captures[0]


def test_abstraction_gate_reuses_function_model_boundary():
    assert "FunctionModel" in CAPTURE_MECHANISM
    assert PYDANTIC_AI_PROVIDER_BOUNDARY == "PROVEN"
    assert HTTP_WIRE_BYTES == "NOT_OBSERVED"


def test_b1_b2_b3_preserve_teo_wbs_and_davi_product_structure_visibility():
    servers = _davi_teo_servers()
    b1 = asyncio.run(_list_owner_tools(servers))
    b2 = asyncio.run(_compose_b2_envelope(b1))
    b3 = _capture_b3_for_question(G1)

    assert b1["tool_count"] == 4
    assert "teo.read" in b1["tools_by_name"]
    assert "davi.read" in b1["tools_by_name"]

    teo_b1 = b1["tools_by_name"]["teo.read"]
    assert teo_b1["description_has_process_wbs"] is True
    assert teo_b1["description_has_bom_negative"] is True
    assert "processo_id" in teo_b1["description"]

    davi_b1 = b1["tools_by_name"]["davi.read"]
    assert davi_b1["description_mentions_get_product_structure"] is True
    assert "davi.get_product_structure" not in b1["tools_by_name"]

    cmp_12 = compare_boundaries(b1, b2, names=["teo.read", "davi.read"])
    for name in ("teo.read", "davi.read"):
        pair = cmp_12["per_tool"][name]
        assert pair["description_prefix_preserved"] is True
        assert pair["description_length_delta"] >= 0

    assert b3["pydantic_ai_provider_boundary"] == "PROVEN"
    assert b3["http_wire_bytes"] == "NOT_OBSERVED"
    assert "teo.read" in b3["tools_by_name"]
    assert "davi.read" in b3["tools_by_name"]
    assert "declare_investigation_goal" in b3["tools_by_name"]

    teo_b3 = b3["tools_by_name"]["teo.read"]
    assert teo_b3["description_has_process_wbs"] is True
    assert teo_b3["description_has_bom_negative"] is True
    assert teo_b3["description"].startswith(teo_b1["description"])
    assert len(teo_b3["description"]) > len(teo_b1["description"])

    davi_b3 = b3["tools_by_name"]["davi.read"]
    assert davi_b3["description_mentions_get_product_structure"] is True
    assert davi_b3["description"].startswith(davi_b1["description"])
    assert len(davi_b3["description"]) > len(davi_b1["description"])


def test_g1_p1_m1_differ_only_in_user_prompt_at_b3():
    g1 = _capture_b3_for_question(G1)
    p1 = _capture_b3_for_question(P1)
    m1 = _capture_b3_for_question(M1)

    assert g1["user_prompt"] == G1
    assert p1["user_prompt"] == P1
    assert m1["user_prompt"] == M1
    assert g1["agent_instructions"] == p1["agent_instructions"] == m1[
        "agent_instructions"
    ]
    assert g1["tool_order"] == p1["tool_order"] == m1["tool_order"]
    assert g1["tool_choice_policy"] == "UNFORCED"

    def _tool_tuple(capture: dict) -> list:
        return [
            (t["name"], t["description_sha256"], t["schema_sha256"])
            for t in capture["tools"]
        ]

    assert _tool_tuple(g1) == _tool_tuple(p1) == _tool_tuple(m1)
    assert len(
        {
            request_fingerprint(g1),
            request_fingerprint(p1),
            request_fingerprint(m1),
        }
    ) == 3
    zeroed = []
    for capture in (g1, p1, m1):
        clone = dict(capture)
        clone["user_prompt"] = ""
        zeroed.append(request_fingerprint(clone))
    assert zeroed[0] == zeroed[1] == zeroed[2]


def test_declare_investigation_goal_visible_semantic_proposal_not_mcp_gate():
    # INT-2: goal declaration remains model-elected (UNFORCED tool
    # choice), model-visible and NOT an authorization/MCP gate — the
    # typed-objective wording replaced the v2-3 "optional" phrasing.
    b3 = _capture_b3_for_question(G1)
    goal = b3["tools_by_name"]["declare_investigation_goal"]
    desc = goal["description"].lower()
    assert "typed" in desc or "declare" in desc
    assert "semantic proposal" in desc
    assert "never grants access" in desc or "not authorization" in desc
    assert "davi.read" in b3["tools_by_name"]
    assert "teo.read" in b3["tools_by_name"]
    assert b3["tool_choice_policy"] == "UNFORCED"


def test_catalog_projection_is_not_b3():
    from scripts.int1_openrouter_qwen14b_instrumented_eval import (
        _catalog_snapshot,
    )

    gates = _gates(providers=_davi_teo_providers())
    live = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    for entry in live:
        if entry.get("capability_id") == "teo.read":
            entry["description"] = _TEO_READ_DESC
        if entry.get("capability_id") == "davi.read":
            entry["description"] = _DAVI_READ_DESC
    snap = _catalog_snapshot(live)
    assert snap["capture_boundary"] == "catalog_projection_pre_envelope_hint"
    assert snap["capture_boundary"] != CAPTURE_MECHANISM
