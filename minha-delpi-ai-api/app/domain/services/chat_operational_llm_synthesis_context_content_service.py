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
    def leak_markers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "leakMarkers")
            if str(item).strip()
        )

    @classmethod
    def prose_panel_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "prosePanelRule", default="")
            or ""
        ).strip()

    @classmethod
    def prose_composition_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "proseCompositionRule", default="")
            or ""
        ).strip()

    @classmethod
    def prose_composition_json_fallback(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "proseCompositionJsonFallback",
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def enrich_insight_composition_reminder(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "enrichInsightCompositionReminder",
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def prose_panel_kind_hint(cls, selected: str | None) -> str:
        kind = str(selected or "").strip().lower()

        if not kind:
            return ""

        mapping = ChatAssistantContentService.get_mapping(_BUNDLE, "prosePanelKindHints")
        return str(mapping.get(kind) or "").strip()

    @classmethod
    def field_humanization_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "fieldHumanizationRule", default="")
            or ""
        ).strip()

    @classmethod
    def factual_fidelity_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "factualFidelityRule", default="")
            or ""
        ).strip()

    @classmethod
    def multi_source_cross_rule(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "multiSourceCrossRule", default="")
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
    def dedupe_paragraph_key_chars(cls) -> int:
        return cls._answer_enrichment_int("dedupeParagraphKeyChars", 160)

    @classmethod
    def dedupe_paragraph_min_key_chars(cls) -> int:
        return cls._answer_enrichment_int("dedupeParagraphMinKeyChars", 40)

    @classmethod
    def dedupe_sentence_key_chars(cls) -> int:
        return cls._answer_enrichment_int("dedupeSentenceKeyChars", 160)

    @classmethod
    def dedupe_sentence_min_key_chars(cls) -> int:
        return cls._answer_enrichment_int("dedupeSentenceMinKeyChars", 48)

    @classmethod
    def _answer_enrichment_int(cls, key: str, default: int) -> int:
        raw = cls.answer_enrichment_node().get(key)

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return default

    @classmethod
    def max_normal_prose_chars(cls) -> int:
        return cls.limit_int("maxNormalProseChars", 520)

    @classmethod
    def max_thinker_prose_chars(cls) -> int:
        return cls.limit_int("maxThinkerProseChars", 2400)

    @classmethod
    def enrich_insight_facts_budget_node(
        cls,
        *,
        profile: str = "local",
    ) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "enrichInsightFactsBudget")

        if not isinstance(node, dict):
            return {}

        profile_node = node.get(str(profile or "local").strip().lower())

        return profile_node if isinstance(profile_node, dict) else {}

    @classmethod
    def enrich_insight_facts_budget(
        cls,
        mode: str,
        *,
        profile: str = "local",
    ) -> dict[str, int]:
        mode_key = str(mode or "normal").strip().lower() or "normal"
        profile_node = cls.enrich_insight_facts_budget_node(profile=profile)
        mode_node = profile_node.get(mode_key)

        if not isinstance(mode_node, dict):
            mode_node = profile_node.get("normal") if isinstance(profile_node.get("normal"), dict) else {}

        defaults = {
            "base": 1200,
            "perTool": 350,
            "maxToolsCounted": 3,
            "hardCap": 2800,
        }

        resolved: dict[str, int] = {}

        for key, default in defaults.items():
            raw = mode_node.get(key) if isinstance(mode_node, dict) else None

            try:
                resolved[key] = max(1, int(raw))
            except (TypeError, ValueError):
                resolved[key] = default

        return resolved

    @classmethod
    def resolve_enrich_insight_facts_max_chars(
        cls,
        mode: str,
        *,
        ok_tool_count: int,
        profile: str = "local",
    ) -> int:
        budget = cls.enrich_insight_facts_budget(mode, profile=profile)
        extra_tools = max(0, int(ok_tool_count) - 1)
        counted = min(extra_tools, budget["maxToolsCounted"])
        dynamic = budget["base"] + (budget["perTool"] * counted)

        return min(dynamic, budget["hardCap"])
