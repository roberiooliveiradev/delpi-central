from __future__ import annotations

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.infrastructure.config.settings import Settings


class ChatExternalActionOrchestrationService:
    """Planeja uma ou mais consultas OpenAPI (actions) para a mesma pergunta."""

    _MULTI_PRODUCT_INTENTS = frozenset(
        {
            ChatProductQueryIntent.STRUCTURE,
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.DESCRIPTION,
            ChatProductQueryIntent.PARENTS,
        }
    )

    @classmethod
    def plan_actions(
        cls,
        selection_service,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        max_calls: int | None = None,
    ) -> list[dict]:
        if not selection_service or not allowed_action_ids:
            return []

        if not Settings.CHAT_MULTI_ACTION_ENABLED:
            selected = selection_service.select_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
            )
            return [selected] if selected else []

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            from app.application.services.chat_structure_comparison_orchestration_service import (
                ChatStructureComparisonOrchestrationService,
            )

            planned = ChatStructureComparisonOrchestrationService.plan_structure_fetches(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                max_calls=max_calls,
            )

            if planned:
                return planned

        if ChatCanvasIntentService.is_canvas_placement_request(message):
            return []

        limit = cls._resolve_max_calls(max_calls)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            message,
            conversation_context,
        )
        intent = cls._resolve_product_intent(message, normalized)

        if len(codes) > 1 and intent in cls._MULTI_PRODUCT_INTENTS:
            planned: list[dict] = []

            for code in codes[:limit]:
                selected = selection_service.select_action_for_product(
                    message,
                    product_code=code,
                    allowed_action_ids=allowed_action_ids,
                    intent=intent,
                )

                if selected:
                    planned.append(selected)

            if planned:
                return planned

        selected = selection_service.select_action(
            message,
            allowed_action_ids=allowed_action_ids,
            conversation_context=conversation_context,
        )

        return [selected] if selected else []

    @classmethod
    def _resolve_max_calls(cls, max_calls: int | None) -> int:
        if max_calls is not None:
            return max(1, min(int(max_calls), 8))

        return max(1, min(Settings.CHAT_MULTI_ACTION_MAX_CALLS, 8))

    @classmethod
    def _resolve_product_intent(cls, message: str, normalized: str) -> str:
        intent = ChatProductQueryIntentService.detect(message)

        if intent != ChatProductQueryIntent.FULL:
            return intent

        if ChatProductQueryIntentService._looks_like_structure_question(normalized):
            return ChatProductQueryIntent.STRUCTURE

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return ChatProductQueryIntent.STOCK

        if ChatProductQueryIntentService._looks_like_parents_question(normalized):
            return ChatProductQueryIntent.PARENTS

        if ChatProductQueryIntentService._looks_like_description_question(normalized):
            return ChatProductQueryIntent.DESCRIPTION

        return intent
