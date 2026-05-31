"""Onboarding e modo treinamento (Playbook 10)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/onboarding")


class ChatOnboardingService:
    @classmethod
    def payload_for_catalog(cls) -> dict[str, Any]:
        data = _content()
        welcome = data.get("welcome") if isinstance(data.get("welcome"), dict) else {}

        return {
            "welcome": {
                "title": str(welcome.get("title") or "").strip(),
                "subtitle": str(welcome.get("subtitle") or "").strip(),
            },
            "starterCards": cls.starter_cards(),
            "tourSteps": cls.tour_steps(),
            "idleHints": cls.idle_hints(),
        }

    @classmethod
    def starter_cards(cls) -> list[dict[str, str]]:
        items = _content().get("starterCards") or []
        cards: list[dict[str, str]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()

            if not label or not query:
                continue

            cards.append(
                {
                    "id": str(item.get("id") or label).strip(),
                    "label": label,
                    "description": str(item.get("description") or "").strip(),
                    "query": query,
                }
            )

        return cards

    @classmethod
    def tour_steps(cls) -> list[dict[str, str]]:
        items = _content().get("tourSteps") or []
        steps: list[dict[str, str]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "").strip()
            body = str(item.get("body") or "").strip()

            if not title:
                continue

            steps.append(
                {
                    "id": str(item.get("id") or title).strip(),
                    "title": title,
                    "body": body,
                }
            )

        return steps

    @classmethod
    def idle_hints(cls) -> list[str]:
        hints = _content().get("idleHints") or []

        return [str(item).strip() for item in hints if str(item).strip()]

    @classmethod
    def is_training_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        detection = _content().get("trainingDetection") or {}
        max_length = int(detection.get("maxLength") or 80)

        if not normalized or len(normalized) > max_length:
            return False

        phrases = tuple(str(item) for item in (detection.get("phrases") or ()))

        for phrase in phrases:
            token = ChatMessageNormalizationService.normalize_for_matching(phrase)

            if token and (normalized == token or token in normalized):
                return True

        return False

    @classmethod
    def build_training_answer(cls) -> str:
        block = _content().get("trainingAnswer") or {}
        title = str(block.get("title") or "**Guia rápido**").strip()
        sections = block.get("sections") or []
        footer = str(block.get("footer") or "").strip()
        lines = [title, ""]

        for section in sections:
            if not isinstance(section, dict):
                continue

            heading = str(section.get("heading") or "").strip()
            bullets = section.get("bullets") or []

            if heading:
                lines.append(f"### {heading}")

            for bullet in bullets:
                text = str(bullet).strip()

                if text:
                    lines.append(f"- {text}")

            lines.append("")

        if footer:
            lines.append(footer)

        return "\n".join(lines).strip()

    @classmethod
    def resolve_direct_answer(cls, *, message: str) -> str | None:
        if not cls.is_training_request(message):
            return None

        return cls.build_training_answer()

    @classmethod
    def training_follow_up_suggestions(cls) -> list[dict[str, str]]:
        items = _content().get("trainingFollowUpChips") or []
        suggestions: list[dict[str, str]] = []

        for item in items:
            if isinstance(item, dict):
                label = str(item.get("label") or "").strip()
                query = str(item.get("query") or label).strip()
            else:
                label = str(item).strip()
                query = label

            if label and query:
                suggestions.append({"label": label, "query": query})

        return suggestions[:6]
