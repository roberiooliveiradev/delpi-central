"""DAVI Stage 3: enterprise READ intelligence acceptance without new permissions.

Static contract test: approved allowlist, source status, provider/identity gates.
DOES NOT prove Agent Studio sync, runtime values or second-user AuthZ.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.davi_agent_intelligence_service import (
    DAVI_AGENT_DIRECTIVES_MAX_BYTES,
    DaviAgentIntelligenceService,
)
from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)

_ROOT = Path(__file__).resolve().parents[1]
_MATRIX_PATH = _ROOT / "tests/fixtures/davi_enterprise_intelligence_acceptance_v1.json"
_TOPIC_PATH = _ROOT / "docs/integrations/evidence/davi-governed-knowledge-topics-v1.json"
_READY = {"CONTRACT_PROVEN_RUNTIME_PENDING", "MIXED_PROVIDER_PENDING"}
_GAP = {"TO_INVENTORY", "UNSUPPORTED", "GUIDANCE_PROVIDER_PENDING"}
_ALLOWED_SOURCES = {
    "API_DELPI", "GOVERNED_FILES", "API_DELPI_PLUS_GOVERNED_FILES",
    "CORE_SOLUTION_REGISTRY", "NONE",
}


@pytest.fixture(scope="module")
def matrix() -> dict:
    return json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def allowed_operations() -> dict:
    allowlist = load_external_read_allowlist()
    return {row["operationId"]: row for row in allowlist["operations"]}


def test_e01_schema_and_evidence_ladder_are_fail_closed(matrix: dict) -> None:
    assert matrix["schema_version"] == "davi-enterprise-intelligence-acceptance-v1"
    assert matrix["identity"] == "END_USER_ACCOUNT"
    assert matrix["business_authorization"] == "FINAL_BACKEND_CANONICAL"
    assert matrix["tool_surface"] == [
        "discover_delpi_information", "execute_delpi_information"
    ]
    evidence = matrix["acceptance"]
    assert evidence["provider_sync"] == "TEST_NOT_RUN"
    assert evidence["provider_preview"] == "TEST_NOT_RUN"
    assert evidence["second_user_identity"] == "PENDING"
    assert evidence["negative_business_authz"] == "PENDING"
    assert evidence["external_core_approval"] == "TO_INVENTORY"
    assert evidence["global_shortage_business_contract"] == "TO_INVENTORY"


def test_e02_each_case_is_identifiable_and_references_known_routing(matrix: dict) -> None:
    cases = matrix["scenarios"]
    assert len(cases) == 14
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    routes = DaviAgentIntelligenceService.agent_directives()[
        "knowledge_orchestration"
    ]["routing"]
    for case in cases:
        assert case["id"].startswith("EI")
        assert case["query"] and case["name"]
        assert case["intent"] in routes
        assert case["source"] in _ALLOWED_SOURCES
        assert case["contract_status"] in _READY | _GAP
        assert case["completeness"] and case["expected"]
        assert isinstance(case["operations"], list)
        assert isinstance(case["response_fields"], list)


def test_e03_source_ready_actions_remain_eligible_and_fields_allowlisted(
    matrix: dict, allowed_operations: dict
) -> None:
    live_actions = {
        action.operation_id
        for action in get_technical_actions()
        if action.executable
    }
    for case in matrix["scenarios"]:
        if case["contract_status"] not in _READY:
            assert case["operations"] == [], case["id"]
            assert case["response_fields"] == [], case["id"]
            continue
        assert case["operations"], case["id"]
        assert case["source"] in {"API_DELPI", "API_DELPI_PLUS_GOVERNED_FILES"}
        for operation_id in case["operations"]:
            assert operation_id in allowed_operations, case["id"]
            assert operation_id in live_actions, case["id"]
            operation = allowed_operations[operation_id]
            assert operation["executionMode"] in {
                "catalog_action", "approved_external_capability",
            }
            assert set(case["response_fields"]) <= set(
                operation["approvedResponseFields"]
            ), case["id"]
            assert set(case["required_input_fields"]) <= set(
                operation["approvedInputFields"]
            ), case["id"]


def test_e04_no_direct_tool_or_core_sql_added(matrix: dict) -> None:
    prohibited = {"execute_readonly_sql", "POST /data/sql", "generic_proxy"}
    all_ids = {op for c in matrix["scenarios"] for op in c["operations"]}
    assert not (all_ids & prohibited)
    assert len(matrix["tool_surface"]) == 2
    core = next(c for c in matrix["scenarios"] if c["id"] == "EI12")
    assert core["contract_status"] == "TO_INVENTORY"
    assert core["operations"] == []
    assert core["expected"] == "REPORT_UNAVAILABLE_SOURCE_NOT_ABSENCE"


def test_e05_restrict_global_shortage_and_cross_domain_inference(matrix: dict) -> None:
    limited = next(c for c in matrix["scenarios"] if c["id"] == "EI07")
    global_query = next(c for c in matrix["scenarios"] if c["id"] == "EI10")
    reconciliation = next(c for c in matrix["scenarios"] if c["id"] == "EI11")
    assert limited["operations"] == ["get_product_raw_material_set_shortages"]
    assert limited["required_input_fields"] == ["code", "branch"]
    for scenario in (global_query, reconciliation):
        assert scenario["contract_status"] == "TO_INVENTORY"
        assert scenario["operations"] == []
        assert scenario["expected"] in {
            "REPORT_CAPABILITY_GAP_NOT_GLOBAL_ASSERTION",
            "NO_AGENT_SIDE_JOIN_OR_BUSINESS_CLASSIFIER",
        }


def test_e06_third_party_knowledge_and_concepts_do_not_grant_live_reads(
    matrix: dict,
) -> None:
    topics = json.loads(_TOPIC_PATH.read_text(encoding="utf-8"))
    ids = {topic["id"] for topic in topics["topics"]}
    for case in matrix["scenarios"]:
        topic_id = case["knowledge_topic"]
        if topic_id is not None:
            assert topic_id in ids
            assert case["source"] in {
                "GOVERNED_FILES", "API_DELPI_PLUS_GOVERNED_FILES",
            }
    mi = next(c for c in matrix["scenarios"] if c["id"] == "EI08")
    assert mi["intent"] == "PURE_CONCEPT"
    assert mi["operations"] == []
    assert mi["contract_status"] == "GUIDANCE_PROVIDER_PENDING"


def test_e07_write_and_sql_requests_are_not_executable(matrix: dict) -> None:
    candidates = get_technical_actions()
    for key in ("EI13", "EI14"):
        case = next(c for c in matrix["scenarios"] if c["id"] == key)
        assert case["intent"] == "WRITE_OR_GENERIC_SQL"
        assert case["contract_status"] == "UNSUPPORTED"
        assert case["operations"] == []
        assert retrieve_eligible_actions(case["query"], candidates, top_k=5) == []


def test_e08_where_used_and_structure_governance_are_preserved(matrix: dict) -> None:
    query = next(c for c in matrix["scenarios"] if c["id"] == "EI03")["query"]
    relevant = [
        action for action in get_technical_actions()
        if action.executable
        and action.operation_id in {"get_product_parents", "get_product_structure"}
    ]
    ranked = retrieve_eligible_actions(query, relevant, top_k=2)
    assert ranked
    assert ranked[0][0].operation_id == "get_product_parents"


def test_e09_pagination_and_uncertainty_must_be_visible(matrix: dict) -> None:
    lookup = {c["id"]: c for c in matrix["scenarios"]}
    assert "pagination" in lookup["EI03"]["completeness"]
    assert "is_complete" in lookup["EI04"]["completeness"]
    assert "is_complete" in lookup["EI06"]["completeness"]
    assert "global_coverage_not_proven" in lookup["EI10"]["completeness"]
    ko = DaviAgentIntelligenceService.agent_directives()["knowledge_orchestration"]
    assert "SEARCH_MISS IS_NOT PROOF_OF_ABSENCE" in ko["precedence"]
    assert "PARTIAL" in ko["gap_handling"]["vocabulary"]


def test_e10_instructions_budget_and_identity_stay_fixed(matrix: dict) -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["read_only"] is True
    assert DaviAgentIntelligenceService.directives_serialized_size() <= DAVI_AGENT_DIRECTIVES_MAX_BYTES
    sources = directives["knowledge_orchestration"]["sources"]
    assert sources["solution_ecosystem"]["access"] == "NOT_CONNECTED_TO_DAVI"
    assert sources["governed_knowledge"]["provider_status"] == "TEST_NOT_RUN"
    assert matrix["identity"] == "END_USER_ACCOUNT"
