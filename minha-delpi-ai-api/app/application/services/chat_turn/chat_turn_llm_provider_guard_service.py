"""Rate limit adicional para providers LLM externos por turno."""

from __future__ import annotations

from uuid import UUID

from app.composition.rate_limit_composer import get_rate_limit_service
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.infrastructure.config.llm_text_config import is_openai_compatible_provider
from app.infrastructure.config.settings import Settings


class ChatTurnLlmProviderGuardService:
    @classmethod
    def enforce_turn_rate_limit(cls, *, user_id: UUID, provider: str) -> None:
        if not Settings.RATE_LIMIT_ENABLED:
            return

        if not is_openai_compatible_provider(provider):
            return

        message = ChatAssistantContentService.get(
            "error_handling",
            "rateLimit",
            "externalLlmExceeded",
            default="Rate limit exceeded for external LLM provider",
        )

        get_rate_limit_service().check(
            key=f"llm_text:{provider}:{user_id}",
            limit=Settings.RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW,
            window_seconds=Settings.RATE_LIMIT_WINDOW_SECONDS,
            message=message,
        )
