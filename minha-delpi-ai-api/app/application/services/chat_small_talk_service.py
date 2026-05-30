from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_agent_personality_service import ChatAgentPersonalityService
from app.domain.services.chat_agent_profile_service import ChatAgentProfileService
from app.domain.services.chat_personality_content_service import (
    ChatPersonalityContentService,
)
from app.domain.services.chat_small_talk_pattern_service import ChatSmallTalkPatternService
from app.infrastructure.content.content_service import ContentService

_CLOSURE_CATEGORIES = frozenset({"closure", "thanks", "praise", "farewell", "ack"})


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
    def build_direct_answer(
        cls,
        *,
        message: str,
        workspace_context: dict,
        previous_messages: list | None = None,
    ) -> str | None:
        category = cls.classify(message)

        if not category:
            return None

        content = _small_talk_content()
        profile = ChatAgentProfileService.from_workspace(workspace_context)
        personality = ChatAgentPersonalityService.from_profile(profile)
        humor_level = ChatAgentPersonalityService.effective_humor_level(
            personality,
            risk_level=0,
        )
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

        answer = ChatAgentProfileService.format_template(template, profile)
        hint = cls._closure_follow_up_hint(previous_messages)

        if category in _CLOSURE_CATEGORIES and hint:
            answer = f"{answer}\n\n{hint}"

        return answer

    @classmethod
    def _closure_follow_up_hint(cls, previous_messages: list | None) -> str:
        if not previous_messages:
            return ""

        for item in reversed(previous_messages):
            role = str(getattr(item, "role", None) or (item or {}).get("role") or "").strip()

            if role != "assistant":
                continue

            metadata = getattr(item, "metadata", None)

            if metadata is None and isinstance(item, dict):
                metadata = item.get("metadata")

            if not isinstance(metadata, dict):
                continue

            suggestions = metadata.get("followUpSuggestions") or []

            if not isinstance(suggestions, list) or not suggestions:
                continue

            labels = [
                str(entry.get("label") or "").strip()
                for entry in suggestions
                if isinstance(entry, dict) and str(entry.get("label") or "").strip()
            ][:3]

            if not labels:
                continue

            joined = ", ".join(labels)
            return f"Se quiser continuar: {joined}."

        return ""
