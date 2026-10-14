"""DAVI concept routing: presentation gate, not domain AuthZ or content lookup."""

from __future__ import annotations

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.concept_intent_guard import (
    is_pure_concept_intent,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.retrieval import (
    retrieve_eligible_actions,
)


@pytest.mark.parametrize(
    "query",
    [
        "O que significa MI?",
        "Qual é o significado de MI?",
        "O que quer dizer unidade de medida MI?",
        "Qual a diferença entre estoque físico e estoque reservado?",
        "Quais são as diferenças entre saldo físico e empenhado?",
        "Explique o conceito de furo de inventário.",
        "Qual o conceito de OTD?",
        "Defina custo médio.",
        "What does OTD mean?",
        "What is the difference between physical and reserved stock?",
        "Define safety stock.",
    ],
)
def test_pure_concept_never_surfaces_operational_candidates(query: str) -> None:
    assert is_pure_concept_intent(query) is True
    assert retrieve_eligible_actions(query, get_technical_actions(), top_k=10) == []


@pytest.mark.parametrize(
    "query",
    [
        "O que significa MI e qual o estoque do produto 10080010?",
        "Explique o conceito de ajuste de inventário e qual foi o valor líquido?",
        "Qual é a diferença entre estoque físico e reservado e qual o saldo atual?",
        "Qual o conceito de OTD neste mês?",
        "O que significa o saldo do produto hoje?",
        "Qual o saldo do produto 10080010?",
        "Onde o produto 10080001 é utilizado?",
        "Quais são as matérias-primas exclusivas?",
        "Como calcular o OTD de compras deste mês?",
        "Altere o estoque do produto 10080010.",
    ],
)
def test_mixed_ambiguous_and_operational_intents_not_suppressed(query: str) -> None:
    # Explicit mutation remains blocked independently by the write guard.
    assert is_pure_concept_intent(query) is False


def test_mixed_query_retains_approved_stock_discovery() -> None:
    query = "O que significa MI e qual o estoque do produto 10080010?"
    ranked = retrieve_eligible_actions(query, get_technical_actions(), top_k=10)
    assert "get_product_stock" in [action.operation_id for action, _ in ranked]


def test_no_token_minted_for_pure_concept_query(monkeypatch) -> None:
    # No production token or provider secret is used in this local test.
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "unit-only-concept-discovery-secret",
    )
    response = discover_delpi_information(
        query="O que significa MI?", actor_id="test-only-actor", top_k=5
    )
    assert response["candidate_count"] == 0
    assert response["candidates"] == []
    directives = response["capability_surface"]["agent_directives"]
    assert directives["knowledge_orchestration"]["routing"]["PURE_CONCEPT"][
        "required"
    ] == ["governed_knowledge"]


def test_no_change_to_backend_authz_and_broker_tool_surface() -> None:
    from app.application.external_capabilities.dynamic_information.candidate_token import (
        mint_candidate_token,
        parse_candidate_token,
        CandidateTokenError,
    )

    token = mint_candidate_token(
        action_id="synthetic-read",
        actor_id="user-A",
        secret="unit-test-secret",
        ttl_seconds=120,
        now=100,
    )
    assert parse_candidate_token(
        token, secret="unit-test-secret", expected_actor_id="user-A", now=105
    )["action_id"] == "synthetic-read"
    with pytest.raises(CandidateTokenError, match="actor"):
        parse_candidate_token(
            token, secret="unit-test-secret", expected_actor_id="user-B", now=105
        )
