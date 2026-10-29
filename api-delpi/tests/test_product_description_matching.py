# tests/test_product_description_matching.py
"""Contract tests for the bounded industrial-description matching.

Task DELIA-C3-API-DELPI-PRODUCT-SEARCH-REMEDIATION-01. These tests pin
the SQL semantics produced by ``build_description_matching`` — AND
token conjunction, word-boundary matching, the controlled abbreviation
table, stopword handling, LIKE escaping and the relevance score. The
live behavioral proof is the local TOTVS A/B probe (doc 204).
"""

import re

import pytest

from app.infrastructure.persistence.totvs.product_repositories.product_description_matching import (
    build_description_matching,
    normalize_description_tokens,
)

COL = "SB1.B1_DESC"


def _built(description):
    result = build_description_matching(description)
    assert result is not None
    return result


class TestTokenNormalization:
    def test_stopwords_are_dropped(self):
        assert normalize_description_tokens("terminal de bala") == [
            "TERMINAL",
            "BALA",
        ]

    def test_stopword_only_query_falls_back_to_raw_tokens(self):
        assert normalize_description_tokens("de e") == ["DE", "E"]

    def test_edge_punctuation_is_stripped(self):
        assert normalize_description_tokens("TERM., bala") == ["TERM", "BALA"]

    def test_inner_punctuation_survives(self):
        assert normalize_description_tokens("0,50-2,27mm2") == ["0,50-2,27MM2"]

    def test_uppercased(self):
        assert normalize_description_tokens("Cabo Flex") == ["CABO", "FLEX"]


class TestWhereSemantics:
    def test_every_token_produces_one_anded_group(self):
        where, params, *_ = _built("terminal bala")
        groups = re.findall(r"\bAND\b", where)
        # one AND joins the two token groups; no OR bridges them
        assert len(groups) == 1
        assert where.count(" OR ") > 0  # alternatives live inside groups

    def test_word_boundary_required(self):
        where, params, *_ = _built("bala")
        # token must be a word prefix: padded column + boundary before
        assert "CONCAT" in where
        assert params == ["%[^A-Z0-9]BALA%"]

    def test_abbreviation_bridge_terminal(self):
        where, params, *_ = _built("terminal")
        # TERMINAL prefix OR exact-word TERM — never TERM prefix
        assert not any(p == "%[^A-Z0-9]TERM%" for p in params)
        assert "%[^A-Z0-9]TERM[^A-Z0-9]%" in params
        assert "%[^A-Z0-9]TERMINAL%" in params

    def test_abbreviation_bridge_term(self):
        where, params, *_ = _built("TERM.")
        assert "%[^A-Z0-9]TERMINAL%" in params
        assert "%[^A-Z0-9]TERM[^A-Z0-9]%" in params

    def test_unknown_abbreviation_gets_no_expansion(self):
        where, params, *_ = _built("xyzq")
        assert params == ["%[^A-Z0-9]XYZQ%"]

    def test_like_metacharacters_escaped(self):
        _, params, *_ = _built("50% a_b [x]")
        assert any("\\%" in p for p in params)
        assert any("\\_" in p for p in params)
        assert any("\\[" in p for p in params)

    def test_all_likes_carry_escape_clause(self):
        where, *_ = _built("terminal bala")
        assert where.count(" ESCAPE '\\'") == where.count(" LIKE ")

    def test_empty_description_returns_none(self):
        assert build_description_matching("") is None
        assert build_description_matching("   ") is None


class TestScoring:
    def test_phrase_prefix_bonus_present(self):
        _, _, score, score_params = _built("TERM. BALA")
        assert "THEN 100" in score
        assert "TERM. BALA[^A-Z0-9]%" in score_params
        assert "TERM. BALA" in score_params

    def test_phrase_bonus_requires_word_boundary(self):
        # "TERM BALA%" alone would promote TERM BALANCA items.
        _, _, score, score_params = _built("term bala")
        assert "TERM BALA%" not in score_params

    def test_no_phrase_bonus_for_single_token(self):
        # Single-token "phrase prefix" = word-prefix noise; BALANCA
        # must not score above an exact-word BALA hit via bonuses.
        _, _, score, _ = _built("bala")
        assert "THEN 100" not in score
        assert "THEN 60" not in score

    def test_normalized_phrase_bonus_present(self):
        _, _, score, score_params = _built("TERM BALA")
        assert "REPLACE" in score
        assert "TERM BALA[^A-Z0-9]%" in score_params

    def test_exact_word_scores_above_prefix(self):
        _, _, score, score_params = _built("bala")
        assert "THEN 30" in score
        assert "THEN 15" in score
        # exact-word alternatives for the token itself
        assert "%[^A-Z0-9]BALA[^A-Z0-9]%" in score_params

    def test_param_alignment(self):
        where, wparams, score, sparams = _built("terminal bala")
        assert where.count("?") == len(wparams)
        assert score.count("?") == len(sparams)


class TestRepositoryIntegration:
    def test_repository_uses_matching_builder(self):
        import inspect

        from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
            ProductRepository,
        )

        src = inspect.getsource(ProductRepository.search_products)
        assert "build_description_matching" in src
        # legacy OR-substring join is gone
        assert '" OR ".join' not in src
