"""Motor declarativo de fast paths — operational_route_registry (DOCIE Fase 0–3)."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ExternalActionOperationalRouteSelectionService:
    def __init__(self, product_route) -> None:
        self._product_route = product_route

    def select(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        for route in OperationalRouteRegistryService.vocabulary_routes():
            selected = self._try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def select_by_intent(
        self,
        message: str,
        product_code: str,
        intent: str,
        allowed_action_ids: list[str],
        *,
        route_segment: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        normalized_intent = str(intent or "").strip().lower()
        normalized_segment = str(route_segment or "").strip().lower()

        if not normalized_intent or not str(product_code or "").strip():
            return None

        for route in OperationalRouteRegistryService.intent_bound_routes():
            binding = str(route.get("intentBinding") or "").strip().lower()

            if binding != normalized_intent:
                continue

            route_segment_spec = str(route.get("routeSegment") or "").strip().lower()

            if route_segment_spec:
                if route_segment_spec != normalized_segment:
                    continue
            elif normalized_segment in ("inbound-invoice", "outbound-invoice"):
                continue

            selected = self._resolve_route_action(
                route,
                message,
                allowed_action_ids,
                identifier=product_code,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def select_production_operational(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        path_lookup_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        kind = ChatProductionOperationalIntentService.resolve(message)

        if not kind:
            return None

        route = OperationalRouteRegistryService.route_by_production_operational_kind(
            kind.value
        )

        if not route:
            return None

        candidate_sets: list[list[dict]] = [
            self._product_route._load_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )
        ]

        path_token = ChatProductionOperationalIntentService.path_token_for(kind)

        if path_lookup_loader and path_token:
            path_candidates = path_lookup_loader(
                path_token=path_token,
                allowed_action_ids=allowed_action_ids,
            )

            if path_candidates:
                candidate_sets.append(path_candidates)

        for candidates in candidate_sets:
            selected = self._resolve_route_action(
                route,
                message,
                allowed_action_ids,
                candidates=candidates,
                previous_messages=previous_messages,
                build_date_branch_parameters=build_date_branch_parameters,
                production_kind=kind,
            )

            if selected:
                return selected

        return None

    def select_sale_orders(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        if not merge_date_parameters:
            return None

        route = OperationalRouteRegistryService.route_by_id("commercialSaleOrders")

        if not route:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return self._try_vocabulary_route(
            route,
            message,
            normalized,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            merge_date_parameters=merge_date_parameters,
        )

    def select_transforma(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        if not build_date_branch_parameters:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for route_id in ("engineeringTransformaSummary", "engineeringTransformaProcesses"):
            route = OperationalRouteRegistryService.route_by_id(route_id)

            if not route:
                continue

            selected = self._try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
                build_date_branch_parameters=build_date_branch_parameters,
            )

            if selected:
                return selected

        return None

    def _try_vocabulary_route(
        self,
        route: dict,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        match_spec = route.get("match")

        if not isinstance(match_spec, dict):
            return None

        if not OperationalRouteMatcherService.matches(
            match_spec,
            message=message,
            normalized=normalized,
        ):
            return None

        identifier = None

        if match_spec.get("requiresProductIdentifier"):
            identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return None

        return self._resolve_route_action(
            route,
            message,
            allowed_action_ids,
            identifier=identifier,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
        )

    def _resolve_route_action(
        self,
        route: dict,
        message: str,
        allowed_action_ids: list[str],
        *,
        identifier: str | None = None,
        candidates: list[dict] | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        production_kind: ProductionOperationalIntentKind | None = None,
    ) -> dict | None:
        route_spec = route.get("route")

        if not isinstance(route_spec, dict):
            return None

        path_markers = [
            str(marker).lower()
            for marker in (route_spec.get("pathMarkers") or [])
            if str(marker).strip()
        ]
        operation_markers = [
            str(marker).lower()
            for marker in (route_spec.get("operationIdMarkers") or [])
            if str(marker).strip()
        ]
        exclude_path_markers = [
            str(marker).lower()
            for marker in (route_spec.get("excludePathMarkers") or [])
            if str(marker).strip()
        ]
        path_exact_end = str(route_spec.get("pathExactEnd") or "").strip().lower()
        path_suffix = str(route_spec.get("pathSuffix") or "").strip().lower()

        if (
            not path_markers
            and not operation_markers
            and not path_exact_end
            and not path_suffix
        ):
            return None

        if candidates is None:
            candidates = self._product_route._find_allowed_actions_by_markers(
                path_markers=path_markers or ([path_exact_end] if path_exact_end else []),
                operation_markers=operation_markers,
                allowed_action_ids=allowed_action_ids,
            )

            if not candidates:
                candidates = self._product_route._load_candidates(
                    message,
                    allowed_action_ids=allowed_action_ids,
                    candidates_loader=candidates_loader,
                )

        expected_method = str(route_spec.get("method") or "GET").upper()

        for action in candidates:
            if str(action.get("method") or "GET").upper() != expected_method:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if path_exact_end and not path.rstrip("/").endswith(path_exact_end.rstrip("/")):
                continue

            if path_suffix and not path.rstrip("/").endswith(path_suffix.rstrip("/")):
                if not operation_markers or not any(
                    marker in operation_id for marker in operation_markers
                ):
                    continue

            if path_markers and not any(marker in path for marker in path_markers):
                if not (
                    path_suffix
                    and path.rstrip("/").endswith(path_suffix.rstrip("/"))
                ):
                    if not operation_markers or not any(
                        marker in operation_id for marker in operation_markers
                    ):
                        continue

            if exclude_path_markers and any(marker in path for marker in exclude_path_markers):
                continue

            if operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                if path_markers or path_exact_end or path_suffix:
                    if not path_markers or not any(marker in path for marker in path_markers):
                        if not path_suffix or not path.rstrip("/").endswith(
                            path_suffix.rstrip("/")
                        ):
                            continue

            if (
                not path_markers
                and not path_exact_end
                and not path_suffix
                and operation_markers
                and not any(marker in operation_id for marker in operation_markers)
            ):
                continue

            if "search" in path and not path_markers and not path_exact_end and not path_suffix:
                continue

            parameters = self._build_parameters(
                route,
                action,
                message=message,
                identifier=identifier,
                previous_messages=previous_messages,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                production_kind=production_kind,
            )

            if parameters is None:
                continue

            presentation = route.get("presentation") or {}
            reason_key = str(presentation.get("reasonKey") or route.get("id") or "").strip()

            if not reason_key:
                continue

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": ExternalActionResponseContentService.get(
                    "selectionReasons",
                    reason_key,
                ),
            }

        return None

    def _build_parameters(
        self,
        route: dict,
        action: dict,
        *,
        message: str,
        identifier: str | None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        production_kind: ProductionOperationalIntentKind | None = None,
    ) -> dict | None:
        parameters_spec = route.get("parameters") or {}
        strategy = str(parameters_spec.get("strategy") or "").strip()

        if strategy == "product_code":
            if not identifier:
                identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return None

            return self._product_route._build_product_parameters(
                action,
                identifier,
                message=message,
            )

        if strategy == "exclusive_catalog":
            normalized = message.lower()

            return self._product_route._build_exclusive_catalog_parameters(
                action,
                message=message,
                normalized=normalized,
            )

        if strategy == "date_branch":
            parameters: dict = {}

            if build_date_branch_parameters:
                parameters = build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                )

            if production_kind in {
                ProductionOperationalIntentKind.LOSSES_TOP,
                ProductionOperationalIntentKind.LOSSES_RECORDS,
            }:
                loss_type = ChatProductionOperationalIntentService.infer_loss_type(
                    ChatMessageNormalizationService.normalize_for_matching(message)
                )

                if loss_type:
                    parameters["loss_type"] = loss_type

            if production_kind == ProductionOperationalIntentKind.CONSUMPTION_BY_ITEM:
                product_code = ChatProductQueryIntentService.extract_product_code(message)

                if product_code:
                    parameters["code"] = product_code

            if not parameters:
                parameters = {"limit": 10}

            return parameters

        if strategy == "sale_orders":
            parameters = {}

            for parameter in action.get("parametersSchema") or []:
                name = parameter.get("name")

                if not name:
                    continue

                lowered = name.lower()

                if lowered in {"page"}:
                    parameters[name] = 1
                elif lowered in {"page_size", "pagesize", "limit"}:
                    parameters[name] = 50

            if not merge_date_parameters:
                return parameters or {"limit": 50}

            return merge_date_parameters(action, message, parameters)

        return None
