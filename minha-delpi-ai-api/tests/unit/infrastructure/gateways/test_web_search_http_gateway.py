from app.infrastructure.gateways.web_search_http_gateway import WebSearchHttpGateway
from app.infrastructure.gateways.web_search_providers import (
    DuckDuckGoInstantProvider,
    SerperSearchProvider,
    TavilySearchProvider,
)


class FakeResponse:
    def __init__(self, payload, *, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")

    def json(self):
        return self._payload


def test_duckduckgo_parses_instant_answer(monkeypatch):
    provider = DuckDuckGoInstantProvider()

    def fake_get(*args, **kwargs):
        return FakeResponse(
            {
                "Heading": "Python",
                "AbstractText": "Linguagem de programação.",
                "AbstractURL": "https://example.com/python",
                "RelatedTopics": [
                    {"Text": "Python software", "FirstURL": "https://example.com/2"},
                ],
            }
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.requests.get",
        fake_get,
    )

    payload = provider.search("python", max_results=3)

    assert payload["searchStatus"] == "success"
    assert payload["results"][0]["snippet"] == "Linguagem de programação."


def test_gateway_retries_english_when_portuguese_empty(monkeypatch):
    gateway = WebSearchHttpGateway()
    calls: list[str] = []

    def fake_search(self, query, *, max_results):
        calls.append(query)

        if query == "python linguagem de programacao":
            return {"query": query, "results": [], "provider": self.name}

        if query == "python programming language":
            return {
                "query": query,
                "results": [
                    {
                        "title": "Python",
                        "snippet": "High-level language.",
                        "url": "https://example.com/python",
                        "source": "instant_answer",
                    }
                ],
                "provider": self.name,
                "searchStatus": "success",
            }

        return {"query": query, "results": [], "provider": self.name}

    monkeypatch.setattr(DuckDuckGoInstantProvider, "search", fake_search)
    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_http_gateway.resolve_web_search_providers",
        lambda: [DuckDuckGoInstantProvider()],
    )

    payload = gateway.search("python linguagem de programacao", max_results=3)

    assert payload["searchStatus"] == "success"
    assert payload["retriedQuery"] == "python programming language"
    assert calls[0] == "python linguagem de programacao"
    assert "python programming language" in calls


def test_gateway_returns_no_results_when_all_attempts_fail(monkeypatch):
    gateway = WebSearchHttpGateway()

    def fake_search(self, query, *, max_results):
        return {"query": query, "results": [], "provider": self.name}

    monkeypatch.setattr(DuckDuckGoInstantProvider, "search", fake_search)
    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_http_gateway.resolve_web_search_providers",
        lambda: [DuckDuckGoInstantProvider()],
    )

    payload = gateway.search("tema inexistente xyz", max_results=3)

    assert payload["searchStatus"] == "no_results"
    assert payload["results"][0]["source"] == "no_results"


def test_tavily_parses_results(monkeypatch):
    provider = TavilySearchProvider()

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.Settings.CHAT_WEB_SEARCH_TAVILY_API_KEY",
        "tvly-test",
    )

    def fake_post(*args, **kwargs):
        return FakeResponse(
            {
                "results": [
                    {
                        "title": "Python.org",
                        "url": "https://python.org",
                        "content": "Python is a programming language.",
                    }
                ]
            }
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.requests.post",
        fake_post,
    )

    payload = provider.search("python", max_results=2)

    assert payload["searchStatus"] == "success"
    assert payload["provider"] == "tavily"
    assert payload["results"][0]["source"] == "tavily"


def test_serper_parses_organic_results(monkeypatch):
    provider = SerperSearchProvider()

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.Settings.CHAT_WEB_SEARCH_SERPER_API_KEY",
        "serper-test",
    )

    def fake_post(*args, **kwargs):
        return FakeResponse(
            {
                "organic": [
                    {
                        "title": "Python",
                        "link": "https://python.org",
                        "snippet": "Official site.",
                    }
                ]
            }
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.requests.post",
        fake_post,
    )

    payload = provider.search("python", max_results=2)

    assert payload["searchStatus"] == "success"
    assert payload["results"][0]["source"] == "serper"


def test_gateway_empty_query():
    gateway = WebSearchHttpGateway()

    payload = gateway.search("   ")

    assert payload["searchStatus"] == "no_results"
