from unittest.mock import Mock

from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)
from app.domain.services.chat_runtime_intelligence_settings_service import (
    ChatRuntimeIntelligenceSettingsService,
)


def test_runtime_settings_service_delegates_to_port():
    port = Mock(spec=ChatRuntimeIntelligenceSettingsPort)
    port.web_search_enabled.return_value = True
    ChatRuntimeIntelligenceSettingsService.configure(port)

    assert ChatRuntimeIntelligenceSettingsService.web_search_enabled() is True

    port.web_search_enabled.assert_called_once()
