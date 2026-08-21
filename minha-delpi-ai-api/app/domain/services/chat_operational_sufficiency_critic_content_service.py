"""Loader JSON `operational_sufficiency_critic` — planos pós-retrieve e reasons."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "operational_sufficiency_critic"


class ChatOperationalSufficiencyCriticContentService:
    @classmethod
    def settings(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "settings")

        return node if isinstance(node, dict) else {}

    @classmethod
    def llm_assist_enabled(cls) -> bool:
        return bool(cls.settings().get("llmAssistEnabled"))

    @classmethod
    def max_auto_follow_ups_default(cls) -> int:
        raw = cls.settings().get("maxAutoFollowUpsDefault")

        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return 1

    @classmethod
    def plans(cls) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "plans")

        if not isinstance(node, list):
            return []

        return [item for item in node if isinstance(item, dict) and str(item.get("id") or "").strip()]

    @classmethod
    def plan_ids(cls) -> list[str]:
        return [str(item.get("id") or "").strip() for item in cls.plans() if str(item.get("id") or "").strip()]

    @classmethod
    def plan_by_id(cls, plan_id: str) -> dict[str, Any]:
        key = str(plan_id or "").strip()

        if not key:
            return {}

        for item in cls.plans():
            if str(item.get("id") or "").strip() == key:
                return item

        return {}

    @classmethod
    def clarify_catalog(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "clarifyCatalog")

        return node if isinstance(node, dict) else {}

    @classmethod
    def clarify_keys(cls) -> list[str]:
        return [str(key).strip() for key in cls.clarify_catalog() if str(key).strip()]

    @classmethod
    def clarify_node(cls, clarify_key: str) -> dict[str, Any]:
        node = cls.clarify_catalog().get(str(clarify_key or "").strip())

        return node if isinstance(node, dict) else {}

    @classmethod
    def reason(cls, reason_key: str, **values: Any) -> str:
        key = str(reason_key or "").strip()

        if not key:
            return ""

        return ChatAssistantContentService.format(
            _BUNDLE,
            "reasons",
            key,
            default="",
            **values,
        ).strip()

    @classmethod
    def llm_assist_node(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "llmAssist")

        return node if isinstance(node, dict) else {}

    @classmethod
    def llm_system_prompt(cls) -> str:
        template = str(cls.llm_assist_node().get("systemTemplate") or "").strip()

        if not template:
            return ""

        return template.format(
            planIds=", ".join(cls.plan_ids()),
            clarifyKeys=", ".join(cls.clarify_keys()),
        )
