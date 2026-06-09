"""Vocabulário PT do fast path operacional — bundle ``operational_pipeline_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatOperationalPipelineVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "operational_pipeline_vocabulary"
