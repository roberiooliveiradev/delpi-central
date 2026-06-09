"""Vocabulário PT de sessão ativa — bundle ``session_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatSessionVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "session_vocabulary"
