"""Fallback semântico de rotas de produto — DOCIE Fase 4 (wrapper fino)."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.application.services.external_actions.external_action_product_route_ranking_service import (
    ExternalActionProductRouteRankingService,
)
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
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductRouteSelectionService:
    """Ranking legado para intent FULL; catálogo/parâmetros no catalog service."""

    HIERARCHICAL_PRODUCT_MAX_DEPTH = (
        ExternalActionProductRouteCatalogService.HIERARCHICAL_PRODUCT_MAX_DEPTH
    )

    def __init__(
        self,
        repository,
        *,
        catalog: ExternalActionProductRouteCatalogService | None = None,
        ranking: ExternalActionProductRouteRankingService | None = None,
        operational_route: ExternalActionOperationalRouteSelectionService | None = None,
    ) -> None:
        self.repository = repository
        self._catalog = catalog or ExternalActionProductRouteCatalogService(repository)
        self._ranking = ranking or ExternalActionProductRouteRankingService()
        self._operational_route = operational_route or ExternalActionOperationalRouteSelectionService(
            self._catalog
        )

    @classmethod
    def _clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        return ExternalActionProductRouteCatalogService.clamp_max_depth_for_path(
            value,
            path,
        )

    def select(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
        candidates_loader: Callable | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = self._catalog.load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

        if not candidates:
            return None

        route_segment_value = str(route_segment or "").strip().lower()

        if route_segment_value:
            selected = self._operational_route.select_by_route_segment(
                message,
                product_code,
                route_segment_value,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
            )

            if selected:
                return selected

        if intent == ChatProductQueryIntent.FULL and not route_segment:
            normalized = ChatMessageNormalizationService.normalize_for_matching(message or "")

            if not ChatProductQueryIntentService.has_actionable_product_route_intent(
                message,
                normalized=normalized,
            ):
                return None

        candidates = [
            action
            for action in candidates
            if action.get("method") == "GET"
        ] or candidates

        invoice_segment = str(route_segment or "").strip().lower()
        if invoice_segment in ("outbound-invoice", "inbound-invoice"):
            invoice_candidates = [
                action
                for action in candidates
                if f"/{invoice_segment}" in str(action.get("path") or "").lower()
            ]

            if invoice_candidates:
                candidates = invoice_candidates
            else:
                return None
        elif intent == ChatProductQueryIntent.SALES:
            sales_candidates = [
                action
                for action in candidates
                if ExternalActionProductRouteRankingService.is_product_sales_summary_path(
                    str(action.get("path") or "")
                )
            ]

            if not sales_candidates:
                return None

            candidates = sales_candidates
        else:
            candidates = [
                action
                for action in candidates
                if "search" not in str(action.get("path") or "").lower()
            ] or candidates

        ranked = self._ranking.rank_product_actions(
            candidates,
            intent=intent,
            message=message,
            route_segment=route_segment,
            allowed_action_ids=allowed_action_ids,
        )

        if preferred_action_id:
            preferred = next(
                (
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") == preferred_action_id
                ),
                None,
            )

            if preferred:
                ranked = [preferred, *[
                    action
                    for action in ranked
                    if str(action.get("actionId") or "") != preferred_action_id
                ]]

        for action in ranked:
            parameters = self._catalog.build_product_parameters(
                action,
                product_code,
                message=message,
                previous_messages=previous_messages,
            )

            if not parameters:
                continue

            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            if (
                ChatOperationalDateParameterService.action_requires_explicit_date(action)
                and not ChatOperationalDateParameterService.parameters_have_date(
                    action,
                    parameters,
                )
            ):
                continue

            path = str(action.get("path") or "").lower()
            if "/directives/" in path:
                reason = ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "productDirectives",
                )
            else:
                reason = ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "productOperational",
                )

            if branch_code := (
                ChatOperationalRefinementService.extract_branch_code(
                    ChatMessageNormalizationService.normalize_for_matching(message)
                )
            ):
                reason = ExternalActionResponseContentService.format(
                    "selectionReasons",
                    "productStockBranchRefinement",
                    product_code=product_code,
                    branch_code=branch_code,
                )

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": reason,
            }

        return None
