from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_route_context_service import ChatRouteContextService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.application.services.external_actions.external_action_selection_dispatch_service import (
    ExternalActionSelectionDispatchService,
)


class ExternalActionSelectionService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15

    def __init__(self, repository, semantic_ranker=None):
        self.repository = repository
        self.semantic_ranker = semantic_ranker
        self._route_selection = ExternalActionRouteSelectionService(repository)
        self._support = ExternalActionSelectionSupportService(
            repository,
            semantic_ranker=semantic_ranker,
        )
        self._dispatch = ExternalActionSelectionDispatchService(
            self._route_selection,
            self._support,
        )

    def select_action_for_product(
        self,
        message: str,
        *,
        product_code: str,
        allowed_action_ids: list[str] | None = None,
        intent: str | None = None,
        route_segment: str | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict | None:
        code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not code or ChatAnalysisIntentService.looks_like_path_placeholder(code):
            return None

        resolved_intent = intent or ChatProductQueryIntentService.detect(message)
        resolved_segment = route_segment or ChatRouteContextService.resolve_product_route_segment(
            message
        )
        preferred_action_id = None

        if previous_messages and resolved_intent == ChatProductQueryIntent.STOCK:
            preferred_action_id = self._support.resolve_previous_external_action_id(
                previous_messages,
            )
            if not preferred_action_id:
                from app.domain.services.operational_route_registry_service import (
                    OperationalRouteRegistryService,
                )

                stock_path_fragment = (
                    OperationalRouteRegistryService.route_path_marker_for_segment("stock")
                    or "/stock"
                )
                preferred_action_id = self._support.resolve_previous_external_action_id(
                    previous_messages,
                    path_fragment=stock_path_fragment,
                )

        return self._select_product_action(
            message,
            code,
            allowed_action_ids=allowed_action_ids or [],
            intent=resolved_intent,
            route_segment=resolved_segment,
            preferred_action_id=preferred_action_id,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
        )

    def select_action(
        self,
        message: str,
        allowed_action_ids: list[str] | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        *,
        raw_message: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        # Fase 9: com OpenAPI-first ativo, não usar registry/markers mesmo via facade.
        from app.domain.services.openapi_planner_mode_service import (
            OpenApiPlannerModeService,
        )

        if OpenApiPlannerModeService.resolve_mode() == "on":
            selected = self._select_via_openapi_first(
                message,
                allowed_action_ids=allowed_action_ids or [],
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
            )
            if selected is not None:
                return selected

        return self._dispatch.dispatch(
            message,
            allowed_action_ids=allowed_action_ids or [],
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            raw_message=raw_message,
            memory_snapshot=memory_snapshot,
        )

    def _select_via_openapi_first(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None,
        memory_snapshot: dict | None,
    ) -> dict | None:
        from app.application.services.openapi_first_selection_bridge_service import (
            OpenApiFirstSelectionBridgeService,
        )
        from app.domain.services.openapi_planner_mode_service import (
            OpenApiPlannerModeDecision,
        )

        workspace_context = None
        if isinstance(memory_snapshot, dict):
            workspace_context = {"workingMemory": memory_snapshot}
        bridge = OpenApiFirstSelectionBridgeService(
            self.repository,
            semantic_ranker=self.semantic_ranker,
        )
        planned = bridge.plan_tool_calls(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            mode_decision=OpenApiPlannerModeDecision(
                mode="on",
                use_openapi_selection=True,
                run_shadow_compare=False,
                canary_matched=False,
            ),
        )
        for item in planned or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "") != "execute_external_action":
                continue
            arguments = dict(item.get("arguments") or {})
            action_id = str(arguments.get("actionId") or "").strip()
            if not action_id:
                continue
            return {
                "actionId": action_id,
                "arguments": arguments,
                "reason": item.get("reason"),
                "metadata": dict(item.get("metadata") or {}),
                "selectionMode": "openapi_first",
            }
        return None

    def select_pagination_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
    ) -> dict | None:
        return self._route_selection.select_pagination_refinement(
            refinement,
            allowed_action_ids=allowed_action_ids,
            message=message,
            select_product=self._select_product_for_refinement,
        )

    def select_operational_group_by_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
    ) -> dict | None:
        return self._route_selection.select_operational_group_by_refinement(
            refinement,
            allowed_action_ids=allowed_action_ids,
        )

    def select_depth_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
    ) -> dict | None:
        return self._route_selection.select_depth_refinement(
            refinement,
            allowed_action_ids=allowed_action_ids,
            message=message,
            select_product=self._select_product_for_refinement,
            clamp_max_depth=self._route_selection.clamp_max_depth_for_path,
        )

    def select_metric_refinement(
        self,
        message: str,
        refinement,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._route_selection.select_metric_refinement(
            message,
            refinement,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=self._list_allowed_candidates,
        )

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
    ) -> dict | None:
        return self._route_selection.select_system_metadata(
            message,
            allowed_action_ids,
            candidates_loader=self._list_allowed_candidates,
        )

    def select_registry_route_id(
        self,
        route_id: str,
        message: str,
        *,
        allowed_action_ids: list[str] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        """Resolve action pelo id do registry (compose multi-rota departamental)."""
        return self._route_selection.select_registry_route_id(
            route_id,
            message,
            allowed_action_ids=allowed_action_ids or [],
            candidates_loader=self._list_allowed_candidates,
            build_date_branch_parameters=self._build_date_branch_parameters,
            previous_messages=previous_messages,
        )

    def _select_product_for_refinement(
        self,
        message: str,
        product_code: str,
        *,
        allowed_action_ids: list[str],
        intent: str | None = None,
        route_segment: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self.select_action_for_product(
            message,
            product_code=product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            previous_messages=previous_messages,
        )

    @staticmethod
    def _looks_like_product_search(value: str) -> bool:
        return ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
            value
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

    def _select_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict | None:
        return self._route_selection.select_product(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=self._list_allowed_candidates,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
        )

    def _build_product_parameters(
        self,
        action: dict,
        code: str,
        *,
        message: str | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict:
        return self._route_selection.build_product_parameters(
            action,
            code,
            message=message,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
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
