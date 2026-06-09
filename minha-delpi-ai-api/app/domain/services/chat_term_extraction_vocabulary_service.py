"""Vocabulário PT de extração/classificação de termos — bundle ``term_extraction_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatTermExtractionVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "term_extraction_vocabulary"
