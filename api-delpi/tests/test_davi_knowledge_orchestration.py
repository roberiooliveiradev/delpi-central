"""DAVI Knowledge Orchestration V1: source governance, routes and retrieval regressions."""

from __future__ import annotations

from unittest.mock import patch

from app.application.external_capabilities.catalog_service import build_gpt_catalog
from app.application.external_capabilities.davi_agent_intelligence_service import (
    DAVI_AGENT_DIRECTIVES_MAX_BYTES,
    DaviAgentIntelligenceService,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)

_REQUIRED_KEYS = {
    "principle", "scope", "sources", "precedence", "routing", "gates",
    "composition_order", "sufficiency", "gap_handling", "epistemology", "forbidden",
}
_INTENTS = {
    "PURE_CONCEPT", "SIMPLE_DOMAIN_READ", "CONCEPT_AND_CURRENT_DATA",
    "STRUCTURE_WHERE_USED", "INVENTORY_ADJUSTMENT", "MULTI_SOURCE_RECONCILIATION",
    "SYSTEM_METADATA", "SOLUTION_DISCOVERY", "WRITE_OR_GENERIC_SQL",
}
_MCP_TOOLS = {"discover_delpi_information", "execute_delpi_information"}


def _ko() -> dict:
    return DaviAgentIntelligenceService.agent_directives()["knowledge_orchestration"]


def test_orchestration_projection_contract_and_budget() -> None:
    ko = _ko()
    assert _REQUIRED_KEYS <= set(ko)
    assert ko["principle"] == "ROUTE_TO_SMALLEST_SUFFICIENT_TRUTH_SET"
    assert ko["scope"] == "READ_ONLY_AGENT_ROUTING_NOT_AUTHORIZATION"
    assert set(ko["routing"]) == _INTENTS
    assert DaviAgentIntelligenceService.directives_serialized_size() <= DAVI_AGENT_DIRECTIVES_MAX_BYTES
    assert DaviAgentIntelligenceService.agent_directives()["read_only"] is True


def test_source_authority_and_provider_evidence_are_separate() -> None:
    sources = _ko()["sources"]
    assert sources["domain_runtime"]["authority"].startswith("AUTHORITATIVE_ONLY_AFTER_BACKEND_AUTHZ")
    assert sources["governed_knowledge"]["status"] == "PROVEN"  # corpus Git only
    assert sources["governed_knowledge"]["provider_status"] == "TEST_NOT_RUN"
    assert sources["solution_ecosystem"]["status"] == "TO_INVENTORY"
    assert sources["solution_ecosystem"]["access"] == "NOT_CONNECTED_TO_DAVI"
    assert sources["conversation_context"]["authority"].startswith("GROUNDING_HINT_ONLY")
    for source in sources.values():
        assert source["owner"] and source["authority"] and source["status"]
        assert set(source.get("tools", [])) <= _MCP_TOOLS


def test_knowledge_availability_is_explicit_for_external_mcp_consumers() -> None:
    source = _ko()["sources"]["governed_knowledge"]
    assert source["corpus_status"] == "PROVEN"
    assert source["retrieval_surface"] == "WORKSPACE_AGENT_FILES"
    assert source["mcp_document_access"] == "EXPOSED_VIA_CATALOG_ACTION_READ"
    assert source["mcp_read_operation_id"] == "read_governed_technical_knowledge"
    assert source["consumer_contract_status"] == "RATIFIED_BOUNDED"
    assert source["published_corpus_versions"] == [1, 2]
    assert source["latest_corpus_version"] == 2
    assert source["tools"] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    gate = _ko()["gates"]["KNOWLEDGE_GATE"]
    assert "MCP" in gate and "agent_directives" in gate
    assert "AuthZ" in gate


def test_routing_references_only_registered_sources_and_directives() -> None:
    ko = _ko()
    directives = DaviAgentIntelligenceService.agent_directives()
    for intent, route in ko["routing"].items():
        assert set(route["required"]) <= set(ko["sources"]), intent
        assert set(route.get("optional", [])) <= set(ko["sources"]), intent
        assert set(route.get("avoid", [])) <= set(ko["sources"]), intent
        assert set(route["gates"]) <= set(ko["gates"]), intent
        assert set(route["directives"]) <= set(directives), intent
        assert not (set(route["required"]) & set(route.get("avoid", []))), intent
        assert "rules" not in route


