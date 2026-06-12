from __future__ import annotations

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)
from app.infrastructure.config.chat_intelligence_runtime_reader import (
    read_resolved_chat_intelligence,
)


class InfrastructureChatRuntimeIntelligenceSettingsAdapter(
    ChatRuntimeIntelligenceSettingsPort,
):
    def __init__(
        self,
        settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
    ) -> None:
        self._settings_repository = settings_repository

    def web_search_enabled(self) -> bool:
        return read_resolved_chat_intelligence(self._settings_repository).web_search_enabled
