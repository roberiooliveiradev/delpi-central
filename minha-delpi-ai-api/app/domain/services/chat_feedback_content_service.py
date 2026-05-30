"""Motivos estruturados de feedback (playbook)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_personality_content_service import ChatPersonalityContentService
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatFeedbackContentService:
    @classmethod
    def allowed_reason_ids(cls) -> set[str]:
        reasons = _playbook().get("feedbackReasons") or []
        allowed: set[str] = set()

        for item in reasons:
            if isinstance(item, dict):
                reason_id = str(item.get("id") or "").strip()

                if reason_id:
                    allowed.add(reason_id)

        return allowed

    @classmethod
    def normalize_reason(cls, value: object) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        allowed = cls.allowed_reason_ids()

        if allowed and normalized not in allowed:
            raise ValueError("invalid feedback reason")

        return normalized

    @classmethod
    def thanks_for_rating(cls, rating: int, *, seed: str = "") -> str | None:
        if rating == 1:
            thanks = (_playbook().get("feedbackThanks") or {}).get("up") or []

            if isinstance(thanks, list) and thanks:
                index_seed = seed or "feedback-up"
                import zlib

                index = zlib.adler32(index_seed.encode("utf-8")) % len(thanks)
                return str(thanks[index]).strip()

        if rating == -1:
            prompt = (_playbook().get("feedbackThanks") or {}).get("downPrompt")

            return str(prompt).strip() if prompt else None

        return None
