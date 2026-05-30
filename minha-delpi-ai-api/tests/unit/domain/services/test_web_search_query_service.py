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


def test_build_no_results_payload_has_explicit_status():
    payload = WebSearchQueryService.build_no_results_payload(
        "consulta vazia",
        provider="tavily",
    )

    assert payload["searchStatus"] == "no_results"
    assert payload["results"][0]["source"] == "no_results"
