from __future__ import annotations

from app.domain.ports.app_config_port import AppConfigPort
from app.infrastructure.config.settings import Settings


class InfrastructureAppConfigAdapter(AppConfigPort):
    def chat_external_action_direct_response_enabled(self) -> bool:
        return bool(Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED)

    def chat_direct_response_stream_chunk_chars(self) -> int:
        return int(Settings.CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS)

    def chat_direct_response_stream_delay_ms(self) -> int:
        return int(Settings.CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS)

    def chat_default_sql_authoring_skill_enabled(self) -> bool:
        return bool(Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL)

    def chat_document_vision_enabled(self) -> bool:
        return bool(Settings.CHAT_DOCUMENT_VISION_ENABLED)

    def chat_document_vision_auto_with_drawing(self) -> bool:
        return bool(Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING)
