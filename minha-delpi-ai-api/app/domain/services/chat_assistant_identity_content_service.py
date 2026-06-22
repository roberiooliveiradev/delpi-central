"""Vocabulário declarativo de identidade do assistente — bundle ``identity``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "identity"


class ChatAssistantIdentityContentService:
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

    @classmethod
    def llm_synthesis_facts_section_title(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "factsSectionTitle",
                default="Sobre o assistente",
            )
            or "Sobre o assistente"
        ).strip()

    @classmethod
    def llm_synthesis_compound_section_title(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "compoundSectionTitle",
                default="Sobre o assistente",
            )
            or "Sobre o assistente"
        ).strip()
