"""Vocabulário PT de intervalos de data — bundle ``date_range_vocabulary.json``."""

from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatDateRangeVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "date_range_vocabulary"

    @classmethod
    @lru_cache(maxsize=1)
    def months_pt(cls) -> dict[str, int]:
        raw = cls.node("monthsPt")

        if not isinstance(raw, dict):
            return {}

        return {
            str(key): int(value)
            for key, value in raw.items()
            if str(key).strip() and value is not None
        }

    @classmethod
    @lru_cache(maxsize=1)
    def month_labels_pt(cls) -> dict[int, str]:
        raw = cls.node("monthLabelsPt")

        if not isinstance(raw, dict):
            return {}

        return {
            int(key): str(value)
            for key, value in raw.items()
            if str(value).strip()
        }

    @classmethod
    @lru_cache(maxsize=1)
    def week_offset_phrases(cls) -> dict[int, tuple[str, ...]]:
        raw = cls.node("weekOffsetPhrases")

        if not isinstance(raw, dict):
            return {}

        resolved: dict[int, tuple[str, ...]] = {}

        for key, value in raw.items():
            if not isinstance(value, list):
                continue

            resolved[int(key)] = tuple(str(item) for item in value if str(item).strip())

        return resolved

    @classmethod
    @lru_cache(maxsize=1)
    def weekdays_pt(cls) -> dict[str, int]:
        raw = cls.node("weekdaysPt")

        if not isinstance(raw, dict):
            return {}

        return {
            str(key): int(value)
            for key, value in raw.items()
            if str(key).strip() and value is not None
        }

    @classmethod
    @lru_cache(maxsize=1)
    def fixed_semester_phrases(cls) -> dict[int, tuple[str, ...]]:
        raw = cls.node("fixedSemesterPhrases")

        if not isinstance(raw, dict):
            return {}

        resolved: dict[int, tuple[str, ...]] = {}

        for key, value in raw.items():
            if not isinstance(value, list):
                continue

            resolved[int(key)] = tuple(str(item) for item in value if str(item).strip())

        return resolved

    @classmethod
    def temporal_range_markers(cls) -> tuple[str, ...]:
        return cls.terms("temporalRangeMarkers")
