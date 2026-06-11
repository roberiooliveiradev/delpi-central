from __future__ import annotations

from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)
from app.infrastructure.config.settings import Settings


class InfrastructureChatRuntimeIntelligenceSettingsAdapter(
    ChatRuntimeIntelligenceSettingsPort,
):
    def __init__(self, settings_repository=None) -> None:
        # Repositório mantido por compatibilidade de wiring; runtime lê só o .env.
        self._settings_repository = settings_repository

    def web_search_enabled(self) -> bool:
        return bool(Settings.CHAT_WEB_SEARCH_ENABLED)
