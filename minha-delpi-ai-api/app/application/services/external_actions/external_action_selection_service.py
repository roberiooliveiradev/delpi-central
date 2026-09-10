from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
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

        allowed = allowed_action_ids or []

        # Multi-scope / fast-path pass intent+segment — honor deterministic product routing
        # before OpenAPI-first (which ignores those signals and may invent unknown_tool).
        if intent is not None or route_segment is not None:
            selected = self._select_product_action(
                message,
                code,
                allowed,
                intent=intent or ChatProductQueryIntent.FULL,
                route_segment=route_segment,
                previous_messages=previous_messages,
                drawing_analysis_mode=drawing_analysis_mode,
                attachment_ids=attachment_ids,
            )
            if selected:
                return self._attach_product_selection_shadow(
                    selected,
                    message=message,
                    product_code=code,
                    intent=intent,
                    route_segment=route_segment,
                    allowed_action_ids=list(allowed),
                )

        enriched = f"{message} {code}".strip()
        return self._select_via_openapi_first(
            enriched,
            allowed_action_ids=allowed,
            previous_messages=previous_messages,
            memory_snapshot={
                "executionContext": {
                    "parameters": {"code": code, "productCode": code},
                }
            },
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
        del conversation_context, raw_message
        return self._select_via_openapi_first(
            message,
            allowed_action_ids=allowed_action_ids or [],
            previous_messages=previous_messages,
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
                "name": "execute_external_action",
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
        """Resolve action via metadados técnicos da rota + Action Catalog (OpenAPI-first)."""
        return self._select_registry_route_via_openapi(
            route_id,
            message,
            allowed_action_ids=allowed_action_ids or [],
            previous_messages=previous_messages,
        )

    def _select_registry_route_via_openapi(
        self,
        route_id: str,
        message: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None,
    ) -> dict | None:
        """Usa só metadados técnicos da rota (path/operationId) + Action Catalog."""
        from app.domain.services.operational_route_registry_service import (
            OperationalRouteRegistryService,
        )

        route = OperationalRouteRegistryService.route_by_id(str(route_id or "").strip())
        if not isinstance(route, dict):
            return None

        route_node = route.get("route") if isinstance(route.get("route"), dict) else {}
        path_markers = [
            str(item).strip().lower()
            for item in (route_node.get("pathMarkers") or [])
            if str(item).strip()
        ]
        operation_markers = [
            str(item).strip().lower()
            for item in (route_node.get("operationIdMarkers") or [])
            if str(item).strip()
        ]
        path_suffix = str(route_node.get("pathSuffix") or "").strip().lower()

        list_actions = getattr(self.repository, "list_actions", None)
        if not callable(list_actions):
            return None

        allowed = {str(item) for item in allowed_action_ids}
        matched_ids: list[str] = []
        for action in list_actions():
            action_id = str(action.get("actionId") or "").strip()
            if not action_id or (allowed and action_id not in allowed):
                continue
            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()
            if path_suffix and path_suffix in path:
                matched_ids.append(action_id)
                continue
            if any(marker in path for marker in path_markers):
                matched_ids.append(action_id)
                continue
            if any(marker in operation_id for marker in operation_markers):
                matched_ids.append(action_id)

        if not matched_ids:
            return None

        # Prefer single matched action; otherwise let OpenAPI planner disambiguate.
        selected = self._select_via_openapi_first(
            message,
            allowed_action_ids=matched_ids,
            previous_messages=previous_messages,
            memory_snapshot=None,
        )
        if not isinstance(selected, dict):
            return None
        shadow = self._build_registry_selection_shadow(
            message=message,
            route_id=str(route_id or "").strip(),
            legacy_action_id=self._legacy_action_id(selected),
            marker_matched_ids=list(matched_ids),
            full_allowed_ids=list(allowed_action_ids),
            catalog_actions=list(list_actions()),
            kind="registry_route_id",
        )
        if shadow is not None:
            metadata = dict(selected.get("metadata") or {})
            metadata["registrySelectionShadow"] = shadow
            selected = {**selected, "metadata": metadata}
            from app.domain.services.registry_selection_shadow_observability_service import (
                RegistrySelectionShadowObservabilityService,
            )

            RegistrySelectionShadowObservabilityService.record(shadow)
        return selected

    @staticmethod
    def _legacy_action_id(selected: dict) -> str:
        top = str(selected.get("actionId") or "").strip()
        if top:
            return top
        arguments = selected.get("arguments")
        if isinstance(arguments, dict):
            return str(arguments.get("actionId") or "").strip()
        return ""

    def _attach_product_selection_shadow(
        self,
        selected: dict,
        *,
        message: str,
        product_code: str,
        intent: str | None,
        route_segment: str | None,
        allowed_action_ids: list[str],
    ) -> dict:
        """E1.S4 — shadow do preemption product intent/segment vs retrieval lexical."""
        list_actions = getattr(self.repository, "list_actions", None)
        catalog_actions = list(list_actions()) if callable(list_actions) else []
        enriched = f"{message} {product_code}".strip()
        route_label = (
            f"product.intent:{intent or ''}|segment:{route_segment or ''}"
        ).strip()
        shadow = self._build_registry_selection_shadow(
            message=enriched,
            route_id=route_label,
            legacy_action_id=self._legacy_action_id(selected),
            marker_matched_ids=[],
            full_allowed_ids=list(allowed_action_ids),
            catalog_actions=catalog_actions,
            kind="product_intent_segment",
            intent=intent,
            route_segment=route_segment,
        )
        if shadow is None:
            return selected
        metadata = dict(selected.get("metadata") or {})
        metadata["productSelectionShadow"] = shadow
        from app.domain.services.registry_selection_shadow_observability_service import (
            RegistrySelectionShadowObservabilityService,
        )

        RegistrySelectionShadowObservabilityService.record(shadow)
        return {**selected, "metadata": metadata}

    def _build_registry_selection_shadow(
        self,
        *,
        message: str,
        route_id: str,
        legacy_action_id: str,
        marker_matched_ids: list[str],
        full_allowed_ids: list[str],
        catalog_actions: list[dict],
        kind: str = "registry_route_id",
        intent: str | None = None,
        route_segment: str | None = None,
    ) -> dict | None:
        """E1.S4 — compara autoridade residual vs retrieval lexical no allowlist completo.

        Não altera a action escolhida. Lexical-only (sem semantic_ranker) para não
        duplicar custo de embedding/LLM.
        """
        from app.application.services.retrieve_action_candidates_service import (
            RetrieveActionCandidatesService,
        )
        from app.domain.services.openapi_tool_routing_content_service import (
            OpenApiToolRoutingContentService,
        )

        if not OpenApiToolRoutingContentService.bool_setting(
            "registrySelectionShadow",
            "enabled",
            default=False,
        ):
            return None

        top_k = OpenApiToolRoutingContentService.int_setting(
            "registrySelectionShadow",
            "topK",
            default=5,
        )
        allowed = [str(item).strip() for item in full_allowed_ids if str(item).strip()]
        if not allowed:
            return None

        try:
            candidates = RetrieveActionCandidatesService(
                self.repository,
                semantic_ranker=None,
            ).retrieve(
                message,
                allowed_action_ids=allowed,
                catalog_actions=catalog_actions,
                top_k=max(1, top_k),
            )
        except Exception:
            payload = {
                "kind": kind,
                "routeId": route_id,
                "legacyActionId": legacy_action_id,
                "markerMatchedIds": list(marker_matched_ids),
                "candidateTopIds": [],
                "agree": False,
                "error": "retrieve_failed",
            }
            if intent is not None:
                payload["intent"] = intent
            if route_segment is not None:
                payload["routeSegment"] = route_segment
            return payload

        candidate_ids = [item.action_id for item in candidates]
        payload = {
            "kind": kind,
            "routeId": route_id,
            "legacyActionId": legacy_action_id,
            "markerMatchedIds": list(marker_matched_ids),
            "candidateTopIds": candidate_ids,
            "agree": bool(legacy_action_id) and legacy_action_id in candidate_ids,
        }
        if intent is not None:
            payload["intent"] = intent
        if route_segment is not None:
            payload["routeSegment"] = route_segment
        return payload

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
