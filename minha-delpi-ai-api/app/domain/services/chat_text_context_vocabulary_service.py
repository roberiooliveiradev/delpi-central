"""Vocabulário PT do resolvedor de contexto textual — bundle ``text_context_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "text_context_vocabulary"


class ChatTextContextVocabularyService:
    @classmethod
    def terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, *path))

    @classmethod
    def text(cls, *path: str, default: str = "", **values: str) -> str:
        template = ChatAssistantContentService.get(_BUNDLE, *path, default=default)

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template
