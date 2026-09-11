"""E2.S5 — map Turn Understanding → generic router signals (no OpenAPI/path)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.turn_understanding import TurnUnderstanding


@dataclass(frozen=True)
class GenericIntentSignals:
    """Cheap TU-derived signals for intent_router overlay."""

    no_tool: bool | None = None
    presentation_view: str | None = None
    is_reasoning: bool = False


class TurnUnderstandingGenericIntentMapperService:
    """Derives no-tool / presentation / compare-explain signals from TU."""

    _PRESENTATION_VIEWS = frozenset({"table", "chart", "kpi"})
    _NO_TOOL_LEGACY_INTENTS = frozenset({"small_talk", "utility", "identity"})

    @classmethod
    def from_understanding(cls, contract: TurnUnderstanding | None) -> GenericIntentSignals:
        if contract is None:
            return GenericIntentSignals()

        presentation_view = None
        presentation = contract.presentation_intent
        if isinstance(presentation, dict):
            view = str(presentation.get("view") or "").strip().lower()
            if view in cls._PRESENTATION_VIEWS:
                presentation_view = view

        is_reasoning = any(
            str(goal.kind or "").strip().lower() == "reasoning" for goal in contract.goals
        )

        return GenericIntentSignals(
            no_tool=contract.needs_tool if contract.needs_tool is not None else None,
            presentation_view=presentation_view,
            is_reasoning=is_reasoning,
        )

    @classmethod
    def from_message(cls, message: str) -> GenericIntentSignals:
        from app.domain.services.chat_turn_understanding_service import (
            ChatTurnUnderstandingService,
        )

        return cls.from_understanding(ChatTurnUnderstandingService.analyze(message))
