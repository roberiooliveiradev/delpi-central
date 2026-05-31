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
    def payload_for_catalog(
        cls,
        *,
        profile_id: str | None = None,
        agent_name: str | None = None,
        agent_category: str | None = None,
    ) -> dict[str, Any]:
        data = _content()
        welcome = data.get("welcome") if isinstance(data.get("welcome"), dict) else {}
        resolved_profile = cls.resolve_profile_id(
            profile_id=profile_id,
            agent_name=agent_name,
            agent_category=agent_category,
        )
        preset = cls.profile_preset(resolved_profile) if resolved_profile else None
        subtitle = str(welcome.get("subtitle") or "").strip()

        if preset:
            preset_subtitle = str(preset.get("subtitle") or "").strip()

            if preset_subtitle:
                subtitle = preset_subtitle

        return {
            "welcome": {
                "title": str(welcome.get("title") or "").strip(),
                "subtitle": subtitle,
            },
            "profiles": cls.list_profiles(),
            "selectedProfileId": resolved_profile,
            "starterCards": cls.starter_cards(profile_id=resolved_profile),
            "tourSteps": cls.tour_steps(),
            "idleHints": cls.idle_hints(),
        }

    @classmethod
    def list_profiles(cls) -> list[dict[str, str]]:
        profiles: list[dict[str, str]] = []

        for preset in cls._profile_presets_raw():
            profile_id = str(preset.get("id") or "").strip()
            label = str(preset.get("label") or "").strip()

            if not profile_id or not label:
                continue

            profiles.append(
                {
                    "id": profile_id,
                    "label": label,
                    "subtitle": str(preset.get("subtitle") or "").strip(),
                }
            )

        return profiles

    @classmethod
    def profile_preset(cls, profile_id: str | None) -> dict[str, Any] | None:
        token = str(profile_id or "").strip().lower()

        if not token:
            return None

        for preset in cls._profile_presets_raw():
            if str(preset.get("id") or "").strip().lower() == token:
                return dict(preset)

        return None

    @classmethod
    def resolve_profile_id(
        cls,
        *,
        profile_id: str | None = None,
        agent_name: str | None = None,
        agent_category: str | None = None,
    ) -> str | None:
        explicit = str(profile_id or "").strip().lower()

        if explicit and cls.profile_preset(explicit):
            return explicit

        inferred = cls.infer_profile_from_agent(
            agent_name=agent_name,
            agent_category=agent_category,
        )

        return inferred

    @classmethod
    def infer_profile_from_agent(
        cls,
        *,
        agent_name: str | None,
        agent_category: str | None = None,
    ) -> str | None:
        category = ChatMessageNormalizationService.normalize_for_matching(
            str(agent_category or "")
        )
        name = ChatMessageNormalizationService.normalize_for_matching(str(agent_name or ""))
        haystack = f"{category} {name}".strip()

        if not haystack:
            return None

        for preset in cls._profile_presets_raw():
            profile_id = str(preset.get("id") or "").strip()
            match = preset.get("match")

            if not profile_id or not isinstance(match, dict):
                continue

            categories = match.get("categories") or []

            for item in categories:
                token = ChatMessageNormalizationService.normalize_for_matching(str(item))

                if token and token in category:
                    return profile_id

            name_tokens = match.get("nameTokens") or []

            for item in name_tokens:
                token = ChatMessageNormalizationService.normalize_for_matching(str(item))

                if token and token in haystack:
                    return profile_id

        return None

    @classmethod
    def starter_cards(cls, *, profile_id: str | None = None) -> list[dict[str, str]]:
        preset = cls.profile_preset(profile_id)

        if preset:
            items = preset.get("cards") or []
        else:
            items = _content().get("starterCards") or []

        return cls._normalize_cards(items)

    @classmethod
    def _normalize_cards(cls, items: list[Any]) -> list[dict[str, str]]:
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
    def _profile_presets_raw(cls) -> list[dict[str, Any]]:
        items = _content().get("profilePresets") or []

        return [dict(item) for item in items if isinstance(item, dict)]

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
