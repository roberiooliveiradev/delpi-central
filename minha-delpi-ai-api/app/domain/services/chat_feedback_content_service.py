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

    @classmethod
    def reason_label(cls, reason_id: str | None) -> str:
        if not reason_id:
            return "feedback negativo"

        reasons = _playbook().get("feedbackReasons") or []

        for item in reasons:
            if isinstance(item, dict) and str(item.get("id") or "") == reason_id:
                return str(item.get("label") or reason_id)

        return reason_id

    @classmethod
    def corrective_actions_for_reason(cls, reason: str | None) -> list[dict[str, str]]:
        if not reason:
            return cls._default_corrective_actions()

        playbook = _playbook()
        by_reason = playbook.get("feedbackCorrectiveActionsByReason") or {}
        specific = by_reason.get(reason) if isinstance(by_reason, dict) else None

        if isinstance(specific, list) and specific:
            return cls._normalize_corrective_actions(specific, reason)

        return cls._default_corrective_actions(reason)

    @classmethod
    def _default_corrective_actions(cls, reason: str | None = None) -> list[dict[str, str]]:
        playbook = _playbook()
        defaults = playbook.get("feedbackCorrectiveActions") or []
        reason_label = cls.reason_label(reason)

        return cls._normalize_corrective_actions(defaults, reason, reason_label=reason_label)

    @classmethod
    def _normalize_corrective_actions(
        cls,
        items: list,
        reason: str | None,
        *,
        reason_label: str | None = None,
    ) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        label = reason_label or cls.reason_label(reason)

        for item in items:
            if not isinstance(item, dict):
                continue

            action_id = str(item.get("id") or "").strip()
            action_label = str(item.get("label") or "").strip()
            query = str(item.get("query") or item.get("queryTemplate") or "").strip()
            action_type = str(item.get("action") or "send_query").strip()

            if not action_id or not action_label:
                continue

            if query:
                query = query.replace("{{reasonLabel}}", label).replace("{{reasonId}}", reason or "")

            payload: dict[str, str] = {
                "id": action_id,
                "label": action_label,
                "action": action_type,
            }

            if query:
                payload["query"] = query

            normalized.append(payload)

        return normalized[:4]
