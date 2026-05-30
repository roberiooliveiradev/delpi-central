from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.web_search_providers import resolve_web_search_providers


def test_resolve_auto_prefers_tavily_when_key_present(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "auto")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TAVILY_API_KEY", "tvly-test")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_SERPER_API_KEY", "")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_BING_API_KEY", "")

    providers = resolve_web_search_providers()

    assert [provider.name for provider in providers] == [
        "tavily",
        "duckduckgo_instant_answer",
    ]


def test_resolve_explicit_duckduckgo_only(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_PROVIDER", "duckduckgo")
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_TAVILY_API_KEY", "tvly-test")

    providers = resolve_web_search_providers()

    assert len(providers) == 1
    assert providers[0].name == "duckduckgo_instant_answer"
