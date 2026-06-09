"""Vocabulário PT de intenção de análise/comparação — bundle ``analysis_intent_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "analysis_intent_vocabulary"


class ChatAnalysisIntentVocabularyService:
    @classmethod
    def terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, *path))
