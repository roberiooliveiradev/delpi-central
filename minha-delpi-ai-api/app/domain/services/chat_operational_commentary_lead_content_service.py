"""Loader JSON — perfis de profundidade do lead de dataCommentary."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)

_DEFAULT_PROFILE: dict[str, Any] = {
    "highlightLimit": 2,
    "interpretationMaxChars": 0,
    "summaryLineLimit": 3,
    "attentionLimit": 3,
    "limitationsLimit": 0,
    "nextStepsLimit": 1,
    "includeNarrativeInsight": False,
    "includeSummaryWhenNoHighlights": True,
    "includeNextSteps": True,
}


class ChatOperationalCommentaryLeadContentService:
    @classmethod
    def depth_for_mode(cls, mode: str | None) -> str:
        normalized = str(mode or "").strip().lower()
        mapped = ChatResponseModeContentService.commentary_lead_depth_for_mode(normalized)

        if mapped:
            return mapped

        return cls.default_depth()

    @classmethod
    def default_depth(cls) -> str:
        return ChatResponseModeContentService.commentary_lead_default_depth()

    @classmethod
    def default_brief_depth(cls) -> str:
        return ChatResponseModeContentService.commentary_lead_depth_for_mode("fast") or "brief"

    @classmethod
    def brief_direct_tool_context_flag(cls) -> str:
        return ChatResponseModeContentService.commentary_brief_direct_tool_context_flag()

    @classmethod
    def synthesis_effect_for_depth(cls, depth: str) -> str:
        return ChatResponseModeContentService.commentary_lead_synthesis_effect(depth)

    @classmethod
    def profile(cls, depth: str) -> dict[str, Any]:
        resolved = str(depth or "").strip().lower() or cls.default_depth()
        node = ChatResponseModeContentService.commentary_lead_profile(resolved)

        if not isinstance(node, dict):
            return dict(_DEFAULT_PROFILE)

        merged = dict(_DEFAULT_PROFILE)
        merged.update(node)

        return {
            "highlightLimit": cls._profile_int(merged, "highlightLimit", 2),
            "interpretationMaxChars": cls._profile_int(merged, "interpretationMaxChars", 0),
            "summaryLineLimit": cls._profile_int(merged, "summaryLineLimit", 3),
            "attentionLimit": cls._profile_int(merged, "attentionLimit", 3),
            "limitationsLimit": cls._profile_int(merged, "limitationsLimit", 0),
            "nextStepsLimit": cls._profile_int(merged, "nextStepsLimit", 1),
            "includeNarrativeInsight": bool(merged.get("includeNarrativeInsight")),
            "includeSummaryWhenNoHighlights": bool(
                merged.get("includeSummaryWhenNoHighlights", True),
            ),
            "includeNextSteps": bool(merged.get("includeNextSteps", True)),
        }

    @classmethod
    def _profile_int(cls, node: dict[str, Any], key: str, default: int) -> int:
        raw = node.get(key)

        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return default
