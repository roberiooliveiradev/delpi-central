"""Vocabulário PT do resolvedor de contexto textual — bundle ``text_context_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatTextContextVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "text_context_vocabulary"
