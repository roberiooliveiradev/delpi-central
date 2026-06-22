"""Intenção de perguntas sobre o perfil do usuário autenticado."""

from __future__ import annotations

from app.domain.services.chat_user_profile_content_service import (
    ChatUserProfileContentService,
)


class ChatUserProfileIntentService:
    @classmethod
    def is_user_identity_question(cls, message: str | None) -> bool:
        normalized = str(message or "").lower().strip()

        if not normalized:
            return False

        return any(term in normalized for term in ChatUserProfileContentService.identity_terms())

    @classmethod
    def should_include_pii_in_llm_context(cls, message: str | None) -> bool:
        """Titular perguntando sobre si — PII entra no prompt mesmo com LGPD ativo."""
        return cls.is_user_identity_question(message)
