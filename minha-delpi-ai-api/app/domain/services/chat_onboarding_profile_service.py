"""Resolução de perfil de onboarding a partir de metadados do agente."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("onboarding")


class ChatOnboardingProfileService:
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

        for preset in cls._profile_presets():
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
    def _profile_presets(cls) -> list[dict[str, Any]]:
        presets = _content().get("profilePresets") or []

        return [item for item in presets if isinstance(item, dict)]
