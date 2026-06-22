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

    @classmethod
    def fast_commentary_direct_enabled(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "fastCommentaryDirect")

        if not isinstance(node, dict):
            return True

        return bool(node.get("enabled", True))

    @classmethod
    def fast_commentary_direct_min_chars(cls) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "fastCommentaryDirect")

        if not isinstance(node, dict):
            return 40

        try:
            return max(1, int(node.get("minAnswerChars", 40)))
        except (TypeError, ValueError):
            return 40

    @classmethod
    def normal_commentary_direct_enabled(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "normalCommentaryDirect")

        if not isinstance(node, dict):
            return False

        return bool(node.get("enabled", False))

    @classmethod
    def normal_commentary_direct_min_chars(cls) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "normalCommentaryDirect")

        if not isinstance(node, dict):
            return 48

        try:
            return max(1, int(node.get("minAnswerChars", 48)))
        except (TypeError, ValueError):
            return 48

    @classmethod
    def fast_llm_max_facts_chars(cls) -> int | None:
        node = ChatAssistantContentService.get_node(_BUNDLE, "fastLlmBudget")

        if not isinstance(node, dict):
            return None

        raw = node.get("maxFactsChars")

        if raw in (None, ""):
            return None

        try:
            return max(128, int(raw))
        except (TypeError, ValueError):
            return None

    @classmethod
    def fast_llm_skip_prose_panel_rules(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "fastLlmBudget")

        if not isinstance(node, dict):
            return False

        return bool(node.get("skipProsePanelRules"))

    @classmethod
    def normal_llm_max_facts_chars(cls) -> int | None:
        node = ChatAssistantContentService.get_node(_BUNDLE, "normalLlmBudget")

        if not isinstance(node, dict):
            return None

        raw = node.get("maxFactsChars")

        if raw in (None, ""):
            return None

        try:
            return max(128, int(raw))
        except (TypeError, ValueError):
            return None

    @classmethod
    def normal_llm_skip_prose_panel_rules(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "normalLlmBudget")

        if not isinstance(node, dict):
            return False

        return bool(node.get("skipProsePanelRules"))
