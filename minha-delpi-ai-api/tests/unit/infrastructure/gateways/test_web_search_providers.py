from unittest.mock import MagicMock

from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.web_search_providers import (
    SearxngSearchProvider,
    resolve_web_search_providers,
)


def test_resolve_auto_prefers_tavily_when_key_present(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "auto")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TAVILY_API_KEY", "tvly-test")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SERPER_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_BING_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SEARXNG_BASE_URL", "http://searxng:8080")

    providers = resolve_web_search_providers()

    assert [provider.name for provider in providers] == [
        "tavily",
        "searxng",
        "duckduckgo_instant_answer",
    ]


def test_resolve_auto_uses_searxng_when_no_paid_keys(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "auto")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TAVILY_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SERPER_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_BING_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SEARXNG_BASE_URL", "http://searxng:8080")

    providers = resolve_web_search_providers()

    assert [provider.name for provider in providers] == [
        "searxng",
        "duckduckgo_instant_answer",
    ]


def test_resolve_explicit_duckduckgo_only(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "duckduckgo")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TAVILY_API_KEY", "tvly-test")

    providers = resolve_web_search_providers()

    assert len(providers) == 1
    assert providers[0].name == "duckduckgo_instant_answer"


def test_resolve_explicit_searxng(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "searxng")
    monkeypatch.setattr(
        Settings,
        "CHAT_WEB_SEARCH_SEARXNG_BASE_URL",
        "http://searxng:8080",
    )

    providers = resolve_web_search_providers()

    assert len(providers) == 1
    assert providers[0].name == "searxng"


def test_searxng_provider_maps_json_results(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SEARXNG_BASE_URL", "http://searxng:8080")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SEARXNG_LANGUAGE", "pt-BR")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SEARXNG_CATEGORIES", "general")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TIMEOUT_SECONDS", 5)

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {
                "title": "DigiKey - JST connector",
                "content": "Preço e estoque disponíveis.",
                "url": "https://www.digikey.com/product-detail/en/jst/123",
            }
        ]
    }

    monkeypatch.setattr(
        "app.infrastructure.gateways.web_search_providers.requests.get",
        lambda *args, **kwargs: response,
    )

    payload = SearxngSearchProvider().search("JST-SPS-21T-250S", max_results=5)

    assert payload["searchStatus"] == "success"
    assert payload["provider"] == "searxng"
    assert payload["results"][0]["source"] == "searxng"
    assert payload["results"][0]["url"].startswith("https://www.digikey.com/")
