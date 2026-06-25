"""Fachada pública — roteamento de intenção do turno (Playbook 02)."""

from __future__ import annotations

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
        return ChatIntentRouterClassifyService.classify(
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
