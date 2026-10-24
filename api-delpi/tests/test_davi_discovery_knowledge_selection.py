"""DAVI contextual discovery — document vs operational selection generalization.

TASK: DAVI-CONTEXTUAL-DISCOVERY-KNOWLEDGE-SELECTION-GENERALIZATION-01

Real-path discovery matrix (seed catalog → retrieve → rank → mint), not an
isolated classifier check. Every case records ALL candidates and scores so a
false selection is visible, not just the top-1 outcome.

Families:
  D — documentary questions must identify the governed-knowledge capability
      (pure-intent forms offer it as the ONLY candidate).
  O — operational questions keep legitimate business capabilities and never
      mint the document capability as sole/forced answer.
  C — compound questions keep both documentary and operational capabilities
      mintable within the candidate window.
  N — negative/safety behaviour (unsupported text, write intent) unchanged.
"""
from __future__ import annotations

import pytest

_KNOWLEDGE = "read_governed_technical_knowledge"


@pytest.fixture()
def discovery(monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information."
        "discover_service.candidate_token_secret",
        lambda: "synthetic-selection-secret",
    )
    from app.application.external_capabilities.dynamic_information.action_index import (
        reset_action_index_for_tests,
        seed_actions_from_openapi,
    )
    from app.application.external_capabilities.dynamic_information.discover_service import (
        discover_delpi_information,
    )
    from app.main import app

    reset_action_index_for_tests()
    seed_actions_from_openapi(app.openapi())

    def run(query: str) -> list[tuple[str, float]]:
        result = discover_delpi_information(query=query, actor_id="sel-user", top_k=6)
        return [
            (c["action_id"], c["retrieval_score"]) for c in result["candidates"]
        ]

    yield run
    reset_action_index_for_tests()


# ----------------------------- Family D — documentary -----------------------

@pytest.mark.parametrize(
    "query",
    [
        # Reported failing forms
        "Normas completas descrição matérias primas e TERM. BALA",
        "normas de codificação de produtos intermediários",
        # Equivalent long form (already worked — keep it green)
        "Quais são as normas técnicas de descrição de matérias-primas da DELPI?",
        # Telegraphic variants
        "Padrão de descrição técnica dos componentes",
        "regras de nomenclatura de produtos",
        "documentação técnica de cadastro",
        "manual de codificação de itens",
        "codificação de produtos intermediários",
        "nomenclatura técnica dos terminais",
        "diretrizes de descrição de materiais",
        # Verb-prefixed telegraphic
        "consultar normas de descrição de matéria prima",
        "consulte as regras de cadastro de produto",
        "buscar documentação de nomenclatura",
        # Question form about terminal-type nomenclature (TERM. BALA eval 1)
        "Quais normas técnicas tratam da nomenclatura de terminais tipo bala?",
        "Como funcionam as normas de codificação de produtos intermediários?",
    ],
)
def test_documentary_queries_surface_knowledge(discovery, query):
    ranked = discovery(query)
    ids = [a for a, _ in ranked]
    assert _KNOWLEDGE in ids, f"no documentary capability: {ranked}"
    # Documentary-intent queries offer guidance as the sole capability —
    # operational reads are never the answer to a norm/rules question.
    others = [a for a in ids if a != _KNOWLEDGE]
    assert not others, f"documentary query minted operational: {ranked}"


# ----------------------------- Family O — operational -----------------------

@pytest.mark.parametrize(
    "query",
    [
        "Me dê dois exemplos de terminal bala",
        "Localize o produto de código 10080092",
        "Qual é o estoque disponível deste produto?",
        "O que é a SB1?",
        "Quais produtos MP estão cadastrados?",
    ],
)
def test_operational_queries_keep_business_capabilities(discovery, query):
    ranked = discovery(query)
    ids = [a for a, _ in ranked]
    assert ids, f"operational query minted nothing: {query}"
    assert ids[0] != _KNOWLEDGE, (
        f"operational query must not top-rank guidance: {ranked}"
    )


def test_terminal_bala_examples_stay_operational(discovery):
    """TERM. BALA eval 2 — product examples are a business lookup, not docs."""
    ranked = discovery("Me dê dois exemplos de terminal bala")
    ids = [a for a, _ in ranked]
    assert "search_products" in ids, ranked
    # Guidance may co-mint (composite tolerance) but never displaces the
    # operational capability.
    assert ids[0] == "search_products", ranked


# ----------------------------- Family C — compound --------------------------

@pytest.mark.parametrize(
    "query",
    [
        "Explique as normas de terminais e encontre dois exemplos reais",
        "Quais são as regras de PI e quais itens cadastrados são PI?",
        "Interprete a nomenclatura técnica e consulte os registros correspondentes",
        "quais normas explicam a nomenclatura e quais produtos estão cadastrados",
    ],
)
def test_compound_queries_mint_both_capability_kinds(discovery, query):
    ranked = discovery(query)
    ids = [a for a, _ in ranked]
    assert _KNOWLEDGE in ids, f"compound lost documentary half: {ranked}"


# ----------------------------- Family N — negative --------------------------

def test_write_intent_still_mints_nothing(discovery):
    assert discovery("atualize o cadastro do produto 10080092") == []
    assert discovery("insira uma nova ordem de produção") == []


def test_empty_and_unsupported_queries(discovery):
    # Pure unsupported text mints nothing rather than a junk candidate.
    ranked = discovery("asdkfj qwer zxcv")
    assert ranked == []
