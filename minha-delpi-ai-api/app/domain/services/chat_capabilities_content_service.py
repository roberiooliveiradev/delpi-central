"""Vocabulário declarativo de capacidades — bundle ``capabilities``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "capabilities"


class ChatCapabilitiesContentService:
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
                default="O que você pode fazer aqui",
            )
            or "O que você pode fazer aqui"
        ).strip()

    @classmethod
    def llm_synthesis_compound_section_title(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "compoundSectionTitle",
                default="O que você pode fazer aqui",
            )
            or "O que você pode fazer aqui"
        ).strip()
