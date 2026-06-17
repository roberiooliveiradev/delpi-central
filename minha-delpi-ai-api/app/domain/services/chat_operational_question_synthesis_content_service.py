"""Templates de síntese operacional orientada à pergunta — operational_question_synthesis.json."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatOperationalQuestionSynthesisContentService:
    _BUNDLE = "operational_question_synthesis"

    @classmethod
    def format(cls, section: str, key: str, **values: str) -> str:
        return ChatAssistantContentService.format(
            cls._BUNDLE,
            section,
            key,
            **values,
        )
