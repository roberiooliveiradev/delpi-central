from __future__ import annotations

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)
from app.domain.services.chat_intelligence_settings_resolver import (
    resolve_chat_intelligence_settings,
)
from app.infrastructure.config.chat_intelligence_settings_defaults import (
    build_chat_intelligence_defaults_from_settings,
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
        stored = None

        if self._settings_repository is not None:
            stored = self._settings_repository.get_chat_intelligence_settings()

        resolved = resolve_chat_intelligence_settings(
            defaults=build_chat_intelligence_defaults_from_settings(),
            stored=stored,
        )
        return resolved.web_search_enabled
