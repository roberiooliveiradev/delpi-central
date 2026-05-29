from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
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
        if not ChatFastPathService.is_small_talk(message):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        content = _small_talk_content()
        patterns = content.get("patterns") or {}
        priority = content.get("categoryPriority") or list(patterns.keys())

        for category in priority:
            for pattern in patterns.get(category) or ():
                candidate = ChatMessageNormalizationService.normalize_for_matching(
                    str(pattern)
                ) or str(pattern)
                candidate = " ".join(candidate.split())

                if not candidate:
                    continue

                if normalized == candidate:
                    return str(category)

                if normalized.startswith(f"{candidate} ") or normalized.startswith(
                    f"{candidate},"
                ):
                    return str(category)

        return "greeting"

    @classmethod
    def build_direct_answer(cls, *, message: str, workspace_context: dict) -> str | None:
        category = cls.classify(message)
        if not category:
            return None

        content = _small_talk_content()
        responses = content.get("responses") or {}
        agent = workspace_context.get("agent") or {}
        agent_name = str(agent.get("name") or workspace_context.get("agentKey") or "").strip()
        has_agent = bool(agent_name)

        scope = "agent" if has_agent else "platform"
        template = str((responses.get(scope) or {}).get(category) or "").strip()

        if not template:
            template = str((responses.get("platform") or {}).get(category) or "").strip()

        if not template:
            return None

        placeholders = content.get("placeholders") or {}
        agent_description = str(agent.get("description") or "").strip()

        if not agent_description:
            agent_description = str(
                placeholders.get("agentDescriptionFallback")
                or "assistente especializado configurado para este tema."
            )

        return template.format(
            agent_name=agent_name,
            agent_description=agent_description,
        )
