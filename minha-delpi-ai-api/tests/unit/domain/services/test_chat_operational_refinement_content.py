"""Contrato do bundle operational_refinement — padrões e termos."""

from __future__ import annotations

from app.domain.services.chat_operational_refinement.chat_operational_refinement_content_service import (
    ChatOperationalRefinementContentService,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_vocabulary import (
    ChatOperationalRefinementVocabulary as VOCAB,
)


def test_operational_refinement_term_lists_exist():
    for key in (
        "filter",
        "nextPage",
        "prevPage",
        "depthIncrease",
        "moreResults",
        "stockReset",
    ):
        terms = ChatOperationalRefinementContentService.terms(key)
        assert terms, f"missing operational_refinement.terms.{key}"


def test_operational_refinement_patterns_compile():
    for key in ("branch", "warehouse", "maxDepth", "pageNumber"):
        pattern = ChatOperationalRefinementContentService.compile_pattern(key)
        assert pattern.search  # callable

    page_size = ChatOperationalRefinementContentService.compile_pattern_list("pageSize")
    assert len(page_size) >= 3


def test_vocabulary_lazy_patterns_match_samples():
    assert VOCAB.BRANCH_RE.search("filial 01")
    assert VOCAB.WAREHOUSE_RE.search("armazém 02")
    assert VOCAB.PAGE_NUMBER_RE.search("página 3")
    assert VOCAB.MAX_DEPTH_RE.search("profundidade 5")
    assert any(p.search("mostre 50 registros") for p in VOCAB.PAGE_SIZE_PATTERNS)
    assert "estoque completo" in VOCAB.STOCK_RESET_TERMS
    assert "filtre" in VOCAB.FILTER_TERMS
