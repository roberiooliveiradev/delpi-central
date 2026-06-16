"""Fase ``sessionRefinement`` do registry — refinamentos, drawing e fast paths."""

from __future__ import annotations

from typing import Callable, Protocol

from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_presentation_detail_action_service import (
    ChatPresentationDetailActionService,
)
from app.domain.services.chat_product_description_resolution_service import (
    ChatProductDescriptionResolutionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.chat_sql_query_refinement_service import (
    ChatSqlQueryRefinementService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class _ProductSelector(Protocol):
    def __call__(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        *,
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
    ) -> dict | None: ...


class ExternalActionSessionRefinementPhaseService:
    """Executa ``sessionRefinement`` — antes das rotas operacionais no dispatchOrder."""

    def __init__(self, route_selection: ExternalActionRouteSelectionService) -> None:
        self._route_selection = route_selection

    def run(
        self,
        *,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
        select_product: _ProductSelector,
        candidates_loader: Callable[..., list[dict]],
        resolve_previous_external_action_id: Callable[..., str | None],
        clamp_max_depth_for_path: Callable[[int, str], int],
    ) -> dict | None:
        selected = self._try_drawing_analyser(
            message,
            allowed_action_ids=allowed_action_ids,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            select_product=select_product,
        )

        if selected:
            return selected

        selected = self._try_presentation_detail(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
        )

        if selected:
            return selected

        selected = self._try_operational_refinements(
            message,
            allowed_action_ids=allowed_action_ids,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            select_product=select_product,
            candidates_loader=candidates_loader,
            resolve_previous_external_action_id=resolve_previous_external_action_id,
            clamp_max_depth_for_path=clamp_max_depth_for_path,
        )

        if selected:
            return selected

        selected = self._try_system_metadata(
            message,
            normalized,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
        )

        if selected:
            return selected

        return self._try_early_product_search(
            message,
            normalized,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
        )

    def _try_drawing_analyser(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        conversation_context: str | None,
        previous_messages: list | None,
        memory_snapshot: dict | None,
        select_product: _ProductSelector,
    ) -> dict | None:
        if not ChatDrawingIntentService.is_drawing_analysis_request(message):
            return None

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if not product_code:
            return None

        return select_product(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=ChatProductQueryIntent.ANALYSER,
        )

    def _try_presentation_detail(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
        detail_plan = ChatPresentationDetailActionService.detect_plan(
            message,
            previous_messages=previous_messages,
        )

        if not detail_plan:
            return None

        return self._route_selection.select_presentation_detail(
            detail_plan,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

    def _try_operational_refinements(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        conversation_context: str | None,
        previous_messages: list | None,
        select_product: _ProductSelector,
        candidates_loader: Callable[..., list[dict]],
        resolve_previous_external_action_id: Callable[..., str | None],
        clamp_max_depth_for_path: Callable[[int, str], int],
    ) -> dict | None:
        refinement = ChatOperationalRefinementService.detect(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

        if not refinement:
            return None

        if refinement.kind in {"stock_refinement", "stock_reset"}:
            stock_path_fragment = (
                OperationalRouteRegistryService.route_path_marker_for_segment("stock")
                or "/stock"
            )
            previous_stock_action_id = resolve_previous_external_action_id(
                previous_messages,
                path_fragment=stock_path_fragment,
            )

            return select_product(
                message,
                str(refinement.product_code or ""),
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STOCK,
                preferred_action_id=previous_stock_action_id,
            )

        if refinement.kind in {"metric_refinement", "metric_reset"}:
            return self._route_selection.select_metric_refinement(
                message,
                refinement,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                candidates_loader=candidates_loader,
            )

        if refinement.kind == "pagination_refinement":
            return self._route_selection.select_pagination_refinement(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
                select_product=select_product,
            )

        if refinement.kind == "depth_refinement":
            return self._route_selection.select_depth_refinement(
                refinement,
                allowed_action_ids=allowed_action_ids,
                message=message,
                select_product=select_product,
                clamp_max_depth=clamp_max_depth_for_path,
            )

        return None

    def _try_system_metadata(
        self,
        message: str,
        normalized: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
        if not OperationalRouteMatcherService.looks_like_system_metadata_question(
            normalized
        ):
            return None

        if ChatProductQueryIntentService.extract_product_code(message):
            return None

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            message,
            previous_messages=previous_messages,
        ):
            return None

        return self._route_selection.select_system_metadata(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

    def _try_early_product_search(
        self,
        message: str,
        normalized: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
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
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        description_lookup = ChatProductDescriptionResolutionService.extract_description_query(
            message,
        )

        if not description_lookup:
            return None

        if ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
            message,
        ):
            return None

        resolved_from_history = ChatProductDescriptionResolutionService.resolve_code_from_history(
            description_lookup,
            previous_messages=previous_messages,
        )

        if resolved_from_history:
            return None

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return None

        return self._route_selection.select_product_search(
            message,
            normalized,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
            description_override=description_lookup,
        )
