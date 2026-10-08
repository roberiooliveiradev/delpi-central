"""VISTA Knowledge Orchestration V1 (KIC-V1 PHASE 1).

Structural/eval gate for the ``knowledge_orchestration`` block inside the
canonical intelligence authority (``vista_agent_intelligence.json``). These
are orchestration-routing invariants, not model-quality scores: they prove
the specialist is told which source families exist, which are required per
intent, which gates apply, and when to stop — without duplicating the
directive bodies it routes to.
"""

from __future__ import annotations

import re

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)

_GPT_NAME_RE = re.compile(r"gpt_[a-z_]+")

_REQUIRED_SECTION_KEYS = {
    "principle",
    "sources",
    "precedence",
    "routing",
    "gates",
    "composition_order",
    "sufficiency",
    "gap_handling",
    "epistemology",
    "forbidden",
}

_REQUIRED_SOURCE_FAMILIES = {
    "editor_context",
    "presentation_truth",
    "execution_contract",
    "data_contract",
    "data_runtime",
    "visual_evidence",
    "mutation",
    "product_usage",
    "design_methodology",
    "solution_ecosystem",
    "history",
}

_REQUIRED_INTENTS = {
    "SIMPLE_PRESENTATION_READ",
    "PRODUCT_USAGE",
    "DESIGN_REVIEW",
    "DATA_DISCOVERY",
    "DATA_DIAGNOSIS",
    "PRESENTATION_MUTATION",
    "VISUAL_VERIFICATION",
    "AMBIGUOUS_OBJECT_REFERENCE",
    "DIGITAL_SOLUTION_NEED",
}

_REQUIRED_GATES = {
    "PRESENTATION_TRUTH_GATE",
    "EXECUTION_CONTRACT_GATE",
    "DATA_CONTRACT_GATE",
    "DATA_RUNTIME_GATE",
    "VISUAL_EVIDENCE_GATE",
    "MUTATION_GATE",
    "PRODUCT_USAGE_GATE",
    "SOLUTION_ECOSYSTEM_GATE",
}

_GAP_VOCABULARY = {
    "UNKNOWN",
    "TO_INVENTORY",
    "PARTIAL",
    "UNAVAILABLE_IN_CURRENT_SURFACE",
    "UNSUPPORTED",
}

# Routing matrix: minimal required source families per intent. This is the
# PHASE 1 orchestration-routing eval fixture — it pins WHICH families the
# specialist must consult, not prose snapshots.
_ROUTING_MATRIX = {
    "SIMPLE_PRESENTATION_READ": {
        "required": {"presentation_truth"},
        "avoid": {"design_methodology", "data_contract", "solution_ecosystem", "mutation"},
    },
    "PRODUCT_USAGE": {"required": {"product_usage"}},
    "DESIGN_REVIEW": {"required": {"presentation_truth", "design_methodology"}},
    "DATA_DISCOVERY": {"required": {"data_contract"}},
    "DATA_DIAGNOSIS": {"required": {"presentation_truth", "data_runtime"}},
    "PRESENTATION_MUTATION": {
        "required": {"presentation_truth", "execution_contract", "mutation"},
    },
    "VISUAL_VERIFICATION": {"required": {"presentation_truth", "visual_evidence"}},
    "AMBIGUOUS_OBJECT_REFERENCE": {"required": {"editor_context"}},
    "DIGITAL_SOLUTION_NEED": {"required": {"data_contract"}},
}


def _orchestration(transport: str = "mcp") -> dict:
    directives = VistaAgentIntelligenceService.agent_directives(transport=transport)
    return directives["knowledge_orchestration"]


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()


def test_knowledge_orchestration_projected_on_both_transports():
    mcp = _orchestration("mcp")
    assert mcp["principle"] == "ROUTE_TO_SMALLEST_SUFFICIENT_TRUTH_SET"
    assert _REQUIRED_SECTION_KEYS <= set(mcp.keys())
    # Actions gets the minimal-sufficient compact projection (same semantic
    # source): principle + precedence + required families per intent.
    actions = _orchestration("actions")
    assert actions["principle"] == mcp["principle"]
    assert set(actions["routing"]) == set(mcp["routing"])
    assert actions["precedence"] == mcp["precedence"]


def test_actions_projection_is_smaller_and_semantically_aligned():
    import json

    mcp = _orchestration("mcp")
    actions = _orchestration("actions")
    assert len(json.dumps(actions)) < len(json.dumps(mcp))
    # Same intents, same required families — no semantic drift per intent.
    for intent, route in actions["routing"].items():
        assert route["required"] == mcp["routing"][intent]["required"]


