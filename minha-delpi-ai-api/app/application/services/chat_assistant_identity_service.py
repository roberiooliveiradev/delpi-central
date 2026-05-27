from __future__ import annotations

from functools import lru_cache

from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _identity_content() -> dict:
    return ContentService.load_json("assistant/identity")


class ChatAssistantIdentityService:
    """Respostas diretas (sem LLM) sobre quem é o assistente/agente e como usá-lo."""

    @classmethod
    def is_assistant_identity_question(cls, message: str) -> bool:
        return cls.classify(message) is not None

    @classmethod
    def classify(cls, message: str) -> str | None:
        if ChatUserContextService.is_user_identity_question(message):
            return None

        content = _identity_content()
        max_length = int(content.get("maxMessageLength") or 220)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return None

        exclusions = tuple(
            str(item) for item in (content.get("userIdentityExclusions") or ())
        )
        if ChatMessageNormalizationService.contains_any(message, exclusions):
            return None

        patterns = content.get("patterns") or {}
        priority = tuple(
            str(item)
            for item in (
                content.get("categoryPriority")
                or ("who", "limits", "origin", "usage", "role", "what")
            )
        )

        for category in priority:
            terms = tuple(str(item) for item in (patterns.get(category) or ()))
            if terms and ChatMessageNormalizationService.contains_any(message, terms):
                return category

        return None

    @classmethod
    def build_direct_answer(cls, *, message: str, workspace_context: dict) -> str | None:
        category = cls.classify(message)
        if not category:
            return None

        content = _identity_content()
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

        platform_name = str(content.get("platformName") or "Minha DELPI")

        return template.format(
            platform_name=platform_name,
            agent_name=agent_name,
            agent_description=agent_description,
        )
