"""Vocabulário PT de pesquisa web — bundle ``web_search.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatWebSearchVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "web_search"
