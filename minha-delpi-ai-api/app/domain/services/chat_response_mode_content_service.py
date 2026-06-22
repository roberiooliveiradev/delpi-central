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

    @classmethod
    def thinker_llm_max_facts_chars(cls) -> int | None:
        node = ChatAssistantContentService.get_node(_BUNDLE, "thinkerLlmBudget")

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
    def thinker_llm_skip_prose_panel_rules(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE, "thinkerLlmBudget")

        if not isinstance(node, dict):
            return False

        return bool(node.get("skipProsePanelRules"))

    @classmethod
    def generation_limit_model(cls, mode: str, *, default: str) -> str:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "generationLimits",
            str(mode or "").strip().lower(),
        )

        if isinstance(node, dict):
            raw = str(node.get("model") or "").strip()

            if raw:
                return raw

        return default

    @classmethod
    def _node_int(cls, *path: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if node in (None, ""):
            return default

        try:
            return int(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _node_float(cls, *path: str, default: float) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if node in (None, ""):
            return default

        try:
            return float(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def generation_limit_int(cls, mode: str, field: str, *, default: int) -> int:
        return cls._node_int(
            "generationLimits",
            str(mode or "").strip().lower(),
            field,
            default=default,
        )

    @classmethod
    def generation_limit_float(cls, mode: str, field: str, *, default: float) -> float:
        return cls._node_float(
            "generationLimits",
            str(mode or "").strip().lower(),
            field,
            default=default,
        )

    @classmethod
    def latency_target_sec(cls, mode: str, *, default: int) -> int:
        value = cls._node_int(
            "latencyTargetsSec",
            str(mode or "").strip().lower(),
            default=default,
        )

        return max(1, value)

    @classmethod
    def quality_fallback_min_chars(cls) -> int:
        return cls._node_int("qualityFallbackMinChars", default=40)

    @classmethod
    def _commentary_lead_node(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "commentaryLead")

        return node if isinstance(node, dict) else {}

    @classmethod
    def commentary_lead_depth_for_mode(cls, mode: str) -> str:
        node = cls._commentary_lead_node().get("depthByMode")

        if not isinstance(node, dict):
            return ""

        return str(node.get(str(mode or "").strip().lower()) or "").strip().lower()

    @classmethod
    def commentary_lead_default_depth(cls) -> str:
        return str(cls._commentary_lead_node().get("defaultDepth") or "standard").strip().lower()

    @classmethod
    def commentary_brief_direct_tool_context_flag(cls) -> str:
        return str(
            cls._commentary_lead_node().get("briefDirectToolContextFlag") or "commentaryBriefDirect",
        ).strip()

    @classmethod
    def commentary_lead_synthesis_effect(cls, depth: str) -> str:
        node = cls._commentary_lead_node().get("synthesisEffectByDepth")

        if not isinstance(node, dict):
            return "llm_synthesis"

        resolved = str(depth or "").strip().lower()

        return str(node.get(resolved) or node.get("standard") or "llm_synthesis").strip()

    @classmethod
    def commentary_lead_profile(cls, depth: str) -> dict[str, Any]:
        node = cls._commentary_lead_node().get("profiles")

        if not isinstance(node, dict):
            return {}

        profile = node.get(str(depth or "").strip().lower())

        return profile if isinstance(profile, dict) else {}
