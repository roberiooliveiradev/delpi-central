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
        raw = cls._coherence_checks_node().get("sparseListPatterns")

        if not isinstance(raw, list):
            return ()

        patterns: list[re.Pattern[str]] = []

        for item in raw:
            pattern = str(item or "").strip()

            if not pattern:
                continue

            patterns.append(re.compile(pattern))

        return tuple(patterns)
