"""Vocabulário PT de intenção de análise/comparação — bundle ``analysis_intent_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatAnalysisIntentVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "analysis_intent_vocabulary"
