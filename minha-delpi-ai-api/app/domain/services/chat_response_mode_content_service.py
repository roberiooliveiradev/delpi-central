"""Catálogo JSON `response_modes` — rótulos, aliases e textos de efeito no pipeline."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "response_modes"


class ChatResponseModeContentService:
    @classmethod
    def mode_catalog(cls) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "modes")

        if not isinstance(node, list):
            return []

        return [item for item in node if isinstance(item, dict) and item.get("id")]

    @classmethod
    def alias_map(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "aliases")

        if not isinstance(node, dict):
            return {}

        return {str(key).strip().lower(): str(value).strip().lower() for key, value in node.items()}

    @classmethod
    def pipeline_effect_text(cls, effect: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "pipelineEffects",
            effect,
            default="",
        )
