"""TÉO Knowledge Orchestration V1 — live directive contract tests.

Proves the agent's living knowledge architecture: explicit source map,
intent → smallest-sufficient-source routing, mandatory gates, precedence
and sufficiency rules — with ZERO new tools added.
"""

from __future__ import annotations

from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
    clear_teo_agent_intelligence_cache,
)


def setup_function() -> None:
    clear_teo_agent_intelligence_cache()


def teardown_function() -> None:
    clear_teo_agent_intelligence_cache()


def _ko():
    ko = TeoAgentIntelligenceService.document().get("knowledge_orchestration")
    assert isinstance(ko, dict), "knowledge_orchestration block missing"
    return ko


def test_orchestration_is_projected_to_agent_directives():
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )

    directives = build_capability_surface_catalog()["agent_directives"]
    ko = directives.get("knowledge_orchestration")
    assert isinstance(ko, dict) and ko.get("sources") and ko.get("routing")


def test_zero_new_tools_source_map_uses_existing_surface():
    from tm_app.interface.mcp.constants import MCP_TOOL_NAMES

    known = set(MCP_TOOL_NAMES)
    seen: set[str] = set()
    for name, source in _ko()["sources"].items():
        assert source.get("authority"), name
        tools = source.get("tools") or []
        assert tools, name
        seen.update(tools)
    unknown = seen - known
    assert not unknown, f"orchestration references non-existent tools: {unknown}"


def test_source_map_covers_all_knowledge_families():
    sources = _ko()["sources"]
    for family in (
        "workspace_context",
        "process_truth",
        "domain_records",
        "product_usage",
        "methodology",
        "solution_ecosystem",
        "evidence",
        "timeline",
        "diagnostic",
        "analysis",
        "execution_contract",
        "mutation",
        "act",
    ):
        assert family in sources, family
    # Boundary invariants.
    assert sources["act"]["tools"] == ["commit_proposal"]
    assert sources["workspace_context"]["authority"] == "navigation_hint_only"


def test_routing_matrix_intents():
    routing = _ko()["routing"]
    for intent in (
        "SIMPLE_DOMAIN_READ",
        "PRODUCT_USAGE",
        "PROCESS_DIAGNOSIS",
        "PROCESS_IMPROVEMENT",
        "DIGITAL_SOLUTION_NEED",
        "SOLUTION_DISCOVERY",
        "TRANSFORMOMETRO_WRITE",
        "METHODOLOGY_REQUEST",
    ):
        assert intent in routing, intent


def test_scenario_1_dashboard_need_routes_to_ecosystem_first():
    """Dashboard proposal → process truth → ecosystem → fit. Never NEW first."""
    digital = _ko()["routing"]["DIGITAL_SOLUTION_NEED"]
    pipeline = digital["pipeline"]
    assert "solution_read(action=catalog)" in pipeline
    assert "solution_read(action=context) nos candidatos" in pipeline
    assert pipeline.index("classify fit") > pipeline.index(
        "solution_read(action=catalog)"
    )
    rule = digital["rule"]
    assert "NEW_CAPABILITY_CANDIDATE" in rule
    for fit in (
        "REUSE_EXISTING",
        "EXTEND_EXISTING",
        "INTEGRATE_EXISTING",
        "NEW_CAPABILITY_CANDIDATE",
        "TO_INVENTORY",
    ):
        assert fit in digital["fit"]


def test_scenario_2_product_usage_no_ecosystem():
    """'Como cadastro corretamente o baseline?' → product guide, no solutions."""
    product = _ko()["routing"]["PRODUCT_USAGE"]
    assert product["route"][0] == "get_product_guide"
    assert "solution_read" not in str(product["route"])
    assert product["gate"] == "PRODUCT_USAGE_GATE"


def test_scenario_3_diagnosis_hypothesis_not_fact():
    diag = _ko()["routing"]["PROCESS_DIAGNOSIS"]
    assert "get_process_context" in diag["route"][0]
    assert "hipótese" in diag["rule"]


def test_scenario_4_solution_discovery():
    disc = _ko()["routing"]["SOLUTION_DISCOVERY"]
    assert disc["route"][0] == "solution_read(action=catalog)"


def test_scenario_5_write_no_methodology_no_solutions():
    write = _ko()["routing"]["TRANSFORMOMETRO_WRITE"]
    assert "PREPARE" in write["route"]
    assert "ACT" in write["route"]
    assert "authoritative read-back" in write["route"]
    assert "methodology" in write["avoid"]
    assert "solution_ecosystem" in write["avoid"]


def test_scenario_6_product_question_no_process_context():
    """'Para que serve a sala de interação?' → product guide only."""
    product = _ko()["routing"]["PRODUCT_USAGE"]
    assert "get_process_context" not in str(product["route"])


def test_mandatory_gates_defined():
    gates = _ko()["gates"]
    for gate in (
        "PROCESS_TRUTH_GATE",
        "PRODUCT_USAGE_GATE",
        "DIGITAL_SOLUTION_GATE",
        "EXECUTION_CONTRACT_GATE",
        "METHODOLOGY_GATE",
    ):
        assert gate in gates, gate
    # Methodology is never mandatory for simple reads.
    assert "NUNCA" in gates["METHODOLOGY_GATE"]


def test_precedence_ordering():
    precedence = "\n".join(_ko()["precedence"])
    assert "CURRENT DOMAIN STATE > PRODUCT GUIDANCE" in precedence
    assert "LIVE CATALOG / EXECUTION POLICY > STATIC INSTRUCTIONS" in precedence
    assert "CORE SOLUTION INTELLIGENCE" in precedence
    assert "EVIDENCE > HYPOTHESIS" in precedence
    assert "AUTHORITATIVE READ-BACK > TECHNICAL 2XX" in precedence
    assert "Search miss != proof of absence" in precedence


def test_sufficiency_and_gap_rules():
    ko = _ko()
    suff = " ".join(ko["sufficiency"])
    assert "suficiente" in suff
    assert "tool spam" in suff
    gap = ko["gap_handling"]
    assert "NÃO inventar" in gap["rule"]
    for label in ("UNKNOWN", "TO_INVENTORY", "PROPOSED", "INFERRED"):
        assert label in gap["labels"]
