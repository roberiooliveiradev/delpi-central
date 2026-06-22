"""Vocabulário declarativo do perfil do usuário — bundle ``user_context``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "user_context"


class ChatUserProfileContentService:
    @classmethod
    def identity_terms(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "identityTerms")
            if str(item).strip()
        )

    @classmethod
    def prompt_context_header(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "promptContext",
                "header",
                default="[Dados do usuário que está conversando com você]",
            )
            or "[Dados do usuário que está conversando com você]"
        ).strip()

    @classmethod
    def prompt_context_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "promptContext", "rule", default="")
            or ""
        ).strip()

    @classmethod
    def llm_synthesis_user_message_lead(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "userMessageLead",
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def llm_synthesis_question_prefix(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "userMessageQuestionPrefix",
                default="Pergunta:",
            )
            or "Pergunta:"
        ).strip()
