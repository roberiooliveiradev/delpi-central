from app.domain.services.keyword_similarity import keyword_overlap_score


def test_keyword_overlap_score_prefers_matching_terms():
    score = keyword_overlap_score(
        "pedidos abertos do cliente",
        "Relatório de pedidos abertos na fila comercial",
    )

    assert score > 0.2


def test_keyword_overlap_score_is_zero_without_terms():
    assert keyword_overlap_score("ab", "conteúdo qualquer") == 0.0
