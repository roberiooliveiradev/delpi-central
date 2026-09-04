"""Flags da inteligência conversacional — JSON como default, env como override.

Default declarativo em ``conversational_intelligence.json``; o ambiente pode
sobrescrever (``CHAT_TURN_UNDERSTANDING_SHADOW``, ``CHAT_TASK_PLANNER_ENABLED``)
via ``AppConfigPort`` — o domain nunca lê ``os.environ``.
"""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "conversational_intelligence"

TURN_UNDERSTANDING_SHADOW = "turnUnderstandingShadow"
TASK_PLANNER_ENABLED = "taskPlannerEnabled"


class ChatConversationalIntelligenceFlagService:
    BUNDLE = _BUNDLE

    @classmethod
    def is_enabled(cls, key: str) -> bool:
        override = cls._env_override(key)

        if override is not None:
            return override

        return cls.json_default(key)

    @classmethod
    def json_default(cls, key: str) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "featureFlags")

        if not isinstance(node, dict):
            return False

        return bool(node.get(key, False))

    @classmethod
    def turn_understanding_shadow_enabled(cls) -> bool:
        return cls.is_enabled(TURN_UNDERSTANDING_SHADOW)

    @classmethod
    def task_planner_enabled(cls) -> bool:
        return cls.is_enabled(TASK_PLANNER_ENABLED)

    @classmethod
    def _env_override(cls, key: str) -> bool | None:
        from app.domain.services.chat_domain_config_service import (
            ChatDomainConfigService,
        )

        try:
            return ChatDomainConfigService.conversational_intelligence_flag_override(key)
        except Exception:
            return None
