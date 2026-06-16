"""Despacho por intent em external_action_selection — Fase 3B lote 23."""

from __future__ import annotations

from app.application.services.external_actions.external_action_registry_dispatch_phase_service import (
    ExternalActionRegistryDispatchPhaseService,
    RegistryDispatchCallbacks,
    RegistryDispatchContext,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.application.services.external_actions.external_action_selection_preflight_service import (
    ExternalActionSelectionPreflightService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


class ExternalActionSelectionDispatchService:
    def __init__(
        self,
        route_selection: ExternalActionRouteSelectionService,
        support: ExternalActionSelectionSupportService,
    ) -> None:
        self._route_selection = route_selection
        self._support = support
        self._registry_phases = ExternalActionRegistryDispatchPhaseService(route_selection)

    def dispatch(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        raw_message: str | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict | None:
        sql_source = str(raw_message or message).strip()

        if ExternalActionSelectionPreflightService.blocks_selection(
            message,
            previous_messages=previous_messages,
        ):
            return None

        sql_authoring = ExternalActionSelectionPreflightService.try_sql_authoring_system_metadata(
            message,
            route_selection=self._route_selection,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=self._list_allowed_candidates,
        )

        if sql_authoring != "skip":
            return sql_authoring

        selected = ExternalActionSelectionPreflightService.try_preflight_sql_policies(
            message,
            sql_source=sql_source,
            allowed_action_ids=allowed_action_ids,
            select_sql=self._select_sql_or_data_action,
        )

        if selected:
            return selected

        if ExternalActionSelectionPreflightService.blocks_sql_show_mode(
            message,
            previous_messages=previous_messages,
        ):
            return None

        selected = ExternalActionSelectionPreflightService.try_sql_refinement_execute(
            message,
            sql_source=sql_source,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            select_sql=self._select_sql_or_data_action,
        )

        if selected:
            return selected

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return self._registry_phases.run(
            RegistryDispatchContext(
                message=message,
                normalized=normalized,
                sql_source=sql_source,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                product_code=None,
                bound_product_intent=ChatProductQueryIntent.FULL,
                product_route_segment=None,
                memory_snapshot=memory_snapshot,
            ),
            callbacks=RegistryDispatchCallbacks(
                candidates_loader=self._list_allowed_candidates,
                build_date_branch_parameters=self._build_date_branch_parameters,
                merge_date_parameters=self._merge_date_parameters,
                path_lookup_loader=self._lookup_production_operational_actions,
                rank_candidates=self._rank_candidates,
                extract_sale_number=self._extract_sale_number,
                select_product=self._select_product_action,
                select_lmp=self._select_lmp_action,
                select_sql=self._select_sql_or_data_action,
                resolve_previous_external_action_id=self._support.resolve_previous_external_action_id,
                clamp_max_depth_for_path=self._clamp_max_depth_for_path,
            ),
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

    def _select_sql_or_data_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
        selection_reason_key: str | None = None,
        raw_message: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_sql(
            message,
            allowed_action_ids,
            sql=sql,
            selection_reason_key=selection_reason_key,
            raw_message=raw_message,
            candidates_loader=self._list_allowed_candidates,
            rank_candidates=self._rank_candidates,
        )

    def _select_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_product(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=self._list_allowed_candidates,
        )

    @staticmethod
    def _clamp_max_depth_for_path(value: int, path: str) -> int:
        return ExternalActionRouteSelectionService.clamp_max_depth_for_path(value, path)

    def _select_lmp_action(
        self,
        message: str,
        allowed_action_ids: list[str],
        conversation_context: str | None = None,
    ) -> dict | None:
        return self._route_selection.select_lmp(
            message,
            allowed_action_ids,
            conversation_context=conversation_context,
            candidates_loader=self._list_allowed_candidates,
            merge_date_parameters=self._merge_date_parameters,
        )

    def _extract_sale_number(self, text: str | None) -> str | None:
        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        return OperationalRouteMatcherService.extract_lmp_sale_number(text)

    def _merge_date_parameters(
        self,
        action: dict,
        message: str,
        parameters: dict,
        *,
        previous_messages: list | None = None,
    ) -> dict:
        return self._route_selection.parameter_builder.merge_date_range(
            action,
            message,
            parameters,
            previous_messages=previous_messages,
        )

    def _lookup_production_operational_actions(
        self,
        *,
        path_token: str,
        allowed_action_ids: list[str],
    ) -> list[dict]:
        return self._support.find_allowed_actions_by_path_token(
            path_token=path_token,
            operation_token="",
            allowed_action_ids=allowed_action_ids,
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

    def _rank_candidates(
        self,
        message: str,
        candidates: list[dict],
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        return self._support.rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed_action_ids,
        )
