"""DAVI Stage 3: offline contract E2E without ERP, SSH, provider or Core calls.

Real broker application code executes against a fake canonical catalog adapter.
This proves static/projection/token/negative contracts, NOT backend business
authorization, actual user rights, business results, or deployed Agent Studio.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
)
from app.application.external_capabilities.dynamic_information.concept_intent_guard import (
    is_pure_concept_intent,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)

_API_ROOT = Path(__file__).resolve().parents[1]
_MATRIX = _API_ROOT / "tests/fixtures/davi_enterprise_intelligence_acceptance_v1.json"
_CORE_PROPOSAL = _API_ROOT / "docs/integrations/evidence/davi-core-solution-catalog-ratification-v1.json"
_SECRET = "synthetic-hmac-only-no-erp"
_ACTOR = "offline-user-a"


@pytest.fixture(scope="module")
def cases() -> dict[str, dict]:
    matrix = json.loads(_MATRIX.read_text(encoding="utf-8"))
    return {case["id"]: case for case in matrix["scenarios"]}


@pytest.fixture()
def offline_tokens(monkeypatch) -> None:
    for where in ("discover_service", "execute_service"):
        monkeypatch.setattr(
            "app.application.external_capabilities.dynamic_information."
            f"{where}.candidate_token_secret",
            lambda: _SECRET,
        )


def _token_for(query: str, expected: str) -> str:
    found = discover_delpi_information(
        query=query,
        actor_id=_ACTOR,
        top_k=10,
    )
    matches = [
        value for value in found["candidates"]
        if value["action_id"] == expected
    ]
    assert matches, (
        f"{expected} not returned by actual discovery for {query!r}; "
        f"candidates={[v['action_id'] for v in found['candidates']]}"
    )
    return matches[0]["candidate_token"]


@pytest.mark.parametrize("key", [f"EI{number:02d}" for number in range(1, 8)])
def test_s01_approved_intents_are_semantically_discoverable(
    key: str, cases: dict[str, dict]
) -> None:
    """Ranking checks are on *real governed metadata*, never a fake action."""
    case = cases[key]
    ranked = retrieve_eligible_actions(
        case["query"], get_technical_actions(), top_k=10,
    )
    candidates = [action.operation_id for action, _ in ranked]
    assert case["operations"][0] in candidates[:5], (
        f"{key}: wanted {case['operations'][0]} in top5; got {candidates[:10]}"
    )


def test_s01_siblings_keep_description_vs_dictionary_and_shortage_vs_status(
    cases: dict[str, dict]
) -> None:
    actions = get_technical_actions()
    scenarios = [
        (
            cases["EI01"]["query"],
            "search_products",
            "search_protheus_columns_by_description",
        ),
        (
            cases["EI07"]["query"],
            "get_product_raw_material_set_shortages",
            "get_product_production_status",
        ),
    ]
    for query, expected, competing in scenarios:
        ranked = retrieve_eligible_actions(query, actions, top_k=10)
        returned = [action.operation_id for action, _ in ranked]
        assert returned and returned[0] == expected, (query, returned)
        assert returned[0] != competing

    # Semantic siblings: a Protheus column and normal production-status
    # question must remain different intents, not stolen by the new aliases.
    for query, expected in [
        ("Qual coluna do Protheus armazena a descrição do produto?", "search_protheus_columns_by_description"),
        ("Qual o status de produção do produto 10080010?", "get_product_production_status"),
    ]:
        ranked = retrieve_eligible_actions(query, actions, top_k=10)
        returned = [action.operation_id for action, _ in ranked]
        assert expected in returned[:5], (query, returned)



def test_s02_pure_concept_does_not_mint_operational_candidate(
    offline_tokens, cases: dict[str, dict]
) -> None:
    case = cases["EI08"]
    assert is_pure_concept_intent(case["query"])
    discovered = discover_delpi_information(
        query=case["query"], actor_id=_ACTOR, top_k=10
    )
    assert discovered["candidate_count"] == 0
    assert discovered["candidates"] == []
    # Approved metadata inventory can exceed dynamically executable OpenAPI
    # entries (e.g. a missing baseline path or malformed response binding).
    # Compare the actual broker's availability, never a hardcoded allowlist size.
    assert discovered["eligible_action_count"] == sum(
        1 for action in get_technical_actions() if action.executable
    )
    assert discovered["eligible_action_count"] > 0
    # No Knowledge answer implied: provider-native Files remain untested.


def test_s03_mixed_knowledge_plus_live_read_keeps_only_governed_candidates(
    cases: dict[str, dict]
) -> None:
    case = cases["EI09"]
    assert is_pure_concept_intent(case["query"]) is False
    ranked = retrieve_eligible_actions(
        case["query"], get_technical_actions(), top_k=10
    )
    ids = [action.operation_id for action, _ in ranked]
    assert case["operations"][0] in ids[:5], ids
    assert all(action.executable for action, _ in ranked)


def test_s04_two_real_broker_reads_remain_separate_and_allowlisted(
    offline_tokens, cases: dict[str, dict]
) -> None:
    """No Agent-side join or global-shortage assessment is introduced."""
    stock_id = cases["EI02"]["operations"][0]
    shortage_id = cases["EI07"]["operations"][0]
    stock_token = _token_for(cases["EI02"]["query"], stock_id)
    shortage_token = _token_for(cases["EI07"]["query"], shortage_id)
    seen: list[tuple[str, dict]] = []

    class FakeCanonicalExecutor:
        def execute(self, *, action_id, validated_arguments):
            seen.append((action_id, dict(validated_arguments)))
            if action_id == stock_id:
                return CatalogActionExecutionResult(
                    outcome="ok",
                    payload={
                        "success": True,
                        "data": {
                            "items": [{
                                "product_code": "10080010",
                                "branch": "01",
                                "warehouse": "01",
                                "current_quantity": 7,
                                "available_quantity": 3,
                                "unit_cost": 999.99,
                                "customer_reference": "must-not-leak",
                            }],
                            "page": 1, "page_size": 50, "total": 1,
                            "total_pages": 1,
                        },
                    },
                )
            if action_id == shortage_id:
                return CatalogActionExecutionResult(
                    outcome="ok",
                    payload={
                        "success": True,
                        "data": {
                            "product": {
                                "product_code": "10080010",
                                "product_description": "SYNTHETIC PA",
                                "unit": "UN",
                                "product_type": "PA",
                                "internal_cost": 888.88,
                            },
                            "sets": [{
                                "production_order": "SYNTHETIC-OP",
                                "planned_start_date": "2026-10-16",
                                "due_date": "2026-10-21",
                                "open_quantity": 2,
                                "status": "SYNTHETIC",
                                "short_material_count": 1,
                                "materials": [{
                                    "product_code": "SYNTHETIC-MP",
                                    "shortage_quantity": 5,
                                    "needed_quantity": 8,
                                    "available_stock": 3,
                                    "cost": 777,
                                }],
                            }],
                            "summary": {
                                "open_set_count": 1,
                                "at_risk_set_count": 1,
                                "short_mp_count": 1,
                                "internal_margin": 123,
                            },
                            "private_supplier": "must-not-leak",
                        },
                    },
                )
            raise AssertionError(f"unexpected external operation: {action_id}")

    executor = FakeCanonicalExecutor()
    stock = execute_delpi_information(
        candidate_token=stock_token,
        arguments={"code": "10080010", "branch": "01"},
        actor_id=_ACTOR,
        catalog_action_executor=executor,
    )
    shortage = execute_delpi_information(
        candidate_token=shortage_token,
        arguments={"code": "10080010", "branch": "01"},
        actor_id=_ACTOR,
        catalog_action_executor=executor,
    )

    assert seen == [
        (stock_id, {"code": "10080010", "branch": "01"}),
        (shortage_id, {"code": "10080010", "branch": "01"}),
    ]
    assert stock["status"] == shortage["status"] == "ok"
    assert stock["action_id"] == stock_id
    assert shortage["action_id"] == shortage_id
    assert stock["projection"] == shortage["projection"] == "approved_fields"
    assert stock["data"]["items"][0]["available_quantity"] == 3
    assert shortage["data"]["sets"][0]["production_order"] == "SYNTHETIC-OP"
    assert shortage["data"]["summary"]["at_risk_set_count"] == 1
    serialized = json.dumps([stock, shortage])
    for prohibited in (
        "must-not-leak", "unit_cost", "customer_reference",
        "internal_cost", "private_supplier", "internal_margin",
    ):
        assert prohibited not in serialized
    # The two results retain their individual provenance and limits;
    # no global ranking or enterprise-wide risk is computed here.
    assert "global_shortage_rank" not in serialized


def test_s05_one_forbidden_canonical_read_cannot_be_relabelled_as_success(
    offline_tokens, cases: dict[str, dict]
) -> None:
    shortage_id = cases["EI07"]["operations"][0]
    token = _token_for(cases["EI07"]["query"], shortage_id)

    class ForbiddenCanonical:
        calls = 0
        def execute(self, *, action_id, validated_arguments):
            self.calls += 1
            assert action_id == shortage_id
            return CatalogActionExecutionResult(outcome="forbidden")

    fake = ForbiddenCanonical()
    with pytest.raises(PermissionError, match="Forbidden"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "10080010", "branch": "01"},
            actor_id=_ACTOR,
            catalog_action_executor=fake,
        )
    assert fake.calls == 1
    # This synthetic 403 does NOT prove second-user business AuthZ in runtime.


def test_s06_token_bound_to_one_actor_does_not_execute_for_another(
    offline_tokens, cases: dict[str, dict]
) -> None:
    token = _token_for(cases["EI07"]["query"], cases["EI07"]["operations"][0])

    class ForbiddenIfCalled:
        def execute(self, *, action_id, validated_arguments):
            raise AssertionError("should fail at actor-bound token")

    with pytest.raises(CandidateTokenError, match="actor"):
        execute_delpi_information(
            candidate_token=token,
            arguments={"code": "10080010", "branch": "01"},
            actor_id="offline-user-b",
            catalog_action_executor=ForbiddenIfCalled(),
        )


@pytest.mark.parametrize(
    "bad_args",
    [
        {"code": "10080010"},
        {"code": "10080010", "branch": "01", "url": "https://invalid.example"},
        {"code": "10080010", "branch": "01", "operationId": "get_product_stock"},
    ],
)
def test_s07_missing_scope_and_transport_smuggling_rejected_before_adapter(
    offline_tokens, cases: dict[str, dict], bad_args: dict
) -> None:
    token = _token_for(cases["EI07"]["query"], cases["EI07"]["operations"][0])

    class ForbiddenIfCalled:
        def execute(self, *, action_id, validated_arguments):
            raise AssertionError("argument validation should precede transport")

    with pytest.raises(GovernedExecutionError):
        execute_delpi_information(
            candidate_token=token, arguments=bad_args, actor_id=_ACTOR,
            catalog_action_executor=ForbiddenIfCalled(),
        )


def test_s08_core_catalog_ratif_contract_does_not_expand_broker(
    cases: dict[str, dict],
) -> None:
    """A proposal/document is not source authorization, a tool or a contract."""
    proposal = json.loads(_CORE_PROPOSAL.read_text(encoding="utf-8"))
    assert proposal["state"] == "TO_INVENTORY"
    assert proposal["implementation_authorized"] is False
    assert proposal["source"]["technical_owner"] == "core-api"
    assert proposal["source"]["business_owner_status"] == "TO_INVENTORY"
    assert proposal["identity"]["mode"] == "END_USER_ONLY"
    assert proposal["identity"]["core_audience_compatibility"] == "TO_INVENTORY"
    assert proposal["capability"]["phase"] == "READ_PROPOSED_NOT_EXECUTABLE"
    assert proposal["capability"]["candidate_limit"] == 5
    assert set(proposal["capability"]["proposed_output_allowlist"]) == {
        "id", "name", "description", "category", "accessible"
    }
    assert cases["EI12"]["operations"] == []
    assert not any(
        action.operation_id.startswith("get_solution")
        or action.operation_id.startswith("list_solution")
        for action in get_technical_actions()
        if action.executable
    )
    assert proposal["release_gates"]["negative_business_authz"] == "PENDING"
