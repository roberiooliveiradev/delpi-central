from app.domain.services.chat_web_search_direct_answer_service import (
    ChatWebSearchDirectAnswerService,
)


def test_format_success_from_instant_answer():
    payload = {
        "query": "python linguagem de programacao",
        "searchStatus": "success",
        "retriedQuery": "python programming language",
        "results": [
            {
                "title": "Python (programming language)",
                "snippet": "Python is a high-level programming language.",
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "source": "instant_answer",
            },
            {
                "title": "NumPy",
                "snippet": "NumPy library.",
                "url": "https://duckduckgo.com/NumPy",
                "source": "related_topic",
            },
        ],
    }

    answer = ChatWebSearchDirectAnswerService.format(payload, message="pesquise na internet")

    assert answer is not None
    assert "internet pública" in answer
    assert "Python is a high-level programming language." in answer
    assert "wikipedia.org" in answer
    assert "não pesquis" not in answer.lower()


def test_format_no_results():
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
