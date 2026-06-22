"""Loader JSON — qualidade da síntese LLM vs template operacional."""

from __future__ import annotations

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
        raw = ChatAssistantContentService.get(_BUNDLE, *path, default=str(default))

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def limit_float(cls, *path: str, default: float = 0.0) -> float:
        value = ChatAssistantContentService.get(_BUNDLE, *path, default=default)

        try:
            return float(value)
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
