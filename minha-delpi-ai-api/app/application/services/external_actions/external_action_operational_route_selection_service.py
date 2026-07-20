"""Motor declarativo de fast paths — operational_route_registry (DOCIE Fase 0–3)."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.operational_route_selection.operational_route_action_resolver_service import (
    OperationalRouteActionResolverService,
)
from app.application.services.external_actions.operational_route_selection.operational_route_auto_tier_c_selection_service import (
    OperationalRouteAutoTierCSelectionService,
)
from app.application.services.external_actions.operational_route_selection.operational_route_domain_selection_service import (
    OperationalRouteDomainSelectionService,
)
from app.application.services.external_actions.operational_route_selection.operational_route_vocabulary_matcher_service import (
    OperationalRouteVocabularyMatcherService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ExternalActionOperationalRouteSelectionService:
    """Orquestra delegates de seleção operacional por registry."""

    def __init__(self, catalog) -> None:
        self._catalog = catalog
        self._resolver = OperationalRouteActionResolverService(catalog)
        self._vocabulary = OperationalRouteVocabularyMatcherService(catalog, self._resolver)
        self._domain = OperationalRouteDomainSelectionService(
            catalog,
            self._resolver,
            self._vocabulary,
        )
        self._auto_tier_c = OperationalRouteAutoTierCSelectionService(self._resolver)

    def select(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
        path_lookup_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        selected = self._domain.select_production_operational(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            path_lookup_loader=path_lookup_loader,
        )

        if selected:
            return selected

        for route in OperationalRouteRegistryService.vocabulary_routes():
            selected = self._vocabulary.try_vocabulary_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
                build_date_branch_parameters=build_date_branch_parameters,
                merge_date_parameters=merge_date_parameters,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        return None

    def select_auto_tier_c(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._auto_tier_c.select_auto_tier_c(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            rank_candidates=rank_candidates,
            build_date_branch_parameters=build_date_branch_parameters,
            previous_messages=previous_messages,
        )

    def select_by_department_kpi(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._domain.select_by_department_kpi(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            previous_messages=previous_messages,
        )

    def select_registry_route_id(
        self,
        route_id: str,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        """Resolve action pelo id do registry — ignora predicados ``match`` vocabulary."""
        route = OperationalRouteRegistryService.route_by_id(str(route_id or "").strip())

        if not route:
            return None

        return self._resolver.resolve_route_action(
            route,
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
        )

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
        return self._domain.select_by_intent(
            message,
            product_code,
            intent,
            allowed_action_ids,
            route_segment=route_segment,
            candidates_loader=candidates_loader,
        )

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
        return self._domain.select_by_route_segment(
            message,
            product_code,
            route_segment,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
        )

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
        return self._domain.select_production_operational(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            path_lookup_loader=path_lookup_loader,
        )

    def select_sale_orders(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        return self._domain.select_sale_orders(
            message,
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
        return self._domain.select_transforma(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
        )

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
        return self._domain.select_lmp(
            message,
            normalized,
            allowed_action_ids,
            conversation_context=conversation_context,
            candidates_loader=candidates_loader,
            merge_date_parameters=merge_date_parameters,
        )

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
        return self._domain.select_product_with_code(
            message,
            product_code,
            allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
        )

    def select_product_search(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        description_override: str | None = None,
    ) -> dict | None:
        return self._domain.select_product_search(
            message,
            normalized,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            description_override=description_override,
        )

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._domain.select_system_metadata(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
        )
