"""Concept-intent guard — pure knowledge questions must never surface
operational business candidates."""

from __future__ import annotations

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.concept_intent_guard import (
    is_pure_concept_intent,
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
    ranked = retrieve_eligible_actions(query, get_technical_actions(), top_k=10)
    # Pure concepts may only surface the governed knowledge READ capability —
    # never an operational business action.
    assert {a.operation_id for a, _ in ranked} <= {
        "read_governed_technical_knowledge"
    }


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
