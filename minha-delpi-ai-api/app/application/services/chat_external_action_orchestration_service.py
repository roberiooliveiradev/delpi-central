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
            ChatProductQueryIntent.SALES,
            ChatProductQueryIntent.SUMMARY,
            ChatProductQueryIntent.ANALYSER,
            ChatProductQueryIntent.DESCRIPTION,
            ChatProductQueryIntent.PARENTS,
            ChatProductQueryIntent.FULL,
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
        on_stream_activity=None,
    ) -> list[dict]:
        if not selection_service or not allowed_action_ids:
            return []

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return []

        def _return_planned(planned: list[dict]) -> list[dict]:
            if on_stream_activity and planned:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                ChatStreamActivityService.emit_planned_actions(
                    on_stream_activity,
                    planned,
                )

            return planned

        if not Settings.CHAT_MULTI_ACTION_ENABLED:
            selected = selection_service.select_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
            )

            return _return_planned([selected] if selected else [])

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.plan_step(
                        step=1,
                        total=1,
                        target="estruturas para comparação",
                        verb="Planejando",
                        detail="Buscando fichas/estruturas dos produtos citados.",
                    )
                )

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
                return _return_planned(planned)

        if ChatCanvasIntentService.blocks_external_action_selection(message):
            return []

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.application.services.external_actions.external_action_selection_service import (
            ExternalActionSelectionService,
        )

        if ExternalActionSelectionService._looks_like_sale_orders_list_question(
            normalized
        ):
            selected = selection_service.select_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
            )

            return _return_planned([selected] if selected else [])

        from app.domain.services.chat_operational_refinement_service import (
            ChatOperationalRefinementService,
        )
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        operational_follow_ups = ChatOperationalRefinementService.plan_operational_follow_ups(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if operational_follow_ups:
            limit = cls._resolve_max_calls(max_calls)
            planned: list[dict] = []

            for refinement in operational_follow_ups[:limit]:
                if refinement.kind in {"stock_refinement", "stock_reset"}:
                    selected = selection_service.select_action_for_product(
                        message,
                        product_code=str(refinement.product_code or ""),
                        allowed_action_ids=allowed_action_ids,
                        intent=ChatProductQueryIntent.STOCK,
                        previous_messages=previous_messages,
                    )
                elif refinement.kind in {"metric_refinement", "metric_reset"}:
                    selected = selection_service.select_action(
                        message,
                        allowed_action_ids=allowed_action_ids,
                        conversation_context=conversation_context,
                        previous_messages=previous_messages,
                    )
                elif refinement.kind == "pagination_refinement":
                    selected = selection_service.select_action(
                        message,
                        allowed_action_ids=allowed_action_ids,
                        conversation_context=conversation_context,
                        previous_messages=previous_messages,
                    )
                elif refinement.kind == "depth_refinement":
                    selected = selection_service.select_action(
                        message,
                        allowed_action_ids=allowed_action_ids,
                        conversation_context=conversation_context,
                        previous_messages=previous_messages,
                    )
                else:
                    selected = None

                if selected:
                    planned.append(selected)

            if planned:
                return _return_planned(planned)

        limit = cls._resolve_max_calls(max_calls)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            message,
            conversation_context,
            previous_messages=previous_messages,
        )
        intent = ChatProductQueryIntentService.resolve_product_intent(
            message,
            previous_messages=previous_messages,
        )
        route_segment = ChatRouteContextService.resolve_product_route_segment(
            message,
            previous_messages=previous_messages,
        )

        explicit_route_segment = ChatRouteContextService.segment_from_message(message)

        if intent == ChatProductQueryIntent.FULL:
            intent = cls._resolve_product_intent(message, normalized)

        recent_batch = ChatRouteContextService.collect_recent_product_route_batch(
            previous_messages,
            route_segment=None if explicit_route_segment else route_segment,
        )

        if (
            not codes
            and recent_batch
            and (
                ChatProductQueryIntentService.references_previous_product(message)
                or ChatRouteContextService.is_product_route_segment(route_segment)
                or ChatRouteContextService.is_product_route_segment(explicit_route_segment)
            )
        ):
            codes = list(recent_batch.product_codes)
            route_segment = route_segment or recent_batch.route_segment

            if not explicit_route_segment:
                inherited_intent = ChatRouteContextService.intent_for_product_segment(
                    recent_batch.route_segment
                )

                if inherited_intent:
                    intent = inherited_intent

        multi_product = len(codes) > 1 and (
            intent in cls._MULTI_PRODUCT_INTENTS
            or ChatRouteContextService.is_product_route_segment(route_segment)
        )

        if multi_product:
            planned: list[dict] = []

            for code in codes[:limit]:
                selected = selection_service.select_action_for_product(
                    message,
                    product_code=code,
                    allowed_action_ids=allowed_action_ids,
                    intent=intent,
                    route_segment=route_segment,
                )

                if selected:
                    planned.append(selected)

            if planned:
                return _return_planned(planned)

        selected = selection_service.select_action(
            message,
            allowed_action_ids=allowed_action_ids,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        return _return_planned([selected] if selected else [])

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

        if ChatProductQueryIntentService._looks_like_sales_question(normalized):
            return ChatProductQueryIntent.SALES

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return ChatProductQueryIntent.STOCK

        if ChatProductQueryIntentService._looks_like_parents_question(normalized):
            return ChatProductQueryIntent.PARENTS

        if ChatProductQueryIntentService._looks_like_description_question(normalized):
            return ChatProductQueryIntent.DESCRIPTION

        if ChatProductQueryIntentService._looks_like_full_analyser_question(normalized):
            return ChatProductQueryIntent.ANALYSER

        return intent
