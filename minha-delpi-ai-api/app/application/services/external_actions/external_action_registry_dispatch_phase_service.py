"""Loop declarativo de fases DOCIE — operational_route_registry.dispatchOrder (Fase 8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_heuristics_service import (
    ExternalActionSelectionHeuristicsService,
)
from app.application.services.external_actions.external_action_sql_fallback_policy_service import (
    ExternalActionSqlFallbackPolicyService,
    SqlFallbackRunState,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
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
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
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


@dataclass(frozen=True)
class RegistryDispatchContext:
    message: str
    normalized: str
    sql_source: str
    allowed_action_ids: list[str]
    conversation_context: str | None
    previous_messages: list | None
    product_code: str | None
    bound_product_intent: str
    product_route_segment: str | None


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


class _LmpSelector(Protocol):
    def __call__(
        self,
        message: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
    ) -> dict | None: ...


class _SqlSelector(Protocol):
    def __call__(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
        selection_reason_key: str | None = None,
        raw_message: str | None = None,
    ) -> dict | None: ...


@dataclass(frozen=True)
class RegistryDispatchCallbacks:
    candidates_loader: Callable[..., list[dict]]
    build_date_branch_parameters: Callable[..., dict]
    merge_date_parameters: Callable[..., dict]
    path_lookup_loader: Callable[..., list[dict]]
    rank_candidates: Callable[..., list[dict]]
    extract_sale_number: Callable[[str | None], str | None]
    select_product: _ProductSelector
    select_lmp: _LmpSelector
    select_sql: _SqlSelector


class ExternalActionRegistryDispatchPhaseService:
    """Executa fases registry na ordem de ``dispatchOrder``."""

    def __init__(self, route_selection: ExternalActionRouteSelectionService) -> None:
        self._route_selection = route_selection

    def run(
        self,
        ctx: RegistryDispatchContext,
        *,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        handlers = {
            "productionOperational": lambda state: self._phase_production_operational(
                ctx,
                callbacks,
                state=state,
            ),
            "operationalRoutes": lambda state: self._phase_operational_routes(
                ctx,
                callbacks,
            ),
            "intentBoundRoutes": lambda state: self._phase_intent_bound_routes(
                ctx,
                callbacks,
            ),
            "domainRoutes": lambda state: self._phase_domain_routes(ctx, callbacks),
            "sqlFallback": lambda state: self._phase_sql_fallback(
                ctx,
                callbacks,
                state=state,
            ),
            "semanticFallback": lambda state: self._phase_semantic_fallback(
                ctx,
                callbacks,
            ),
        }

        state = SqlFallbackRunState()

        for phase in OperationalRouteRegistryService.dispatch_order():
            if phase == "sessionRefinement":
                continue

            handler = handlers.get(phase)

            if not handler:
                continue

            selected = handler(state)

            if selected:
                return selected

            if state.abort_remaining:
                return None

        return None

    def _phase_production_operational(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
        *,
        state: SqlFallbackRunState,
    ) -> dict | None:
        if not ChatProductionOperationalIntentService.matches_rest_route(ctx.message):
            return None

        selected = self._route_selection.select_production_operational(
            ctx.message,
            allowed_action_ids=ctx.allowed_action_ids,
            previous_messages=ctx.previous_messages,
            candidates_loader=callbacks.candidates_loader,
            build_date_branch_parameters=callbacks.build_date_branch_parameters,
            path_lookup_loader=callbacks.path_lookup_loader,
        )

        if selected:
            return selected

        for policy in OperationalRouteRegistryService.fallback_policies_for_phase(
            "productionOperational"
        ):
            selected = ExternalActionSqlFallbackPolicyService.try_policy(
                policy,
                message=ctx.message,
                sql_source=ctx.sql_source,
                allowed_action_ids=ctx.allowed_action_ids,
                select_sql=callbacks.select_sql,
                after_rest_miss=True,
                state=state,
            )

            if selected:
                return selected

        return None

    def _phase_operational_routes(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        return self._route_selection.select_operational_registry(
            ctx.message,
            ctx.normalized,
            ctx.allowed_action_ids,
            candidates_loader=callbacks.candidates_loader,
            build_date_branch_parameters=callbacks.build_date_branch_parameters,
            merge_date_parameters=callbacks.merge_date_parameters,
            previous_messages=ctx.previous_messages,
        )

    def _phase_intent_bound_routes(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        if not ctx.product_code:
            return None

        if ctx.bound_product_intent not in _INTENT_BOUND_PRODUCT_INTENTS:
            return self._phase_product_semantic_ranking(ctx, callbacks)

        route_segment = ctx.product_route_segment
        bound_intent = ctx.bound_product_intent

        if ctx.bound_product_intent == ChatProductQueryIntent.SALES:
            route_segment = ctx.product_route_segment or "sales"

            if route_segment in ("outbound-invoice", "inbound-invoice"):
                bound_intent = ChatProductQueryIntent.FULL

        selected = self._route_selection.select_intent_bound_route(
            ctx.message,
            ctx.product_code,
            intent=bound_intent,
            allowed_action_ids=ctx.allowed_action_ids,
            route_segment=route_segment,
            candidates_loader=callbacks.candidates_loader,
        )

        if selected:
            return selected

        if (
            ctx.bound_product_intent == ChatProductQueryIntent.SALES
            and ChatProductQueryIntentService.extract_product_code(ctx.message)
        ):
            return None

        return self._phase_product_semantic_ranking(ctx, callbacks)

    def _phase_product_semantic_ranking(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        if not ctx.product_code:
            return None

        if not (
            ExternalActionSelectionHeuristicsService.looks_like_product_question(
                ctx.normalized
            )
            or ChatProductQueryIntentService.extract_product_code(ctx.message)
            or ctx.product_route_segment
            or ChatProductDescriptionResolutionService.looks_like_description_lookup(
                ctx.message
            )
        ):
            return None

        resolved_intent = (
            ctx.bound_product_intent
            if ctx.bound_product_intent != ChatProductQueryIntent.FULL
            else ChatProductQueryIntent.FULL
        )

        return callbacks.select_product(
            ctx.message,
            ctx.product_code,
            ctx.allowed_action_ids,
            intent=resolved_intent,
            route_segment=ctx.product_route_segment,
        )

    def _phase_domain_routes(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        selected = self._route_selection.select_department_kpi(
            ctx.message,
            allowed_action_ids=ctx.allowed_action_ids,
            candidates_loader=callbacks.candidates_loader,
            build_date_branch_parameters=callbacks.build_date_branch_parameters,
            previous_messages=ctx.previous_messages,
        )

        if selected:
            return selected

        selected = self._route_selection.select_lmp(
            ctx.message,
            ctx.allowed_action_ids,
            conversation_context=ctx.conversation_context,
            candidates_loader=callbacks.candidates_loader,
            merge_date_parameters=callbacks.merge_date_parameters,
        )

        if selected:
            return selected

        if not ctx.product_code:
            selected = self._route_selection.select_kpi_without_product(
                ctx.message,
                ctx.normalized,
                allowed_action_ids=ctx.allowed_action_ids,
                previous_messages=ctx.previous_messages,
                candidates_loader=callbacks.candidates_loader,
            )

            if selected:
                return selected

        return None

    def _phase_sql_fallback(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
        *,
        state: SqlFallbackRunState,
    ) -> dict | None:
        for policy in OperationalRouteRegistryService.fallback_policies_for_phase(
            "sqlFallback"
        ):
            selected = ExternalActionSqlFallbackPolicyService.try_policy(
                policy,
                message=ctx.message,
                sql_source=ctx.sql_source,
                allowed_action_ids=ctx.allowed_action_ids,
                select_sql=callbacks.select_sql,
                state=state,
            )

            if selected:
                return selected

            if state.abort_remaining:
                return None

        return None

    def _phase_semantic_fallback(
        self,
        ctx: RegistryDispatchContext,
        callbacks: RegistryDispatchCallbacks,
    ) -> dict | None:
        if (
            not ctx.product_code
            and ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
                ctx.normalized
            )
            and not ChatProductionOperationalIntentService.matches_rest_route(ctx.message)
        ):
            selected = self._route_selection.select_product_search(
                ctx.message,
                ctx.normalized,
                allowed_action_ids=ctx.allowed_action_ids,
                candidates_loader=callbacks.candidates_loader,
            )

            if selected:
                return selected

        if ChatOperationalParameterService.should_block_semantic_action_fallback(
            ctx.message,
            conversation_context=ctx.conversation_context,
        ):
            return None

        return self._route_selection.select_generic(
            ctx.message,
            allowed_action_ids=ctx.allowed_action_ids,
            previous_messages=ctx.previous_messages,
            candidates_loader=callbacks.candidates_loader,
            rank_candidates=callbacks.rank_candidates,
            build_date_branch_parameters=callbacks.build_date_branch_parameters,
        )
