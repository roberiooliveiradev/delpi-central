from app.domain.services.keyword_similarity import (
    keyword_overlap_score,
    keyword_overlap_score_significant,
    significant_query_tokens,
)


def test_keyword_overlap_score_prefers_matching_terms():
    score = keyword_overlap_score(
        "pedidos abertos do cliente",
        "Relatório de pedidos abertos na fila comercial",
    )

    assert score > 0.2


def test_keyword_overlap_score_is_zero_without_terms():
    assert keyword_overlap_score("ab", "conteúdo qualquer") == 0.0


def test_keyword_overlap_prefers_term_coverage_over_frequency():
    """Doc com 1 token repetido não vence doc que cobre mais termos da query."""
    query = "normas técnicas DELPI matéria-prima"
    noisy = ("delpi " * 80) + "cadastro interno"
    grounded = "Normas Técnicas DELPI para matéria-prima e grupos 1001–1025"
    assert keyword_overlap_score(query, grounded) > keyword_overlap_score(query, noisy)


def test_significant_query_tokens_drops_question_stopwords():
    tokens = significant_query_tokens(
        "o que dizem as normas técnicas DELPI sobre matéria-prima?",
        stopwords={"dizem", "sobre", "que"},
        max_terms=8,
    )
    assert "normas" in tokens
    assert "dizem" not in tokens
    assert "sobre" not in tokens


def test_keyword_overlap_significant_uses_stopwords():
    score = keyword_overlap_score_significant(
        "o que dizem as normas técnicas",
        "Normas Técnicas DELPI",
        stopwords={"dizem", "que"},
    )
    assert score > 0.2
