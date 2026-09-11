"""Fachada pública — roteamento de intenção do turno (Playbook 02)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.domain.services.chat_intent_router.chat_intent_router_classify_service import (
    ChatIntentRouterClassifyService,
)
from app.domain.services.chat_intent_router.chat_intent_router_executed_service import (
    ChatIntentRouterExecutedService,
)
from app.domain.services.chat_intent_router.chat_intent_router_heuristics_service import (
    ChatIntentRouterHeuristicsService,
)
from app.domain.services.chat_intent_router.chat_intent_router_models import IntentRouteResult
from app.domain.services.chat_intent_router.chat_intent_router_support_service import (
    ChatIntentRouterSupportService,
)

__all__ = ["ChatIntentRouterService", "IntentRouteResult"]

_NO_TOOL_LEGACY_INTENTS = frozenset({"small_talk", "utility", "identity"})
_ANALYSIS_SUB_INTENTS = frozenset({"analysis", "data_interpretation", "compound"})


class ChatIntentRouterService:
    """API estável: classify, resolve_executed, heurísticas expostas a consumidores legados."""

    _STAGE_INTENT = ChatIntentRouterSupportService.STAGE_INTENT

    @classmethod
    def classify(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        analysis_mode: bool = False,
        operational_optimize: bool = False,
        canvas_operational_update: bool = False,
    ) -> IntentRouteResult:
        legacy = ChatIntentRouterClassifyService.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            attachment_ids=attachment_ids,
            allowed_action_ids=allowed_action_ids,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            analysis_mode=analysis_mode,
            operational_optimize=operational_optimize,
            canvas_operational_update=canvas_operational_update,
        )
        return cls._overlay_turn_understanding_signals(message, legacy)

    @classmethod
    def _overlay_turn_understanding_signals(
        cls,
        message: str,
        legacy: IntentRouteResult,
    ) -> IntentRouteResult:
        from app.domain.services.chat_conversational_intelligence_flag_service import (
            ChatConversationalIntelligenceFlagService,
        )
        from app.domain.services.turn_understanding_generic_intent_mapper_service import (
            TurnUnderstandingGenericIntentMapperService,
        )

        dial_presentation = (
            ChatConversationalIntelligenceFlagService.presentation_family_cutover_enabled()
        )
        dial_no_tool = ChatConversationalIntelligenceFlagService.no_tool_family_cutover_enabled()
        dial_compare = (
            ChatConversationalIntelligenceFlagService.compare_explain_family_cutover_enabled()
        )
        if not (dial_presentation or dial_no_tool or dial_compare):
            return legacy

        signals = TurnUnderstandingGenericIntentMapperService.from_message(message)
        result = legacy
        flags = list(legacy.flags or ())

        # presentation — mapper-first when legado já é rota de apresentação/formato.
        if dial_presentation and signals.presentation_view:
            view = signals.presentation_view
            if legacy.intent == "presentation_task":
                result = replace(result, sub_intent=view)
                if "tu_presentation" not in flags:
                    flags.append("tu_presentation")
            elif legacy.sub_intent == "format_refinement":
                if "tu_presentation_agree" not in flags:
                    flags.append("tu_presentation_agree")
                if f"tu_view:{view}" not in flags:
                    flags.append(f"tu_view:{view}")
            elif legacy.intent == "text_task" and (
                str(legacy.sub_intent or "").startswith(("to_", "as_"))
                or legacy.sub_intent in {"table", "chart", "kpi"}
            ):
                result = replace(result, sub_intent=view)
                if "tu_presentation" not in flags:
                    flags.append("tu_presentation")

        # no_tool — agree-gated: só reforça quando legado já é small_talk/utility/identity.
        if dial_no_tool and signals.no_tool is False:
            if legacy.intent in _NO_TOOL_LEGACY_INTENTS:
                if "tu_no_tool_agree" not in flags:
                    flags.append("tu_no_tool_agree")
            # diverge (operacional vs needsTool=false): mantém legado — sem inventar small_talk.

        # compare/explain — agree-gated via kind=reasoning.
        if dial_compare and signals.is_reasoning:
            sub = str(legacy.sub_intent or "")
            if legacy.intent in {"analysis", "text_task"} or sub in _ANALYSIS_SUB_INTENTS:
                if "tu_compare_agree" not in flags:
                    flags.append("tu_compare_agree")
            # diverge: mantém legado.

        if flags != list(legacy.flags or ()):
            result = replace(result, flags=tuple(flags))
        return result

    @classmethod
    def resolve_executed(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        analysis_mode: bool = False,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        skip_rag: bool = False,
        direct_answer: str | None = None,
        tool_calls: list | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> IntentRouteResult:
        return ChatIntentRouterExecutedService.resolve_executed(
            message=message,
            pipeline_stages=pipeline_stages,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            skip_rag=skip_rag,
            direct_answer=direct_answer,
            tool_calls=tool_calls,
            attachment_ids=attachment_ids,
            allowed_action_ids=allowed_action_ids,
        )

    @classmethod
    def build_fallback_prompt(cls) -> str:
        return ChatIntentRouterSupportService.build_fallback_prompt()

    @staticmethod
    def _intent_router_terms(*path: str) -> tuple[str, ...]:
        return ChatIntentRouterHeuristicsService.intent_router_terms(*path)

    @staticmethod
    def _product_router_terms(*path: str) -> tuple[str, ...]:
        return ChatIntentRouterHeuristicsService.product_router_terms(*path)

    @staticmethod
    def _with_decision(
        route: IntentRouteResult,
        *,
        decision: str | None = None,
        reason: str | None = None,
    ) -> IntentRouteResult:
        return ChatIntentRouterSupportService.with_decision(
            route,
            decision=decision,
            reason=reason,
        )

    @staticmethod
    def _blocks_web_search(message: str) -> bool:
        return ChatIntentRouterHeuristicsService.blocks_web_search(message)

    @staticmethod
    def _presentation_sub_intent(message: str) -> str | None:
        return ChatIntentRouterHeuristicsService.presentation_sub_intent(message)

    @staticmethod
    def _looks_capabilities_question(message: str) -> bool:
        return ChatIntentRouterHeuristicsService.looks_capabilities_question(message)
