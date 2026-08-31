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
        raw_message: str | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        max_calls: int | None = None,
        on_stream_activity=None,
        workspace_context: dict | None = None,
        forced_product_code: str | None = None,
        forced_intent: str | None = None,
        forced_reason: str | None = None,
        forced_route_segment: str | None = None,
        forced_drawing_analysis_mode: bool = False,
    ) -> list[dict]:
        if not selection_service or not allowed_action_ids:
            return []

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return []

        from app.domain.services.chat_active_query_session_service import (
            ChatActiveQuerySessionService,
        )

        selection_message = ChatActiveQuerySessionService.compose_selection_message(
            message,
            previous_messages=previous_messages,
        )

        from app.application.services.chat_conversation_context_service import (
            ChatConversationContextService,
        )

        if (
            ChatAnalysisIntentService.is_data_interpretation_request(
                message,
                previous_messages,
            )
            and ChatConversationContextService.has_recent_tool_data(previous_messages)
            and not cls._continuity_blocks_parallel_discovery(workspace_context)
        ):
            return []

        memory_snapshot = None

        if isinstance(workspace_context, dict):
            working = workspace_context.get("workingMemory")

            if isinstance(working, dict):
                memory_snapshot = working

        def _return_planned(
            planned: list[dict],
            *,
            memory_snapshot: dict | None = None,
        ) -> list[dict]:
            planned = cls._merge_turn_analysis_action_ids(
                selection_service,
                planned=list(planned or []),
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
                message=selection_message,
                raw_message=raw_message,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
                max_calls=max_calls,
            )
            from app.application.services.chat_multi_intent_continuation_service import (
                ChatMultiIntentContinuationService,
            )

            planned, _ = ChatMultiIntentContinuationService.apply_limit(
                planned,
                max_calls=cls._resolve_max_calls(max_calls),
            )

            if on_stream_activity and planned:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                ChatStreamActivityService.emit_planned_actions(
                    on_stream_activity,
                    planned,
                )

            return planned

        if isinstance(workspace_context, dict):
            from app.domain.services.chat_grounded_capability_planning_service import (
                ChatGroundedCapabilityPlanningService,
            )

            grounded_planned = ChatGroundedCapabilityPlanningService.plan_actions(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
                max_calls=max_calls,
            )

            if cls._continuity_blocks_parallel_discovery(workspace_context):
                return _return_planned(
                    list(grounded_planned or []),
                    memory_snapshot=memory_snapshot,
                )

            if grounded_planned:
                return _return_planned(grounded_planned, memory_snapshot=memory_snapshot)

        if forced_product_code and forced_intent:
            selected = selection_service.select_action_for_product(
                message,
                product_code=forced_product_code,
                allowed_action_ids=allowed_action_ids,
                intent=forced_intent,
                route_segment=forced_route_segment,
                previous_messages=previous_messages,
                drawing_analysis_mode=forced_drawing_analysis_mode,
            )

            if selected and forced_reason:
                selected["reason"] = forced_reason

            if selected and forced_drawing_analysis_mode:
                selected = cls._apply_drawing_analyser_full_view(
                    selection_service,
                    selected,
                    message=message,
                )

            return _return_planned([selected] if selected else [], memory_snapshot=memory_snapshot)

        from app.domain.services.chat_operational_intent_fast_path_service import (
            ChatOperationalIntentFastPathService,
        )

        fast_product_code, fast_intent = (
            ChatOperationalIntentFastPathService.resolve_operational_fast_path(
                selection_message,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
            )
        )
        fast_path_codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            selection_message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if (
            fast_product_code
            and fast_intent == ChatProductQueryIntent.STOCK
            and len(fast_path_codes) <= 1
            and not forced_drawing_analysis_mode
        ):
            selected = selection_service.select_action_for_product(
                selection_message,
                product_code=fast_product_code,
                allowed_action_ids=allowed_action_ids,
                intent=fast_intent,
                previous_messages=previous_messages,
            )

            if selected:
                return _return_planned([selected], memory_snapshot=memory_snapshot)

        from app.domain.services.chat_sql_authoring_guidance_service import (
            ChatSqlAuthoringGuidanceService,
        )
        from app.domain.services.chat_advanced_sql_specialist_service import (
            ChatAdvancedSqlSpecialistService,
        )

        if ChatAdvancedSqlSpecialistService.should_prefetch_schema(
            message=message,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
        ):
            prefetch = ChatSqlAuthoringGuidanceService.plan_schema_prefetch(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
            )

            if prefetch:
                return _return_planned(prefetch, memory_snapshot=memory_snapshot)

        from app.application.services.chat_intelligence_runtime_access import (
            resolve_chat_intelligence_runtime,
        )

        if not resolve_chat_intelligence_runtime().multi_action_enabled:
            selected = selection_service.select_action(
                selection_message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                raw_message=raw_message,
                memory_snapshot=memory_snapshot,
            )

            return _return_planned([selected] if selected else [], memory_snapshot=memory_snapshot)

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            if not ChatProductionOperationalIntentService.matches_rest_route(message):
                if on_stream_activity:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )
                    from app.domain.services.chat_assistant_content_service import (
                        ChatAssistantContentService,
                    )

                    comparison = ChatAssistantContentService.get_mapping(
                        "stream",
                        "activity",
                        "structureComparison",
                    )
                    on_stream_activity(
                        ChatStreamActivityService.plan_step(
                            step=1,
                            total=1,
                            target=str(comparison.get("target") or ""),
                            verb=str(comparison.get("verb") or ""),
                            message=str(comparison.get("message") or ""),
                            detail=str(comparison.get("detail") or ""),
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
                    return _return_planned(planned, memory_snapshot=memory_snapshot)

        if ChatCanvasIntentService.blocks_external_action_selection(message):
            return []

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            selected = selection_service.select_action(
                selection_message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                raw_message=raw_message,
                memory_snapshot=memory_snapshot,
            )

            if selected:
                return _return_planned([selected], memory_snapshot=memory_snapshot)

            return []

        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        if OperationalRouteMatcherService.looks_like_sale_orders_list_question(
            normalized
        ):
            selected = selection_service.select_action(
                selection_message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                raw_message=raw_message,
                memory_snapshot=memory_snapshot,
            )

            return _return_planned([selected] if selected else [], memory_snapshot=memory_snapshot)

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
                        selection_message,
                        product_code=str(refinement.product_code or ""),
                        allowed_action_ids=allowed_action_ids,
                        intent=ChatProductQueryIntent.STOCK,
                        previous_messages=previous_messages,
                    )
                elif refinement.kind in {"metric_refinement", "metric_reset"}:
                    select_metric = getattr(
                        selection_service,
                        "select_metric_refinement",
                        None,
                    )

                    if callable(select_metric):
                        selected = select_metric(
                            selection_message,
                            refinement,
                            allowed_action_ids=allowed_action_ids,
                            previous_messages=previous_messages,
                        )
                    else:
                        selected = selection_service.select_action(
                            selection_message,
                            allowed_action_ids=allowed_action_ids,
                            conversation_context=conversation_context,
                            previous_messages=previous_messages,
                            raw_message=raw_message,
                            memory_snapshot=memory_snapshot,
                        )
                elif refinement.kind == "pagination_refinement":
                    select_pagination = getattr(
                        selection_service,
                        "select_pagination_refinement",
                        None,
                    )

                    if callable(select_pagination):
                        selected = select_pagination(
                            refinement,
                            allowed_action_ids=allowed_action_ids,
                            message=selection_message,
                        )
                    else:
                        selected = selection_service.select_action(
                            selection_message,
                            allowed_action_ids=allowed_action_ids,
                            conversation_context=conversation_context,
                            previous_messages=previous_messages,
                            raw_message=raw_message,
                            memory_snapshot=memory_snapshot,
                        )
                elif refinement.kind == "operational_group_by_refinement":
                    select_group_by = getattr(
                        selection_service,
                        "select_operational_group_by_refinement",
                        None,
                    )

                    if callable(select_group_by):
                        selected = select_group_by(
                            refinement,
                            allowed_action_ids=allowed_action_ids,
                        )
                    else:
                        selected = selection_service.select_action(
                            selection_message,
                            allowed_action_ids=allowed_action_ids,
                            conversation_context=conversation_context,
                            previous_messages=previous_messages,
                            raw_message=raw_message,
                            memory_snapshot=memory_snapshot,
                        )
                elif refinement.kind == "depth_refinement":
                    select_depth = getattr(
                        selection_service,
                        "select_depth_refinement",
                        None,
                    )

                    if callable(select_depth):
                        selected = select_depth(
                            refinement,
                            allowed_action_ids=allowed_action_ids,
                            message=selection_message,
                        )
                    else:
                        selected = selection_service.select_action(
                            selection_message,
                            allowed_action_ids=allowed_action_ids,
                            conversation_context=conversation_context,
                            previous_messages=previous_messages,
                            raw_message=raw_message,
                            memory_snapshot=memory_snapshot,
                        )
                else:
                    selected = None

                if selected:
                    planned.append(selected)

            if planned:
                return _return_planned(planned, memory_snapshot=memory_snapshot)

            return _return_planned([], memory_snapshot=memory_snapshot)

        limit = cls._resolve_max_calls(max_calls)
        planning_message = selection_message
        normalized = ChatMessageNormalizationService.normalize_for_matching(planning_message)
        codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            planning_message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )
        intent = ChatProductQueryIntentService.resolve_product_intent(
            planning_message,
            previous_messages=previous_messages,
        )
        route_segment = ChatRouteContextService.resolve_product_route_segment(
            planning_message,
            previous_messages=previous_messages,
        )

        explicit_route_segment = ChatRouteContextService.segment_from_message(planning_message)

        if intent == ChatProductQueryIntent.FULL:
            intent = ChatProductQueryIntentService.refine_operational_intent_from_full(
                planning_message,
                normalized=normalized,
            )

        recent_batch = ChatRouteContextService.collect_recent_product_route_batch(
            previous_messages,
            route_segment=None if explicit_route_segment else route_segment,
        )

        if (
            not codes
            and recent_batch
            and (
                ChatProductQueryIntentService.references_previous_product(planning_message)
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
            candidate_cap = max(limit, 12)

            for code in codes[:candidate_cap]:
                selected = selection_service.select_action_for_product(
                    selection_message,
                    product_code=code,
                    allowed_action_ids=allowed_action_ids,
                    intent=intent,
                    route_segment=route_segment,
                    previous_messages=previous_messages,
                )

                if selected:
                    planned.append(selected)

            if planned:
                from app.application.services.chat_multi_intent_continuation_service import (
                    ChatMultiIntentContinuationService,
                )

                executed, _ = ChatMultiIntentContinuationService.apply_limit(
                    planned,
                    max_calls=limit,
                )

                return _return_planned(executed, memory_snapshot=memory_snapshot)

        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        product_code = ChatProductQueryIntentService.resolve_product_code(
            planning_message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if product_code:
            scope_planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
                selection_service,
                message=planning_message,
                product_code=product_code,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                max_calls=12,
            )

            if scope_planned:
                from app.application.services.chat_multi_intent_continuation_service import (
                    ChatMultiIntentContinuationService,
                )

                executed, _ = ChatMultiIntentContinuationService.apply_limit(
                    scope_planned,
                    max_calls=limit,
                )

                return _return_planned(executed, memory_snapshot=memory_snapshot)

        from app.domain.services.chat_product_enrichment_composition_planning_service import (
            ChatProductEnrichmentCompositionPlanningService,
        )

        if product_code and ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
            planning_message
        ):
            enrichment_planned = ChatProductEnrichmentCompositionPlanningService.plan(
                selection_service,
                message=planning_message,
                product_code=product_code,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                max_calls=limit,
            )

            if enrichment_planned:
                from app.application.services.chat_multi_intent_continuation_service import (
                    ChatMultiIntentContinuationService,
                )

                executed, deferred = ChatMultiIntentContinuationService.apply_limit(
                    enrichment_planned,
                    max_calls=limit,
                )
                enrichment_audit = {
                    "kind": "product_enrichment_composition",
                    "plannedScopes": [
                        str(item.get("enrichmentScope") or "").strip()
                        for item in enrichment_planned
                        if str(item.get("enrichmentScope") or "").strip()
                    ],
                    "executedCount": len(executed),
                    "skippedByCap": int((deferred or {}).get("deferredCount") or 0)
                    if isinstance(deferred, dict)
                    else 0,
                    "productCode": product_code,
                }

                if executed:
                    first = dict(executed[0])
                    first["enrichmentPlan"] = enrichment_audit
                    executed = [first, *executed[1:]]

                return _return_planned(executed, memory_snapshot=memory_snapshot)

        from app.domain.services.chat_department_meta_composition_planning_service import (
            ChatDepartmentMetaCompositionPlanningService,
        )

        if ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
            planning_message
        ):
            meta_planned = ChatDepartmentMetaCompositionPlanningService.plan(
                selection_service,
                message=planning_message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                max_calls=limit,
            )

            if meta_planned:
                return _return_planned(meta_planned, memory_snapshot=memory_snapshot)

        selected = selection_service.select_action(
            selection_message,
            allowed_action_ids=allowed_action_ids,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            raw_message=raw_message,
            memory_snapshot=memory_snapshot,
        )

        return _return_planned([selected] if selected else [], memory_snapshot=memory_snapshot)

    @classmethod
    def _apply_drawing_analyser_full_view(
        cls,
        selection_service,
        selected: dict | None,
        *,
        message: str,
    ) -> dict | None:
        if not isinstance(selected, dict):
            return selected

        from app.domain.services.chat_drawing_analyser_parameter_service import (
            ChatDrawingAnalyserParameterService,
        )

        arguments = selected.get("arguments") or {}
        action_id = str(arguments.get("actionId") or "").strip()
        action: dict = {"path": "/products/{code}/analyser"}

        if action_id and getattr(selection_service, "repository", None):
            bundle = selection_service.repository.get_action_for_execution(action_id)

            if isinstance(bundle, dict) and isinstance(bundle.get("action"), dict):
                action = bundle["action"]

        return ChatDrawingAnalyserParameterService.apply_to_tool_call(
            selected,
            action=action,
            drawing_analysis_mode=True,
            message=message,
        )

    @classmethod
    def _mode_multi_action_cap(cls) -> int:
        try:
            from app.domain.services.chat_response_mode_context_budget_service import (
                ChatResponseModeContextBudgetService,
            )
            from app.infrastructure.llm.llm_request_context import get_active_config

            return ChatResponseModeContextBudgetService.max_multi_actions_per_turn(
                get_active_config().response_mode
            )
        except Exception:
            return 4

    @classmethod
    def _resolve_max_calls(cls, max_calls: int | None) -> int:
        cap = max(1, min(int(getattr(Settings, "CHAT_MULTI_ACTION_MAX_CALLS", 50)), 50))
        mode_cap = max(1, cls._mode_multi_action_cap())
        effective_cap = min(cap, mode_cap)

        if max_calls is not None:
            return max(1, min(int(max_calls), effective_cap))

        return effective_cap

    @classmethod
    def _turn_analysis_action_ids(cls, workspace_context: dict | None) -> list[str]:
        if not isinstance(workspace_context, dict):
            return []
        raw = workspace_context.get("turnAnalysisActionIds") or []
        if not isinstance(raw, list):
            return []
        ordered: list[str] = []
        seen: set[str] = set()
        for item in raw:
            action_id = str(item or "").strip()
            if not action_id or action_id in seen:
                continue
            seen.add(action_id)
            ordered.append(action_id)
        return ordered

    @classmethod
    def _merge_turn_analysis_action_ids(
        cls,
        selection_service,
        *,
        planned: list[dict],
        workspace_context: dict | None,
        allowed_action_ids: list[str],
        message: str,
        raw_message: str | None,
        conversation_context: str | None,
        previous_messages: list | None,
        memory_snapshot: dict | None,
        max_calls: int | None,
    ) -> list[dict]:
        analysis_ids = cls._turn_analysis_action_ids(workspace_context)
        if not analysis_ids:
            return planned

        from app.application.services.chat_intelligence_runtime_access import (
            resolve_chat_intelligence_runtime,
        )

        multi_enabled = bool(resolve_chat_intelligence_runtime().multi_action_enabled)
        merge_cap = max(cls._resolve_max_calls(max_calls), cls._mode_multi_action_cap(), 6)
        if not multi_enabled:
            merge_cap = max(merge_cap, 6)
        allowed = {
            str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()
        }
        merged = list(planned or [])
        existing = {
            str(item.get("actionId") or "").strip()
            for item in merged
            if isinstance(item, dict) and str(item.get("actionId") or "").strip()
        }

        # Heurística já fechou 1 rota com alta confiança e analysis só confirma a mesma.
        if len(merged) == 1 and analysis_ids == list(existing):
            return merged

        for action_id in analysis_ids:
            if len(merged) >= merge_cap:
                break
            if action_id in existing:
                continue
            if allowed and action_id not in allowed:
                continue

            selected = selection_service.select_action(
                message,
                allowed_action_ids=[action_id],
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                raw_message=raw_message,
                memory_snapshot=memory_snapshot,
            )
            if not selected:
                continue
            selected_id = str(selected.get("actionId") or "").strip()
            if not selected_id or selected_id in existing:
                continue
            selected = dict(selected)
            selected["reason"] = selected.get("reason") or "turn_analysis_action"
            selected["fromTurnAnalysis"] = True
            merged.append(selected)
            existing.add(selected_id)

        return merged[:merge_cap]

    @classmethod
    def _continuity_blocks_parallel_discovery(
        cls,
        workspace_context: dict | None,
    ) -> bool:
        """Consome o contrato do interpretador — sem enumerar stages."""
        if not isinstance(workspace_context, dict):
            return False

        turn_grounding = workspace_context.get("turnGrounding")
        if not isinstance(turn_grounding, dict):
            return False

        follow_up = turn_grounding.get("followUp")
        if not isinstance(follow_up, dict):
            return False

        if "allowsParallelDiscovery" in follow_up:
            return follow_up.get("allowsParallelDiscovery") is False

        continuity_mode = str(follow_up.get("continuityMode") or "").strip()
        if continuity_mode:
            return continuity_mode != "allow_discovery"

        decision = str(follow_up.get("decision") or "").strip()
        if not decision:
            return False

        from app.domain.services.chat_follow_up_turn_content_service import (
            ChatFollowUpTurnContentService,
        )

        return (
            ChatFollowUpTurnContentService.continuity_mode_for_decision(decision)
            != "allow_discovery"
        )

    @classmethod
    def _resolve_product_intent(cls, message: str, normalized: str) -> str:
        intent = ChatProductQueryIntentService.detect(message)

        if intent != ChatProductQueryIntent.FULL:
            return intent

        return ChatProductQueryIntentService.refine_operational_intent_from_full(
            message,
            normalized=normalized,
        )
