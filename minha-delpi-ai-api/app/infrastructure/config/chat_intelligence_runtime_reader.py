from __future__ import annotations

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.domain.services.chat_intelligence_settings_resolver import (
    ChatIntelligenceSettingsSnapshot,
    resolve_chat_intelligence_settings,
)
from app.infrastructure.config.chat_intelligence_settings_defaults import (
    build_chat_intelligence_defaults_from_settings,
)


def read_resolved_chat_intelligence(
    settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
) -> ChatIntelligenceSettingsSnapshot:
    stored = None

    if settings_repository is not None:
        stored = settings_repository.get_chat_intelligence_settings()

    return resolve_chat_intelligence_settings(
        defaults=build_chat_intelligence_defaults_from_settings(),
        stored=stored,
    )
