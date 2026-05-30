from unittest.mock import MagicMock

from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.infrastructure.config.settings import Settings


def test_should_synthesize_when_multiple_results(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS", 2)

    service = ChatWebSearchSynthesisService(llm_gateway=MagicMock())
    payload = {
        "searchStatus": "success",
        "results": [
            {
                "title": "Tyco International",
                "snippet": "Conglomerado de segurança.",
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

    assert service.should_synthesize(payload) is True


def test_synthesize_returns_llm_markdown(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS", 2)
    monkeypatch.setattr(Settings, "LLM_MAX_TOKENS", 768)

    llm = MagicMock()
    llm.generate.return_value = (
        "### 1. Tyco International\n\n"
        "Resumo histórico. [Wikipedia](https://pt.wikipedia.org/wiki/Tyco_International)\n\n"
        "### Linha do tempo resumida\n\n"
        "| Ano | Evento |\n| --- | --- |\n| 1960 | Fundação |\n"
    )

    service = ChatWebSearchSynthesisService(llm_gateway=llm)
    payload = {
        "query": "tyco",
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
                "snippet": "Conectores.",
                "url": "https://pt.wikipedia.org/wiki/TE_Connectivity",
                "source": "wikipedia_pt",
            },
        ],
    }

    answer = service.synthesize(payload, message="pesquise na internet sobre TYCO", fallback="fallback")

    assert answer is not None
    assert "Tyco International" in answer
    assert "| Ano | Evento |" in answer
    llm.generate.assert_called_once()


def test_synthesize_falls_back_on_llm_error(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SYNTHESIS_MIN_RESULTS", 2)

    llm = MagicMock()
    llm.generate.side_effect = RuntimeError("offline")

    service = ChatWebSearchSynthesisService(llm_gateway=llm)
    payload = {
        "searchStatus": "success",
        "results": [
            {"title": "A", "snippet": "1", "url": "https://a.test", "source": "x"},
            {"title": "B", "snippet": "2", "url": "https://b.test", "source": "y"},
        ],
    }

    assert service.synthesize(payload, fallback="resposta simples") == "resposta simples"
