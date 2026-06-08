"""Flags de inteligência com override admin — via ChatRuntimeIntelligenceSettingsPort."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.chat_runtime_intelligence_settings_port import (
    ChatRuntimeIntelligenceSettingsPort,
)


class ChatRuntimeIntelligenceSettingsService:
    _port: ClassVar[ChatRuntimeIntelligenceSettingsPort | None] = None

    @classmethod
    def configure(cls, port: ChatRuntimeIntelligenceSettingsPort) -> None:
        cls._port = port

    @classmethod
    def _require_port(cls) -> ChatRuntimeIntelligenceSettingsPort:
        if cls._port is None:
            raise RuntimeError(
                "ChatRuntimeIntelligenceSettingsPort não configurado — "
                "chame configure_domain_infrastructure_ports()"
            )

        return cls._port

    @classmethod
    def web_search_enabled(cls) -> bool:
        return cls._require_port().web_search_enabled()
