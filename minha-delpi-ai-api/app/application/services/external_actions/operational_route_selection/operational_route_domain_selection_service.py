"""Seletores por domínio — produção, produto, LMP, sistema, KPI."""

from __future__ import annotations

from typing import Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class OperationalRouteDomainSelectionService:
    def __init__(self, catalog, resolver, vocabulary) -> None:
        self._catalog = catalog
        self._resolver = resolver
        self._vocabulary = vocabulary

    def select_by_department_kpi(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )

        match = ChatDepartmentKpiIntentService.resolve(message)

        if not match:
            return None

        spec = OperationalApiRouteSpec.from_department_kpi(match)
        route = OperationalRouteDomainSelectionService._virtual_department_kpi_route(spec)

        selected = self._resolver.resolve_route_action(
            route,
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
        )

        if selected and spec.reason:
            selected["reason"] = spec.reason

        return selected

    @staticmethod
    def _virtual_department_kpi_route(spec) -> dict:
        path_markers: list[str] = []

        for token in spec.path_tokens:
            normalized_token = str(token or "").strip().lower()

            if not normalized_token:
                continue

            if normalized_token.startswith("/"):
                path_markers.append(normalized_token)
                continue

            for prefix in spec.path_prefixes:
                path_markers.append(
                    f"{str(prefix).rstrip('/').lower()}/{normalized_token}"
                )

            if not spec.path_prefixes:
                path_markers.append(normalized_token)

        for prefix in spec.path_prefixes:
            normalized_prefix = str(prefix or "").strip().lower()

            if normalized_prefix and normalized_prefix not in path_markers:
                path_markers.append(normalized_prefix)

        return {
            "presentation": {"reasonKey": "departmentKpi"},
            "parameters": {"strategy": spec.parameter_strategy},
            "route": {
                "pathMarkers": path_markers or list(spec.path_prefixes),
                "operationIdMarkers": list(spec.operation_tokens),
                "method": spec.method,
            },
        }

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

        segment_intent = OperationalRouteRegistryService.refinement_intent_by_route_segment().get(
            normalized_segment
        )

        if segment_intent and segment_intent != normalized_intent:
            normalized_segment = ""

        for route in OperationalRouteRegistryService.intent_bound_routes():
            binding = str(route.get("intentBinding") or "").strip().lower()

            if binding != normalized_intent:
                continue

            route_segment_spec = str(route.get("routeSegment") or "").strip().lower()

            if normalized_segment and route_segment_spec:
                if route_segment_spec != normalized_segment:
                    continue
            elif normalized_segment in ("inbound-invoice", "outbound-invoice"):
                continue

            selected = self._resolver.resolve_route_action(
                route,
                message,
                allowed_action_ids,
                identifier=product_code,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def select_by_route_segment(
        self,
        message: str,
        product_code: str,
        route_segment: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        normalized_segment = str(route_segment or "").strip().lower()

        if not normalized_segment or not str(product_code or "").strip():
            return None

        for route in OperationalRouteRegistryService.routes_by_segment(normalized_segment):
            selected = self._resolver.resolve_route_action(
                route,
                message,
                allowed_action_ids,
                identifier=product_code,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
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
            self._catalog.load_candidates(
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
            selected = self._resolver.resolve_route_action(
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

        return self._vocabulary.try_vocabulary_route(
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

            selected = self._vocabulary.try_vocabulary_route(
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

    def select_lmp(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        conversation_context: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        for route in OperationalRouteRegistryService.lmp_routes():
            selected = self._vocabulary.try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
                merge_date_parameters=merge_date_parameters,
                conversation_context=conversation_context,
            )

            if selected:
                return selected

        return None

    def select_product_with_code(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")
        route_segment_value = str(route_segment or "").strip().lower()
        bound_intent = str(intent or ChatProductQueryIntent.FULL).strip().lower()

        if route_segment_value:
            selected = self.select_by_route_segment(
                message,
                product_code,
                route_segment_value,
                allowed_action_ids,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if bound_intent == ChatProductQueryIntent.FULL:
            if not ChatProductQueryIntentService.has_actionable_product_route_intent(
                message,
                normalized=normalized,
            ):
                return None

            refined = ChatProductQueryIntentService.refine_operational_intent_from_full(
                message,
                normalized=normalized,
            )

            if refined != ChatProductQueryIntent.FULL:
                bound_intent = refined
        elif bound_intent == ChatProductQueryIntent.SALES:
            route_segment_value = route_segment_value or "sales"

            if route_segment_value in ("outbound-invoice", "inbound-invoice"):
                bound_intent = ChatProductQueryIntent.FULL

        if bound_intent != ChatProductQueryIntent.FULL:
            selected = self.select_by_intent(
                message,
                product_code,
                bound_intent,
                allowed_action_ids,
                route_segment=route_segment_value or None,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

            if (
                bound_intent == ChatProductQueryIntent.SALES
                and ChatProductQueryIntentService.extract_product_code(message)
            ):
                return None

            if bound_intent in {
                ChatProductQueryIntent.DESCRIPTION,
                ChatProductQueryIntent.ANALYSER,
            }:
                selected = self.select_by_intent(
                    message,
                    product_code,
                    ChatProductQueryIntent.ANALYSER,
                    allowed_action_ids,
                    candidates_loader=candidates_loader,
                )

                if selected:
                    return selected

        for route in OperationalRouteRegistryService.product_identifier_routes():
            selected = self._vocabulary.try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                identifier=product_code,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.is_product_overview_message(message):
            selected = self.select_by_intent(
                message,
                product_code,
                ChatProductQueryIntent.ANALYSER,
                allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def select_product_search(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        description_override: str | None = None,
    ) -> dict | None:
        from app.domain.services.chat_product_search_intent_service import (
            ChatProductSearchIntentService,
        )

        if not ChatProductSearchIntentService.looks_like_product_search(normalized):
            return None

        for route in OperationalRouteRegistryService.product_search_routes():
            selected = self._vocabulary.try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
                description_override=description_override,
            )

            if selected:
                return selected

        return None

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for route in OperationalRouteRegistryService.system_metadata_routes():
            selected = self._vocabulary.try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

