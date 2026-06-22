"""Montagem canônica do lead a partir de dataCommentary — perfis declarativos por profundidade."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_operational_commentary_lead_content_service import (
    ChatOperationalCommentaryLeadContentService,
)


class ChatOperationalCommentaryLeadService:
    @classmethod
    def format_lead(
        cls,
        commentary: dict[str, Any] | None,
        *,
        compact: bool = False,
        depth: str | None = None,
    ) -> str:
        if not isinstance(commentary, dict):
            return ""

        resolved_depth = cls._resolve_depth(depth=depth, compact=compact)
        profile = ChatOperationalCommentaryLeadContentService.profile(resolved_depth)
        parts: list[str] = []

        highlights = cls._collect_highlights(commentary)
        interpretation = str(commentary.get("interpretation") or "").strip()
        narrative_insight = str(commentary.get("narrativeInsight") or "").strip()
        next_action = str(commentary.get("nextAction") or "").strip()

        highlight_limit = profile["highlightLimit"]

        if highlights:
            parts.append("\n\n".join(highlights[:highlight_limit]))
        elif interpretation:
            max_chars = profile["interpretationMaxChars"]
            parts.append(
                interpretation[:max_chars] if max_chars > 0 else interpretation,
            )
        elif profile["includeSummaryWhenNoHighlights"]:
            summary = cls._resolve_summary(commentary, profile["summaryLineLimit"])

            if summary:
                parts.append(summary)

        if narrative_insight and profile["includeNarrativeInsight"]:
            parts.append(narrative_insight)

        attention = cls._collect_attention(commentary)
        attention_limit = profile["attentionLimit"]

        if attention and attention_limit:
            header = cls._narrative_header("attentionHeader", "**Pontos de atenção**")
            bullets = "\n".join(f"- {item}" for item in attention[:attention_limit])
            parts.append(f"{header}\n\n{bullets}")

        limitations = cls._collect_limitations(commentary)
        limitations_limit = profile["limitationsLimit"]

        if limitations and limitations_limit:
            header = cls._narrative_header("limitationsHeader", "**Limitações**")
            bullets = "\n".join(f"- {item}" for item in limitations[:limitations_limit])
            parts.append(f"{header}\n\n{bullets}")

        if next_action and profile["includeNextSteps"]:
            next_header = cls._narrative_header("nextStepsHeader", "**Próximos passos**")
            limit = profile["nextStepsLimit"]
            steps = [step.strip() for step in next_action.split("\n") if step.strip()]
            bullets = "\n".join(f"- {step}" for step in steps[:limit])
            parts.append(f"{next_header}\n\n{bullets}")

        return "\n\n".join(parts).strip()

    @classmethod
    def _resolve_depth(cls, *, depth: str | None, compact: bool) -> str:
        if depth:
            return str(depth).strip().lower()

        if compact:
            return ChatOperationalCommentaryLeadContentService.default_brief_depth()

        return ChatOperationalCommentaryLeadContentService.default_depth()

    @classmethod
    def _collect_highlights(cls, commentary: dict[str, Any]) -> list[str]:
        return [
            str(item.get("text") if isinstance(item, dict) else item or "").strip()
            for item in (commentary.get("highlights") or [])
            if str(item.get("text") if isinstance(item, dict) else item or "").strip()
        ]

    @classmethod
    def _collect_attention(cls, commentary: dict[str, Any]) -> list[str]:
        return [
            str(item).strip()
            for item in (commentary.get("attention") or [])
            if str(item or "").strip()
        ]

    @classmethod
    def _collect_limitations(cls, commentary: dict[str, Any]) -> list[str]:
        return [
            str(item).strip()
            for item in (commentary.get("limitations") or [])
            if str(item or "").strip()
        ]

    @classmethod
    def _resolve_summary(cls, commentary: dict[str, Any], line_limit: int) -> str:
        summary = str(commentary.get("summary") or "").strip()

        if summary:
            return summary

        summary_lines = [
            str(line).strip()
            for line in (commentary.get("summaryLines") or [])
            if str(line or "").strip()
        ]

        if not summary_lines:
            return ""

        return "\n\n".join(summary_lines[:line_limit])

    @classmethod
    def _narrative_header(cls, key: str, fallback: str) -> str:
        return str(
            ChatAssistantContentService.get(
                "presenter_content",
                "humanizedNarrative",
                key,
                default=fallback,
            )
            or fallback
        ).strip()
