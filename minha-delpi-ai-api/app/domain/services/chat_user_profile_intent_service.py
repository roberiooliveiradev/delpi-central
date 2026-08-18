"""Intenção de perguntas sobre o perfil do usuário autenticado."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
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
    def asks_about_assistant(cls, message: str | None) -> bool:
        """True quando a mensagem também pergunta o assistente (você/vc/agente)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")

        if not normalized:
            return False

        for term in ChatUserProfileContentService.assistant_subject_terms():
            token = ChatMessageNormalizationService.strip_accents(term)

            if not token:
                continue

            if " " in token:
                if token in normalized:
                    return True
                continue

            if re.search(rf"\b{re.escape(token)}\b", normalized):
                return True

        return False

    @classmethod
    def suppresses_capabilities_intent(cls, message: str | None) -> bool:
        """1ª pessoa de perfil/acesso sem sujeito do assistente → não é catálogo do chat."""
        return cls.is_user_identity_question(message) and not cls.asks_about_assistant(
            message
        )

    @classmethod
    def should_include_pii_in_llm_context(cls, message: str | None) -> bool:
        """Titular perguntando sobre si — PII entra no prompt mesmo com LGPD ativo."""
        return cls.is_user_identity_question(message)
