from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)


def test_format_success_from_instant_answer():
    payload = {
        "query": "python linguagem de programacao",
        "searchStatus": "success",
        "localizedFor": "pt-BR",
        "results": [
            {
                "title": "Python",
                "snippet": "Python é uma linguagem de programação de alto nível.",
                "url": "https://pt.wikipedia.org/wiki/Python",
                "source": "wikipedia_pt",
            },
        ],
    }

    answer = ChatWebSearchDirectAnswerService.format(payload, message="pesquise na internet")

    assert answer is not None
    assert "internet pública" in answer
    assert "Python é uma linguagem" in answer
    assert "pt.wikipedia.org" in answer
    assert "Resumo em português via Wikipedia" in answer


def test_format_prefers_wikipedia_pt_when_localized():
    payload = {
        "query": "python linguagem de programacao",
        "searchStatus": "success",
        "localizedFor": "pt-BR",
        "results": [
            {
                "title": "Python",
                "snippet": "Python é uma linguagem de programação de alto nível.",
                "url": "https://pt.wikipedia.org/wiki/Python",
                "source": "wikipedia_pt",
            },
            {
                "title": "Python (programming language)",
                "snippet": "Python is a high-level programming language.",
                "url": "https://en.wikipedia.org/wiki/Python",
                "source": "instant_answer",
            },
        ],
    }

    answer = ChatWebSearchDirectAnswerService.format(payload)

    assert answer is not None
    assert "Python é uma linguagem" in answer
    assert "Python is a high-level" not in answer


def test_format_no_results_message():
    payload = {
        "query": "tema xyz",
        "searchStatus": "no_results",
        "results": [
            {
                "title": "tema xyz",
                "snippet": "A busca na internet não retornou resultados úteis.",
                "source": "no_results",
            }
        ],
    }

    answer = ChatWebSearchDirectAnswerService.format(payload)

    assert answer is not None
    assert "não encontrei resultados úteis" in answer


def test_build_sources_from_web_results():
    payload = {
        "searchStatus": "success",
        "results": [
            {
                "title": "Tyco International",
                "snippet": "Conglomerado.",
                "url": "https://pt.wikipedia.org/wiki/Tyco_International",
                "source": "wikipedia_pt",
            },
            {
                "title": "TE Connectivity",
                "snippet": "Fabricante de conectores.",
                "url": "https://pt.wikipedia.org/wiki/TE_Connectivity",
                "source": "wikipedia_pt",
            },
        ],
    }

    sources = ChatWebSearchDirectAnswerService.build_sources(payload)

    assert len(sources) == 2
    assert sources[0]["scope"] == "web_search"
    assert sources[0]["sourceRef"].startswith("https://")
