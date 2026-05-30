from unittest.mock import patch

from app.domain.services.web_search_portuguese_content_service import (
    WebSearchPortugueseContentService,
)


def test_localize_payload_replaces_english_snippet_with_wikipedia_pt():
    payload = {
        "query": "python linguagem de programacao",
        "searchStatus": "success",
        "retriedQuery": "python programming language",
        "results": [
            {
                "title": "Python (programming language)",
                "snippet": "Python is a high-level, general-purpose programming language.",
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "source": "instant_answer",
            }
        ],
    }

    pt_summary = {
        "title": "Python",
        "snippet": "Python é uma linguagem de programação de alto nível.",
        "url": "https://pt.wikipedia.org/wiki/Python",
        "source": "wikipedia_pt",
    }

    with patch.object(
        WebSearchPortugueseContentService,
        "_fetch_wikipedia_pt_summary",
        return_value=pt_summary,
    ):
        localized = WebSearchPortugueseContentService.localize_payload(payload)

    assert localized is not None
    assert localized["localizedFor"] == "pt-BR"
    assert localized["results"][0]["snippet"].startswith("Python é uma linguagem")
    assert localized["results"][0]["source"] == "wikipedia_pt"


def test_localize_payload_skips_when_query_not_portuguese():
    payload = {
        "query": "python programming language",
        "searchStatus": "success",
        "results": [
            {
                "title": "Python",
                "snippet": "Python is a high-level programming language.",
                "url": "https://en.wikipedia.org/wiki/Python",
                "source": "instant_answer",
            }
        ],
    }

    localized = WebSearchPortugueseContentService.localize_payload(payload)

    assert localized == payload
