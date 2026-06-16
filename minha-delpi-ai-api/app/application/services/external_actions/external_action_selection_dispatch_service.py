"""Despacho por intent em external_action_selection — Fase 3B lote 23."""

from __future__ import annotations

from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.application.services.external_actions.external_action_domain_route_selection_service import (
    ExternalActionDomainRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_heuristics_service import (
    ExternalActionSelectionHeuristicsService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_route_context_service import ChatRouteContextService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


_INTENT_BOUND_PRODUCT_INTENTS = frozenset(
    {
        ChatProductQueryIntent.PARENTS,
        ChatProductQueryIntent.STRUCTURE,
        ChatProductQueryIntent.STOCK,
        ChatProductQueryIntent.SALES,
        ChatProductQueryIntent.SUMMARY,
        ChatProductQueryIntent.ANALYSER,
        ChatProductQueryIntent.DESCRIPTION,
    }
)


class ExternalActionSelectionDispatchService:
    def __init__(
        self,
        route_selection: ExternalActionRouteSelectionService,
        support: ExternalActionSelectionSupportService,
    ) -> None:
        self._route_selection = route_selection
        self._support = support

    def dispatch(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        raw_message: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        sql_source = str(raw_message or message).strip()

        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ) and ChatConversationContextService.has_recent_tool_data(previous_messages):
            return None

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            if not ChatProductionOperationalIntentService.matches_rest_route(message):
                return None

        if ChatCanvasIntentService.blocks_external_action_selection(message):
            return None

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return None

        if ChatSqlIntentService.is_authoring_request(message):
            normalized = ChatMessageNormalizationService.normalize_for_matching(message)

            if ExternalActionDomainRouteSelectionService.looks_like_system_metadata_question(
                normalized
            ):
                selected = self._route_selection.select_system_metadata(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    candidates_loader=self._list_allowed_candidates,
                )

                if selected:
                    return selected

            return None

        from app.domain.services.chat_web_search_source_follow_up_service import (
            ChatWebSearchSourceFollowUpService,
        )

        if ChatWebSearchSourceFollowUpService.blocks_external_action_selection(
            message,
            previous_messages,
        ):
            return None

        if (
            ChatSqlOperationalIntentService.requires_production_sql_knowledge(message)
            and not ChatSqlIntentService.is_authoring_request(message)
        ):
            from app.domain.services.chat_production_operational_intent_service import (
                ChatProductionOperationalIntentService,
            )

            if not ChatProductionOperationalIntentService.matches_rest_route(message):
                from app.domain.services.chat_sql_production_query_service import (
                    ChatSqlProductionQueryService,
                )

                production_resolution = ChatSqlProductionQueryService.resolve(message)

                if production_resolution and production_resolution.mode == "execute":
                    selected = self._select_sql_or_data_action(
                        message,
                        allowed_action_ids=allowed_action_ids,
                        sql=production_resolution.sql,
                        selection_reason_key="productionSqlFastPath",
                        raw_message=sql_source,
                    )

                    if selected:
                        return selected

        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        sql_refinement = ChatSqlQueryRefinementService.resolve(
            message,
            previous_messages=previous_messages,
        )

        if sql_refinement and sql_refinement.mode == "show_sql":
            return None

        if sql_refinement and sql_refinement.mode == "execute":
            selected = self._select_sql_or_data_action(
                message,
                allowed_action_ids=allowed_action_ids,
                sql=sql_refinement.sql,
                selection_reason_key="sqlRefinement",
                raw_message=sql_source,
            )

            if selected:
                selected["reason"] = ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "sqlRefinement",
                )
                return selected

        from app.domain.services.chat_drawing_intent_service import (
            ChatDrawingIntentService,
        )

        if ChatDrawingIntentService.is_drawing_analysis_request(message):
            product_code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
            )

            if product_code:
                selected = self._select_product_action(
                    message,
                    product_code,
                    allowed_action_ids=allowed_action_ids,
                    intent=ChatProductQueryIntent.ANALYSER,
                )

                if selected:
                    return selected

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            from app.domain.services.chat_sql_inventory_query_service import (
                ChatSqlInventoryQueryService,
            )

            if not ChatSqlIntentService.is_authoring_request(message):
                for resolver, reason_key in (
                    (ChatSqlInventoryQueryService, "inventorySqlFastPath"),
                ):
                    resolution = resolver.resolve(message)

                    if resolution and resolution.mode == "execute":
                        selected = self._select_sql_or_data_action(
                            message,
                            allowed_action_ids=allowed_action_ids,
                            sql=resolution.sql,
                            selection_reason_key=reason_key,
                            raw_message=sql_source,
                        )

                        if selected:
                            return selected

            if ChatSqlIntentService.should_auto_execute_sql(message):
                selected = self._select_sql_or_data_action(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    raw_message=sql_source,
                )

                if selected:
                    return selected

            return None

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return None

        from app.domain.services.chat_presentation_detail_action_service import (
            ChatPresentationDetailActionService,
        )

        detail_plan = ChatPresentationDetailActionService.detect_plan(
            message,
            previous_messages=previous_messages,
        )

        if detail_plan:
            selected = self._route_selection.select_presentation_detail(
                detail_plan,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        refinement = ChatOperationalRefinementService.detect(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if refinement and refinement.kind in {"stock_refinement", "stock_reset"}:
            previous_stock_action_id = self._support.resolve_previous_external_action_id(
                previous_messages,
                path_fragment="/stock",
            )
            selected = self._select_product_action(
                message,
                str(refinement.product_code or ""),
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STOCK,
                preferred_action_id=previous_stock_action_id,
            )

            if selected:
                return selected

        if refinement and refinement.kind in {"metric_refinement", "metric_reset"}:
            selected = self._route_selection.select_metric_refinement(
                message,
                refinement,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        if refinement and refinement.kind == "pagination_refinement":
            selected = self._route_selection.select_pagination_refinement(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
                select_product=self._select_product_action,
            )

            if selected:
                return selected

        if refinement and refinement.kind == "depth_refinement":
            selected = self._route_selection.select_depth_refinement(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
                select_product=self._select_product_action,
                clamp_max_depth=self._clamp_max_depth_for_path,
            )

            if selected:
                return selected

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            selected = self._route_selection.select_production_operational(
                message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                candidates_loader=self._list_allowed_candidates,
                build_date_branch_parameters=self._build_date_branch_parameters,
                path_lookup_loader=self._lookup_production_operational_actions,
            )

            if selected:
                return selected

            return None

        if (
            ExternalActionDomainRouteSelectionService.looks_like_system_metadata_question(
                normalized
            )
            and not ChatProductQueryIntentService.extract_product_code(message)
            and not ChatSqlQueryRefinementService.is_sql_follow_up(
                message,
                previous_messages=previous_messages,
            )
        ):
            selected = self._route_selection.select_system_metadata(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        group_search_code = (
            ExternalActionProductSearchRouteSelectionService.extract_search_group_code(
                message,
                normalized,
            )
        )

        if (
            group_search_code
            and ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
                normalized
            )
            and not ChatProductionOperationalIntentService.matches_rest_route(message)
        ):
            selected = self._route_selection.select_product_search(
                message,
                normalized,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        description_lookup = ChatProductDescriptionResolutionService.extract_description_query(
            message,
        )

        if description_lookup and not ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
            message,
        ):
            resolved_from_history = ChatProductDescriptionResolutionService.resolve_code_from_history(
                description_lookup,
                previous_messages=previous_messages,
            )

            if not resolved_from_history and not ChatProductionOperationalIntentService.matches_rest_route(
                message
            ):
                selected = self._route_selection.select_product_search(
                    message,
                    normalized,
                    allowed_action_ids=allowed_action_ids,
                    candidates_loader=self._list_allowed_candidates,
                    description_override=description_lookup,
                )

                if selected:
                    return selected

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )
        product_intent = ChatProductQueryIntentService.resolve_product_intent(
            message,
            previous_messages=previous_messages,
        )
        product_route_segment = ChatRouteContextService.resolve_product_route_segment(
            message,
            previous_messages=previous_messages,
        )

        if ExternalActionDomainRouteSelectionService.looks_like_sale_orders_list_question(
            normalized
        ):
            selected = self._route_selection.select_sale_orders(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=self._list_allowed_candidates,
                merge_date_parameters=self._merge_date_parameters,
            )

            if selected:
                return selected

        if ExternalActionDomainRouteSelectionService.looks_like_transforma_question(
            normalized
        ):
            selected = self._route_selection.select_transforma(
                message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                candidates_loader=self._list_allowed_candidates,
                build_date_branch_parameters=self._build_date_branch_parameters,
            )

            if selected:
                return selected

        selected = self._route_selection.select_vocabulary_fast_path(
            message,
            normalized,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=self._list_allowed_candidates,
        )

        if selected:
            return selected

        if ExternalActionSelectionHeuristicsService.looks_like_lmp_question(
            normalized,
            extract_sale_number=self._extract_sale_number,
        ):
            selected = self._select_lmp_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
            )

            if selected:
                return selected

        if not product_code:
            selected = self._route_selection.select_kpi_without_product(
                message,
                normalized,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        if product_code and product_intent in _INTENT_BOUND_PRODUCT_INTENTS:
            route_segment = product_route_segment
            bound_intent = product_intent

            if product_intent == ChatProductQueryIntent.SALES:
                route_segment = product_route_segment or "sales"

                if route_segment in ("outbound-invoice", "inbound-invoice"):
                    bound_intent = ChatProductQueryIntent.FULL

            selected = self._route_selection.select_intent_bound_route(
                message,
                product_code,
                intent=bound_intent,
                allowed_action_ids=allowed_action_ids,
                route_segment=route_segment,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

            if (
                product_intent == ChatProductQueryIntent.SALES
                and ChatProductQueryIntentService.extract_product_code(message)
            ):
                return None

        if product_code and (
            ExternalActionSelectionHeuristicsService.looks_like_product_question(
                normalized
            )
            or ChatProductQueryIntentService.extract_product_code(message)
            or product_route_segment
            or ChatProductDescriptionResolutionService.looks_like_description_lookup(message)
        ):
            resolved_intent = (
                product_intent
                if product_intent != ChatProductQueryIntent.FULL
                else ChatProductQueryIntent.FULL
            )

            selected = self._select_product_action(
                message,
                product_code,
                allowed_action_ids=allowed_action_ids,
                intent=resolved_intent,
                route_segment=product_route_segment,
            )

            if selected:
                return selected

        if (
            not product_code
            and ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
                normalized
            )
            and not ChatProductionOperationalIntentService.matches_rest_route(message)
        ):
            selected = self._route_selection.select_product_search(
                message,
                normalized,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=self._list_allowed_candidates,
            )

            if selected:
                return selected

        if ExternalActionSelectionHeuristicsService.looks_like_sql_or_data_query(message):
            if ChatSqlIntentService.should_auto_execute_sql(message):
                return self._select_sql_or_data_action(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    raw_message=sql_source,
                )

        from app.domain.services.chat_operational_parameter_service import (
            ChatOperationalParameterService,
        )

        if ChatOperationalParameterService.should_block_semantic_action_fallback(
            message,
            conversation_context=conversation_context,
        ):
            return None

        return self._route_selection.select_generic(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=self._list_allowed_candidates,
            rank_candidates=self._rank_candidates,
            build_date_branch_parameters=self._build_date_branch_parameters,
        )

    def _build_date_branch_parameters(
        self,
        action: dict,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        return self._route_selection.parameter_builder.build_date_branch(
            action,
            message,
            previous_messages=previous_messages,
        )

    def _select_sql_or_data_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
        selection_reason_key: str | None = None,
        raw_message: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_sql(
            message,
            allowed_action_ids,
            sql=sql,
            selection_reason_key=selection_reason_key,
            raw_message=raw_message,
            candidates_loader=self._list_allowed_candidates,
            rank_candidates=self._rank_candidates,
        )

    def _select_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_product(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=self._list_allowed_candidates,
        )

    @staticmethod
    def _clamp_max_depth_for_path(value: int, path: str) -> int:
        return ExternalActionRouteSelectionService.clamp_max_depth_for_path(value, path)

    def _select_lmp_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_lmp(
            message,
            allowed_action_ids,
            conversation_context=conversation_context,
            candidates_loader=self._list_allowed_candidates,
            merge_date_parameters=self._merge_date_parameters,
        )

    def _extract_sale_number(self, text: str | None) -> str | None:
        return self._route_selection._lmp_route._extract_sale_number(text)

    def _merge_date_parameters(
        self,
        action: dict,
        message: str,
        parameters: dict,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        return self._route_selection.parameter_builder.merge_date_range(
            action,
            message,
            parameters,
            previous_messages=previous_messages,
        )

    def _lookup_production_operational_actions(
        self,
        *,
        path_token: str,
        allowed_action_ids: list[str],
    ) -> list[dict]:
        return self._support.find_allowed_actions_by_path_token(
            path_token=path_token,
            operation_token="",
            allowed_action_ids=allowed_action_ids,
        )

    def _list_allowed_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        limit: int,
    ) -> list[dict]:
        return self._support.list_allowed_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=limit,
        )

    def _rank_candidates(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        return self._support.rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed_action_ids,
        )
