from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_agent_profile_service import ChatAgentProfileService
from app.domain.services.chat_personality_content_service import (
    ChatPersonalityContentService,
)
from app.domain.services.chat_small_talk_pattern_service import ChatSmallTalkPatternService
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _small_talk_content() -> dict:
    return ContentService.load_json("assistant/small_talk")


class ChatSmallTalkService:
    @classmethod
    def is_small_talk(cls, message: str) -> bool:
        return cls.classify(message) is not None

    @classmethod
    def classify(cls, message: str) -> str | None:
        return ChatSmallTalkPatternService.match_category(message)

    @classmethod
    def build_direct_answer(cls, *, message: str, workspace_context: dict) -> str | None:
        category = cls.classify(message)
        if not category:
            return None

        content = _small_talk_content()
        profile = ChatAgentProfileService.from_workspace(workspace_context)
        responses = content.get("responses") or {}

        scope = "agent" if profile.has_agent else "platform"
        variants = content.get("responseVariants") or {}
        template = ChatPersonalityContentService.pick_variant(
            variants,
            scope=scope,
            category=category,
            seed=message,
            fallback="",
        )

        if not template:
            template = str((responses.get(scope) or {}).get(category) or "").strip()

        if not template:
            template = str((responses.get("platform") or {}).get(category) or "").strip()

        if not template:
            return None

        return ChatAgentProfileService.format_template(template, profile)
