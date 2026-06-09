"""Vocabulário PT de transformações na lousa — bundle ``canvas_transform_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatCanvasTransformVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "canvas_transform_vocabulary"

    @classmethod
    def kind_terms(cls, kind: str) -> tuple[str, ...]:
        return cls.terms("kindTerms", kind)

    @classmethod
    def kind_label(cls, kind: str, *, default: str = "") -> str:
        return cls.text("kindLabels", kind, default=default)

    @classmethod
    def template(cls, key: str, *, default: str = "") -> str:
        return cls.text("templates", key, default=default)