def test_source_families_and_statuses():
    sources = _orchestration()["sources"]
    assert _REQUIRED_SOURCE_FAMILIES <= set(sources.keys())
    # PHASE-gated families keep their honest status — no fake authority.
    assert sources["product_usage"]["status"] == "PARTIAL"
    assert sources["design_methodology"]["status"] == "PARTIAL"
    assert sources["solution_ecosystem"]["status"] == "UNAVAILABLE_IN_CURRENT_SURFACE"
    assert sources["history"]["status"] == "UNAVAILABLE_IN_CURRENT_SURFACE"
    # editor_context must never become an authority source.
    never = " ".join(sources["editor_context"]["never"]).lower()
    assert "authorization" in never


def test_precedence_is_explicit():
    precedence = " ".join(_orchestration()["precedence"])
    assert "LIVE_EXECUTION_CONTRACT > STATIC_INSTRUCTIONS" in precedence
    assert "AUTHORITATIVE_READ_BACK > TECHNICAL_2XX" in precedence
    assert "CANONICAL_STAGE_PIXELS > SCHEMATIC_PIXEL_CLAIMS" in precedence
    assert "SEARCH_MISS IS_NOT PROOF_OF_ABSENCE" in precedence
    assert "EDITOR_CONTEXT = GROUNDING_HINT IS_NOT AUTHORIZATION" in precedence


def test_routing_matrix_required_families():
    routing = _orchestration()["routing"]
    assert _REQUIRED_INTENTS <= set(routing.keys())
    for intent, expectation in _ROUTING_MATRIX.items():
        route = routing[intent]
        required = {str(item).split(" ")[0] for item in route["required"]}
        assert expectation["required"] <= required, intent
        avoid = {str(item).split(" ")[0] for item in route.get("avoid") or []}
        assert expectation.get("avoid", set()) <= avoid, intent


def test_routing_directive_refs_resolve_to_existing_families():
    """Every directive family referenced by routing must exist in the
    intelligence document — prevents orchestration/directive drift."""
    doc = VistaAgentIntelligenceService.document()
    routing = doc["knowledge_orchestration"]["routing"]
    for intent, route in routing.items():
        for ref in route.get("directives") or []:
            assert ref in doc, f"{intent} references unknown directive '{ref}'"


def test_gates_and_sufficiency_are_explicit():
    ko = _orchestration()
    assert _REQUIRED_GATES <= set(ko["gates"].keys())
    mutation_gate = ko["gates"]["MUTATION_GATE"]
    for step in ("READ", "PREPARE", "COMMIT", "VERIFY"):
        assert step in mutation_gate
    sufficiency = " ".join(ko["sufficiency"]).lower()
    assert "parar" in sufficiency or "stop" in sufficiency
    assert "precaução" in sufficiency or "just in case" in sufficiency


def test_gap_handling_and_epistemic_vocabulary():
    ko = _orchestration()
    assert set(ko["gap_handling"]["vocabulary"]) == _GAP_VOCABULARY
    epistemology = set(ko["epistemology"])
    for rule in (
        "GUIDANCE IS_NOT DOMAIN_TRUTH",
        "SUGGESTED IS_NOT SAVED",
        "PREVIEW IS_NOT COMMITTED",
        "COMMITTED IS_NOT VERIFIED",
        "SCHEMATIC IS_NOT PIXEL_INSPECTION",
        "SEARCH_MISS IS_NOT ABSENCE",
        "EDITOR_CONTEXT IS_NOT AUTHZ",
        "CAPABILITY_CATALOG IS_NOT AUTHZ",
        "MODEL_INFERENCE IS_NOT RUNTIME_FACT",
    ):
        assert rule in epistemology


def test_mutation_intent_preserves_governed_sequence():
    route = _orchestration()["routing"]["PRESENTATION_MUTATION"]
    assert route["sequence"] == [
        "READ_CURRENT_STATE",
        "SUGGEST",
        "PREPARE",
        "CONFIRMATION_POLICY",
        "COMMIT",
        "READ_BACK",
        "VERIFY",
    ]


def test_mcp_projection_has_no_actions_only_names():
    """Orchestration follows the same neutralization contract: the MCP
    projection must not leak gpt_* adapter names."""
    import json

    blob = json.dumps(_orchestration("mcp"))
    assert not _GPT_NAME_RE.search(blob), _GPT_NAME_RE.search(blob)


def test_orchestration_does_not_duplicate_directive_bodies():
    """Routing references families; it must not inline their rule bodies.
    Guard: no routing entry may carry a 'rules' list longer than a reference."""
    for intent, route in _orchestration()["routing"].items():
        assert "rules" not in route, f"{intent} duplicates directive rules"
