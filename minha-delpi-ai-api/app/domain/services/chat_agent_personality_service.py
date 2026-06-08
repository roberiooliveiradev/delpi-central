"""Personalidade por agente (metadata.personality) — Fase 4 do playbook."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.domain.services.chat_agent_profile_service import ChatAgentProfile
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ChatAssistantContentService.load_personality_playbook()


@dataclass(frozen=True)
class ChatAgentPersonality:
    tone: str
    humor_level: int
    emoji_level: int
    proactivity: bool
    suggest_follow_ups: bool

    @property
    def allows_humor(self) -> bool:
        return self.humor_level > 0


class ChatAgentPersonalityService:
    @classmethod
    def from_profile(cls, profile: ChatAgentProfile) -> ChatAgentPersonality:
        defaults = _playbook().get("defaultPersonality") or {}
        raw = profile.metadata.get("personality")

        if not isinstance(raw, dict):
            raw = {}

        tone = str(raw.get("tone") or defaults.get("tone") or "").strip()
        humor_level = cls._clamp_int(
            raw.get("humorLevel", defaults.get("humorLevel")),
            minimum=0,
            maximum=3,
            fallback=2,
        )
        emoji_level = cls._clamp_int(
            raw.get("emojiLevel", defaults.get("emojiLevel")),
            minimum=0,
            maximum=2,
            fallback=0,
        )
        proactivity = cls._as_bool(
            raw.get("proactivity", defaults.get("proactivity")),
            default=True,
        )
        suggest_follow_ups = cls._as_bool(
            raw.get("suggestFollowUps", defaults.get("suggestFollowUps")),
            default=True,
        )

        if not tone:
            persona = (_playbook().get("persona") or {})
            tone = str(persona.get("tone") or "amigável, direto e corporativo")

        return ChatAgentPersonality(
            tone=tone,
            humor_level=humor_level,
            emoji_level=emoji_level,
            proactivity=proactivity,
            suggest_follow_ups=suggest_follow_ups,
        )

    @classmethod
    def effective_humor_level(
        cls,
        personality: ChatAgentPersonality,
        *,
        risk_level: int = 0,
    ) -> int:
        if risk_level >= 2:
            return 0

        if risk_level == 1:
            return min(personality.humor_level, 1)

        return personality.humor_level

    @staticmethod
    def _clamp_int(
        value: object,
        *,
        minimum: int,
        maximum: int,
        fallback: int,
    ) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return fallback

        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _as_bool(value: object, *, default: bool) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"true", "1", "yes", "sim"}:
                return True

            if normalized in {"false", "0", "no", "nao", "não"}:
                return False

        return default
