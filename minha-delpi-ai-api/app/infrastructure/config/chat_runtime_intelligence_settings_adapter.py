from __future__ import annotations

from typing import Any, Protocol

from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)
from app.infrastructure.config.settings import Settings


class _RuntimeSettingsReader(Protocol):
    def get_chat_intelligence_settings(self) -> dict | None:
        ...


class InfrastructureChatRuntimeIntelligenceSettingsAdapter(
    ChatRuntimeIntelligenceSettingsPort,
):
    def __init__(self, settings_repository: _RuntimeSettingsReader | None = None) -> None:
        self._settings_repository = settings_repository

    def web_search_enabled(self) -> bool:
        stored: dict[str, Any] = {}

        if self._settings_repository is not None:
            raw = self._settings_repository.get_chat_intelligence_settings()

            if isinstance(raw, dict):
                stored = raw

        return self._bool(stored.get("webSearchEnabled"), Settings.CHAT_WEB_SEARCH_ENABLED)

    @staticmethod
    def _bool(value: object | None, default: bool) -> bool:
        if value is None:
            return bool(default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}

        return bool(value)