def test_pure_concept_does_not_route_through_lexical_action_overlap() -> None:
    route = _ko()["routing"]["PURE_CONCEPT"]
    assert route["required"] == ["governed_knowledge"]
    assert "domain_runtime" in route["avoid"]
    assert "não descobrir uma action" in route["rule"]
    assert "KNOWLEDGE_GATE" in route["gates"]


def test_mixed_intent_and_simple_read_use_minimum_sources() -> None:
    routes = _ko()["routing"]
    assert {"governed_knowledge", "live_capability_catalog", "domain_runtime"} <= set(
        routes["CONCEPT_AND_CURRENT_DATA"]["required"]
    )
    assert routes["SIMPLE_DOMAIN_READ"]["required"] == [
        "live_capability_catalog", "domain_runtime"
    ]
    assert "governed_knowledge" in routes["SIMPLE_DOMAIN_READ"]["avoid"]


def test_solution_and_write_gates_are_fail_closed() -> None:
    ko = _ko()
    assert ko["routing"]["SOLUTION_DISCOVERY"]["required"] == ["solution_ecosystem"]
    assert ko["sources"]["solution_ecosystem"]["tools"] == []
    assert "TO_INVENTORY" in ko["gates"]["SOLUTION_GATE"]
    assert ko["routing"]["WRITE_OR_GENERIC_SQL"]["required"] == []
    assert "Generic SQL / arbitrary HTTP proxy" in ko["forbidden"]


def test_precedence_sufficiency_epistemology_and_partial_pages() -> None:
    ko = _ko()
    assert "SEARCH_MISS IS_NOT PROOF_OF_ABSENCE" in ko["precedence"]
    assert "DOCUMENT_GUIDANCE IS_NOT BUSINESS_AUTHZ" in ko["precedence"]
    assert {"OBSERVED", "CALCULATED", "INFERRED", "PROPOSED", "UNKNOWN"} <= set(
        ko["epistemology"]
    )
    assert "parar" in " ".join(ko["sufficiency"])
    assert "PARTIAL" in ko["gap_handling"]["vocabulary"]
    assert "COMPOSITION_GATE" in ko["routing"]["MULTI_SOURCE_RECONCILIATION"]["gates"]


def test_catalog_and_mcp_discover_directives_are_identical(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.get_technical_actions",
        lambda: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "test-secret-only",
    )
    with patch(
        "app.application.external_capabilities.catalog_service.user_can_search_products",
        return_value=True,
    ):
        catalog = build_gpt_catalog()
    discovered = discover_delpi_information(query="conceito estoque", actor_id="test-user")
    directives = DaviAgentIntelligenceService.agent_directives()
    assert catalog["capability_surface"]["agent_directives"] == directives
    assert discovered["capability_surface"]["agent_directives"] == directives


def test_where_used_and_reverse_bom_paraphrases_rank_correctly() -> None:
    actions = [
        a for a in get_technical_actions()
        if a.executable and a.operation_id in {"get_product_structure", "get_product_parents"}
    ]
    assert {a.operation_id for a in actions} == {"get_product_structure", "get_product_parents"}
    for query in (
        "Onde o produto 10080001 é utilizado?",
        "BOM reversa do produto 10080001",
        "Onde o produto 10080001 é usado?",
    ):
        ranked = retrieve_eligible_actions(query, actions, top_k=2)
        assert ranked and ranked[0][0].operation_id == "get_product_parents", query
    direct = retrieve_eligible_actions("estrutura do produto 10080001", actions, top_k=2)
    assert direct and direct[0][0].operation_id == "get_product_structure"


def test_sql_generic_and_mutation_requests_still_have_no_candidates() -> None:
    actions = get_technical_actions()
    for query in (
        "Altere o estoque do produto 10080055",
        "SELECT * FROM SB1010",
        "Execute SQL arbitrário SELECT da SB1010",
    ):
        assert retrieve_eligible_actions(query, actions, top_k=10) == [], query


def test_inventory_nature_remains_canonical_not_redefined_by_agent() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    note = directives["flows"]["stock_and_supply"]["note"]
    assert "summary.net_value = surplus_value - shortage_value" in note
    assert "nature=shortage" in note and "nature=surplus" in note
    assert "D3_DOC" not in str(_ko())
