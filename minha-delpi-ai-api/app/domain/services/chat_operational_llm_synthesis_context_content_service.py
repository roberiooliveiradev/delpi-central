"""Contexto compacto de fatos operacionais para síntese LLM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "operational_llm_synthesis_context"


class ChatOperationalLlmSynthesisContextContentService:
    @classmethod
    def title(cls) -> str:
        return ChatAssistantContentService.get(_BUNDLE, "title", default="Fatos consultados:")

    @classmethod
    def prose_panel_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "prosePanelRule", default="")
            or ""
        ).strip()

    @classmethod
    def max_chars(cls) -> int:
        raw = ChatAssistantContentService.get(_BUNDLE, "maxChars", default="1200")

        try:
            return int(raw)
        except (TypeError, ValueError):
            return 1200

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE)

        if isinstance(node, dict) and key in node:
            raw = node.get(key)

            try:
                return int(raw)
            except (TypeError, ValueError):
                return default

        raw = ChatAssistantContentService.get(_BUNDLE, key, default=str(default))

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def include_failed_tools(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE)

        if not isinstance(node, dict):
            return False

        return bool(node.get("includeFailedTools"))
