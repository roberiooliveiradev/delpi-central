"""Detecção de small talk a partir de `small_talk.json` (fonte única de padrões)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _small_talk_content() -> dict:
    return ContentService.load_json("assistant/small_talk")


class ChatSmallTalkPatternService:
    @classmethod
    def is_small_talk(cls, message: str) -> bool:
        return cls.match_category(message) is not None

    @classmethod
    def match_category(cls, message: str) -> str | None:
        text = str(message or "").strip()

        if not text:
            return None

        content = _small_talk_content()
        max_length = int(content.get("maxMessageLength") or 48)

        if len(text) > max_length:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(text) or ""
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        exclusions = tuple(str(item) for item in (content.get("exclusions") or ()))

        if ChatMessageNormalizationService.contains_any(normalized, exclusions):
            return None

        patterns = content.get("patterns") or {}
        priority = content.get("categoryPriority") or list(patterns.keys())
        exact_categories = set(content.get("exactMatchCategories") or ("ack",))

        for category in priority:
            category_patterns = [
                str(pattern)
                for pattern in (patterns.get(category) or ())
                if str(pattern).strip()
            ]
            category_patterns.sort(
                key=lambda pattern: len(
                    ChatMessageNormalizationService.normalize_for_matching(pattern) or pattern
                ),
                reverse=True,
            )

            for pattern in category_patterns:
                candidate = ChatMessageNormalizationService.normalize_for_matching(pattern) or pattern
                candidate = " ".join(candidate.split())

                if not candidate:
                    continue

                if cls._matches(
                    normalized,
                    candidate,
                    exact_only=str(category) in exact_categories,
                ):
                    return str(category)

        return None

    @classmethod
    def _matches(cls, normalized: str, candidate: str, *, exact_only: bool) -> bool:
        if normalized == candidate:
            return True

        trailing = re.sub(r"[\s!?.,:;]+$", "", normalized)

        if trailing == candidate:
            return True

        if exact_only:
            return False

        if normalized.startswith(f"{candidate} "):
            return True

        return normalized.startswith(f"{candidate},")
