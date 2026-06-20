"""Testes do serviço de normalização/retry de consultas web."""

from app.domain.services.web_search_query_service import WebSearchQueryService


def test_build_english_retry_query_from_portuguese_phrase():
    retry = WebSearchQueryService.build_english_retry_query(
        "python linguagem de programacao"
    )

    assert retry == "python programming language"


def test_is_useful_payload_rejects_no_results():
    payload = WebSearchQueryService.build_no_results_payload("x", provider="duckduckgo")

    assert WebSearchQueryService.is_useful_payload(payload) is False


def test_is_useful_payload_accepts_real_snippet():
    payload = {
        "results": [
            {
                "title": "Python",
                "snippet": "High-level language.",
                "source": "instant_answer",
            }
        ]
    }

    assert WebSearchQueryService.is_useful_payload(payload) is True


def test_rank_results_for_query_prioritizes_entity_match():
    payload = {
        "results": [
            {
                "title": "William Ewart Gladstone",
                "snippet": "British statesman.",
                "source": "related_topic",
            },
            {
                "title": "WEG Industries",
                "snippet": "A Brazilian company operating worldwide in electric engineering.",
                "source": "related_topic",
            },
        ]
    }

    ranked = WebSearchQueryService.rank_results_for_query(payload, "weg")

    assert ranked["results"][0]["title"] == "WEG Industries"


def test_build_no_results_payload_has_explicit_status():
    payload = WebSearchQueryService.build_no_results_payload(
        "consulta vazia",
        provider="tavily",
    )

    assert payload["searchStatus"] == "no_results"
    assert payload["results"][0]["source"] == "no_results"


def test_sanitize_query_strips_company_prefix():
    assert WebSearchQueryService.sanitize_query("a empresa tyco") == "tyco"


def test_build_search_candidates_includes_entity_boosts():
    candidates = WebSearchQueryService.build_search_candidates("a empresa tyco")

    assert candidates[0] == "tyco"
    assert "Tyco International" in candidates
    assert "tyco company" in candidates or "Tyco company" in candidates


def test_build_english_retry_query_strips_company_filler():
    retry = WebSearchQueryService.build_english_retry_query("a empresa tyco")

    assert retry == "tyco"


def test_build_search_candidates_skips_english_retry_when_disabled(monkeypatch):
    monkeypatch.setattr(
        "app.domain.services.web_search_query_service.WebSearchQueryService._english_retry_enabled",
        classmethod(lambda cls: False),
    )

    candidates = WebSearchQueryService.build_search_candidates(
        "python linguagem de programacao"
    )

    assert "python programming language" not in candidates
    assert candidates[0] == "python linguagem de programacao"
