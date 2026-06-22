"""Loader JSON — qualidade da síntese LLM vs template operacional."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "response_mode_synthesis_quality"


class ChatResponseModeSynthesisQualityContentService:
    @classmethod
    def deflection_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "deflectionMarkers"))

    @classmethod
    def generic_context_stopwords(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "genericContextStopwords")
            if str(item).strip()
        )

    @classmethod
    def limit_int(cls, *path: str, default: int = 0) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if node in (None, ""):
            return default

        try:
            return int(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def limit_float(cls, *path: str, default: float = 0.0) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if node in (None, ""):
            return default

        try:
            return float(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def mode_limit_int(cls, group: str, mode: str, default: int = 0) -> int:
        return cls.limit_int("limits", group, mode, default=default)

    @classmethod
    def mode_ladder_float(cls, key: str, default: float = 0.0) -> float:
        return cls.limit_float("modeLadder", key, default=default)

    @classmethod
    def mode_ladder_bool(cls, key: str, default: bool = False) -> bool:
        value = ChatAssistantContentService.get(_BUNDLE, "modeLadder", key, default=default)

        return bool(value)

    @classmethod
    def pipeline_modes_allowing_direct_response(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "pipeline", "allowDirectResponseModes")
            if str(item).strip()
        )

    @classmethod
    def pipeline_direct_response_effect(cls, mode: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "pipeline",
                "directResponseEffects",
                str(mode or "").strip().lower(),
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def mode_ladder_int(cls, key: str, default: int = 0) -> int:
        return cls.limit_int("modeLadder", key, default=default)

    @classmethod
    def mode_ladder_required_pairs(cls) -> tuple[tuple[str, str], ...]:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "modeLadder", "requiredPairs")

        if not isinstance(raw, list):
            return (("fast", "normal"), ("normal", "thinker"))

        pairs: list[tuple[str, str]] = []

        for item in raw:
            if not isinstance(item, list) or len(item) < 2:
                continue

            left = str(item[0] or "").strip().lower()
            right = str(item[1] or "").strip().lower()

            if left and right:
                pairs.append((left, right))

        return tuple(pairs) if pairs else (("fast", "normal"), ("normal", "thinker"))

    @classmethod
    def pipeline_expected_effect(cls, mode: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "pipeline",
                "expectedEffectsByMode",
                str(mode or "").strip().lower(),
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def pipeline_expected_prose_delivery_mode(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "pipeline",
                "expectedProseDeliveryMode",
                default="llm",
            )
            or "llm"
        ).strip()

    @classmethod
    def turn_finalization_modes(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(
                _BUNDLE,
                "turnFinalization",
                "coherenceFallbackModes",
            )
            if str(item).strip()
        )

    @classmethod
    def turn_finalization_prefer_commentary_before_enrich(cls) -> bool:
        value = ChatAssistantContentService.get(
            _BUNDLE,
            "turnFinalization",
            "preferCommentaryBeforeEnrich",
            default=True,
        )

        return bool(value)

    @classmethod
    def gap(cls, *path: str, default: str = "", **kwargs: Any) -> str:
        template = ChatAssistantContentService.get(_BUNDLE, "gaps", *path, default=default)

        if template in (None, ""):
            return default

        try:
            return str(template).format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return str(template)

    @classmethod
    def _coherence_checks_node(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "coherenceChecks")

        return node if isinstance(node, dict) else {}

    @classmethod
    def coherence_gap(cls, key: str, *, default: str = "") -> str:
        gaps = cls._coherence_checks_node().get("gaps")

        if not isinstance(gaps, dict):
            return default

        return str(gaps.get(key) or default).strip()

    @classmethod
    def coherence_limit_int(cls, key: str, *, default: int = 0) -> int:
        raw = cls._coherence_checks_node().get(key)

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    @lru_cache(maxsize=1)
    def sparse_list_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls._compile_pattern_list("sparseListPatterns")

    @classmethod
    @lru_cache(maxsize=1)
    def numbered_run_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls._compile_pattern_list("numberedRunPatterns")

    @classmethod
    @lru_cache(maxsize=1)
    def llm_boilerplate_section_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls._compile_pattern_list("llmBoilerplateSectionPatterns")

    @classmethod
    def ungrounded_group_claim_triggers(cls) -> tuple[str, ...]:
        raw = cls._coherence_checks_node().get("ungroundedGroupClaimTriggers")

        if not isinstance(raw, list):
            return ()

        return tuple(
            str(item).strip().lower()
            for item in raw
            if str(item or "").strip()
        )

    @classmethod
    def ungrounded_group_claim_min_token_length(cls) -> int:
        return cls.coherence_limit_int("ungroundedGroupClaimMinTokenLength", default=4)

    @classmethod
    def numbered_run_min_dots(cls) -> int:
        return max(2, cls.coherence_limit_int("numberedRunMinDots", default=3))

    @classmethod
    def _compile_pattern_list(cls, key: str) -> tuple[re.Pattern[str], ...]:
        raw = cls._coherence_checks_node().get(key)

        if not isinstance(raw, list):
            return ()

        patterns: list[re.Pattern[str]] = []

        for item in raw:
            pattern = str(item or "").strip()

            if not pattern:
                continue

            patterns.append(re.compile(pattern, re.IGNORECASE))

        return tuple(patterns)
