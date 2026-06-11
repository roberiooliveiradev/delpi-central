from app.infrastructure.config.chat_runtime_intelligence_settings_adapter import (
    InfrastructureChatRuntimeIntelligenceSettingsAdapter,
)
from app.infrastructure.config.settings import Settings


def test_adapter_uses_environment():
    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter()

    assert adapter.web_search_enabled() == bool(Settings.CHAT_WEB_SEARCH_ENABLED)


def test_adapter_ignores_runtime_repository(monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_ENABLED", True)

    repository = Mock()
    repository.get_chat_intelligence_settings.return_value = {"webSearchEnabled": False}

    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter(repository)

    assert adapter.web_search_enabled() is True
