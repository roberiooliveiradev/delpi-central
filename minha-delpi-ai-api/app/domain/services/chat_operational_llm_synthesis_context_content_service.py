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
    def factual_fidelity_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "factualFidelityRule", default="")
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

    @classmethod
    def skip_summary_answer_when_decoupled(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE)

        if not isinstance(node, dict):
            return True

        return bool(node.get("skipSummaryAnswerWhenDecoupled", True))

    @classmethod
    def skip_table_rows_when_decoupled(cls) -> bool:
        node = ChatAssistantContentService.get_node(_BUNDLE)

        if not isinstance(node, dict):
            return True

        return bool(node.get("skipTableRowsWhenDecoupled", True))

    @classmethod
    def answer_enrichment_node(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE)

        if not isinstance(node, dict):
            return {}

        enrichment = node.get("answerEnrichment")

        return enrichment if isinstance(enrichment, dict) else {}

    @classmethod
    def format_answer_enrichment(cls, key: str, **kwargs: Any) -> str:
        template = cls.answer_enrichment_node().get(key)

        if not template:
            return ""

        try:
            return str(template).format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return str(template)

    @classmethod
    def empty_section_signals(cls) -> list[str]:
        raw = cls.answer_enrichment_node().get("emptySectionSignals")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def contradiction_patterns(cls) -> list[str]:
        raw = cls.answer_enrichment_node().get("contradictionPatterns")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def hallucination_markers(cls) -> list[str]:
        raw = cls.answer_enrichment_node().get("hallucinationMarkers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def min_anchor_token_overlap(cls) -> int:
        raw = cls.answer_enrichment_node().get("minAnchorTokenOverlap")

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def min_ungrounded_sentence_chars(cls) -> int:
        raw = cls.answer_enrichment_node().get("minUngroundedSentenceChars")

        try:
            return max(16, int(raw))
        except (TypeError, ValueError):
            return 32

    @classmethod
    def max_normal_prose_chars(cls) -> int:
        return cls.limit_int("maxNormalProseChars", 520)

    @classmethod
    def max_thinker_prose_chars(cls) -> int:
        return cls.limit_int("maxThinkerProseChars", 960)
