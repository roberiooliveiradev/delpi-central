from unittest.mock import Mock

from app.infrastructure.config.chat_runtime_intelligence_settings_adapter import (
    InfrastructureChatRuntimeIntelligenceSettingsAdapter,
)
from app.infrastructure.config.settings import Settings


def test_adapter_uses_defaults_when_repository_empty():
    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter()

    assert adapter.web_search_enabled() == bool(Settings.CHAT_WEB_SEARCH_ENABLED)


def test_adapter_uses_admin_runtime_over_environment(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_WEB_SEARCH_ENABLED", True)

    repository = Mock()
    repository.get_chat_intelligence_settings.return_value = {"webSearchEnabled": False}

    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter(repository)

    assert adapter.web_search_enabled() is False
