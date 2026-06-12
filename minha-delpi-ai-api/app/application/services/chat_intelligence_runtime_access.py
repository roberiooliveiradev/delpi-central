from __future__ import annotations

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettings,
)


def resolve_chat_intelligence_runtime() -> ChatIntelligenceSettings:
    from app.composition.chat_composer import make_chat_intelligence_settings_service

    return make_chat_intelligence_settings_service().resolve()
