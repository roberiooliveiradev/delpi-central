from __future__ import annotations

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.infrastructure.config.settings import Settings


class ChatExternalActionOrchestrationService:
    """Planeja uma ou mais consultas OpenAPI (actions) para a mesma pergunta."""

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
            # OpenAPI-first: não reentrar no registry via turn_analysis.select_action.
            if not cls._planned_is_openapi_first(planned):
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
            else:
                planned = list(planned or [])
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
            from app.domain.services.chat_product_multi_scope_planning_service import (
                ChatProductMultiScopePlanningService,
            )

            grounded_planned = ChatGroundedCapabilityPlanningService.plan_actions(
                selection_service,
                message=message,
                allowed_action_ids=allowed_action_ids,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
                max_calls=max_calls,
            )
            missing_scopes = (
                ChatProductMultiScopePlanningService.missing_scopes_for_planned_actions(
                    selection_message,
                    grounded_planned,
                )
            )
            if cls._continuity_blocks_parallel_discovery(workspace_context):
                if not missing_scopes:
                    return _return_planned(
                        list(grounded_planned or []),
                        memory_snapshot=memory_snapshot,
                    )
            elif grounded_planned and not missing_scopes:
                return _return_planned(
                    grounded_planned,
                    memory_snapshot=memory_snapshot,
                )

        from app.application.services.openapi_first_selection_bridge_service import (
            OpenApiFirstSelectionBridgeService,
        )
        from app.domain.services.openapi_planner_mode_service import (
            OpenApiPlannerModeService,
        )
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        provider_keys: set[str] = set()
        if isinstance(workspace_context, dict):
            for key in workspace_context.get("providerKeys") or []:
                if str(key).strip():
                    provider_keys.add(str(key).strip())
        for action_id in allowed_action_ids or []:
            text = str(action_id)
            if "." in text:
                provider_keys.add(text.split(".", 1)[0])

        agent_id = None
        if isinstance(workspace_context, dict):
            agent_id = (
                workspace_context.get("agentId")
                or workspace_context.get("activeAgentId")
                or workspace_context.get("contextAgentId")
            )

        openapi_decision = OpenApiPlannerModeService.decide(
            provider_keys=provider_keys,
            agent_id=str(agent_id) if agent_id else None,
        )
        bridge = OpenApiFirstSelectionBridgeService(
            getattr(selection_service, "repository", None),
            semantic_ranker=getattr(selection_service, "semantic_ranker", None),
        )
        openapi_planned = bridge.plan_tool_calls(
            selection_message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            mode_decision=openapi_decision,
        )
        if openapi_planned:
            openapi_planned = cls._enrich_openapi_plan_with_product_scopes(
                selection_service,
                message=selection_message,
                planned=openapi_planned,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
                max_calls=max_calls or 12,
            )
            openapi_planned = cls._enrich_openapi_plan_with_department_meta(
                selection_service,
                message=selection_message,
                planned=openapi_planned,
                allowed_action_ids=allowed_action_ids,
                max_calls=max_calls or 12,
            )
            return _return_planned(
                openapi_planned,
                memory_snapshot=memory_snapshot,
            )

        department_fallback = cls._enrich_openapi_plan_with_department_meta(
            selection_service,
            message=selection_message,
            planned=[],
            allowed_action_ids=allowed_action_ids,
            max_calls=max_calls or 12,
        )
        if department_fallback:
            return _return_planned(
                department_fallback,
                memory_snapshot=memory_snapshot,
            )

        clarify = OpenApiToolRoutingContentService.get(
            "selectionReasons",
            "openapiFirstNoMatch",
        )
        return _return_planned(
            [
                {
                    "name": "clarify_external_action",
                    "arguments": {"message": clarify},
                    "reason": clarify,
                    "directAnswer": clarify,
                    "metadata": {
                        "selectionMode": "openapi_first",
                        "emptyPlan": True,
                    },
                }
            ],
            memory_snapshot=memory_snapshot,
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
    def _planned_is_openapi_first(cls, planned: list[dict] | None) -> bool:
        items = [item for item in (planned or []) if isinstance(item, dict)]
        if not items:
            return False
        return all(
            str((item.get("metadata") or {}).get("selectionMode") or "") == "openapi_first"
            for item in items
        )

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
    def _enrich_openapi_plan_with_department_meta(
        cls,
        selection_service,
        *,
        message: str,
        planned: list[dict],
        allowed_action_ids: list[str] | None,
        max_calls: int,
    ) -> list[dict]:
        """E5.S5 — composição departamental por goals + Action Catalog (sem routeId)."""
        from app.domain.services.chat_department_meta_composition_planning_service import (
            ChatDepartmentMetaCompositionPlanningService,
        )

        if not ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
            message
        ):
            return list(planned or [])

        catalog = cls._actions_by_id_from_selection(
            selection_service,
            allowed_action_ids=allowed_action_ids,
        )
        if not catalog:
            return list(planned or [])

        dept_planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
            message=message,
            allowed_action_ids=allowed_action_ids,
            actions_by_id=catalog,
            max_calls=max_calls,
        )
        if not dept_planned:
            return list(planned or [])

        items = [item for item in (planned or []) if isinstance(item, dict)]
        mode = ChatDepartmentMetaCompositionPlanningService.composition_mode(message)
        limit = max(1, min(int(max_calls), 12))

        if not items or cls._planned_is_clarify_or_unknown_only(items):
            return dept_planned[:limit]

        if mode != "compose":
            return items

        existing = {
            str((item.get("arguments") or {}).get("actionId") or "").strip()
            for item in items
            if isinstance(item, dict)
        }
        merged = list(items)
        for item in dept_planned:
            action_id = str((item.get("arguments") or {}).get("actionId") or "").strip()
            if not action_id or action_id in existing:
                continue
            merged.append(item)
            existing.add(action_id)
            if len(merged) >= limit:
                break
        return merged

    @classmethod
    def _actions_by_id_from_selection(
        cls,
        selection_service,
        *,
        allowed_action_ids: list[str] | None,
    ) -> dict[str, dict]:
        allowed = {
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        }
        catalog: dict[str, dict] = {}
        repository = getattr(selection_service, "repository", None)
        list_actions = getattr(repository, "list_actions", None) if repository else None
        if not callable(list_actions):
            return catalog
        try:
            rows = list_actions() or []
        except Exception:
            return catalog
        for row in rows:
            if not isinstance(row, dict):
                continue
            action_id = str(row.get("actionId") or row.get("action_id") or "").strip()
            if not action_id or (allowed and action_id not in allowed):
                continue
            catalog[action_id] = dict(row)
        return catalog

    @classmethod
    def _enrich_openapi_plan_with_product_scopes(
        cls,
        selection_service,
        *,
        message: str,
        planned: list[dict],
        allowed_action_ids: list[str] | None,
        conversation_context: str | None,
        previous_messages: list | None,
        memory_snapshot: dict | None,
        max_calls: int,
    ) -> list[dict]:
        """Complete OpenAPI-first plans that omit product scopes the user asked for.

        Example: «estoque e descrição» must not stop at /summary without /stock.
        When OpenAPI returns clarify-only despite product scopes being available,
        replace with multi-scope product fetches.
        """
        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        items = [item for item in (planned or []) if isinstance(item, dict)]
        if not items:
            return list(planned or [])

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )
        requested = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        def _plan_scopes() -> list[dict]:
            if not product_code or not requested:
                return []
            if not callable(getattr(selection_service, "select_action_for_product", None)):
                return []
            return list(
                ChatProductMultiScopePlanningService.plan_product_scope_fetches(
                    selection_service,
                    message=message,
                    product_code=product_code,
                    allowed_action_ids=allowed_action_ids,
                    previous_messages=previous_messages,
                    max_calls=max_calls,
                )
                or []
            )

        if cls._planned_is_clarify_or_unknown_only(items) and requested:
            scope_planned = _plan_scopes()
            if scope_planned:
                return scope_planned[: max(1, min(int(max_calls), 12))]

        missing = ChatProductMultiScopePlanningService.missing_scopes_for_planned_actions(
            message,
            items,
        )
        if not missing:
            return items

        scope_planned = _plan_scopes()
        if not scope_planned:
            return items

        limit = max(1, min(int(max_calls), 12))
        if len(requested) == 1 and requested[0] in missing:
            return scope_planned[:limit]

        merged = [
            item
            for item in items
            if str(item.get("name") or "")
            not in {"clarify_external_action", "unknown_tool"}
        ]
        seen_paths = {
            str(
                (item.get("arguments") or {}).get("path") or item.get("path") or ""
            ).lower()
            for item in merged
        }
        for item in scope_planned:
            if len(merged) >= limit:
                break
            path = str(
                (item.get("arguments") or {}).get("path") or item.get("path") or ""
            ).lower()
            if path and path in seen_paths:
                continue
            merged.append(item)
            if path:
                seen_paths.add(path)
        return merged or items

    @classmethod
    def _planned_is_clarify_or_unknown_only(cls, planned: list[dict]) -> bool:
        names = {str(item.get("name") or "").strip() for item in planned if isinstance(item, dict)}
        names.discard("")
        if not names:
            return True
        return names.issubset({"clarify_external_action", "unknown_tool"})

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
