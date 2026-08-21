"""Vocabulário PT de extração/classificação de termos — bundle ``term_extraction_vocabulary.json``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatTermExtractionVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "term_extraction_vocabulary"

    @classmethod
    @lru_cache(maxsize=1)
    def definition_patterns(cls) -> tuple[re.Pattern[str], ...]:
        node = cls.node("definitionPatterns") or []

        return tuple(
            re.compile(str(item), re.IGNORECASE)
            for item in node
            if str(item or "").strip()
        )
