from unittest.mock import Mock

from app.infrastructure.config.chat_runtime_intelligence_settings_adapter import (
    InfrastructureChatRuntimeIntelligenceSettingsAdapter,
)
from app.infrastructure.config.settings import Settings


def test_adapter_uses_env_default_without_repository():
    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter()

    assert adapter.web_search_enabled() == bool(Settings.CHAT_WEB_SEARCH_ENABLED)


def test_adapter_honors_runtime_override():
    repository = Mock()
    repository.get_chat_intelligence_settings.return_value = {"webSearchEnabled": False}

    adapter = InfrastructureChatRuntimeIntelligenceSettingsAdapter(repository)

    assert adapter.web_search_enabled() is False
