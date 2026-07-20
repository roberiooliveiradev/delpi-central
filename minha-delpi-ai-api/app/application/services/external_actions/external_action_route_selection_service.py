"""Seleção unificada de actions OpenAPI a partir de OperationalApiRouteSpec."""

from __future__ import annotations

from typing import Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_operational_api_domain_service import (
    ChatOperationalApiDomainService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.operational_api_parameter_builder_service import (
    OperationalApiParameterBuilderService,
)
from app.application.services.external_actions.external_action_candidate_prioritization_service import (
    ExternalActionCandidatePrioritizationService,
)
from app.application.services.external_actions.external_action_sql_route_selection_service import (
    ExternalActionSqlRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.application.services.external_actions.external_action_refinement_route_selection_service import (
    ExternalActionRefinementRouteSelectionService,
)
from app.application.services.external_actions.external_action_generic_route_selection_service import (
    ExternalActionGenericRouteSelectionService,
)
from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


class ExternalActionRouteSelectionService:
    """Ponto único para resolver action + parâmetros, qualquer domínio operacional."""

    def __init__(
        self,
        repository,
        *,
        parameter_builder: OperationalApiParameterBuilderService | None = None,
        sql_route: ExternalActionSqlRouteSelectionService | None = None,
        refinement_route: ExternalActionRefinementRouteSelectionService | None = None,
        generic_route: ExternalActionGenericRouteSelectionService | None = None,
    ):
        self.repository = repository
        self.parameter_builder = parameter_builder or OperationalApiParameterBuilderService()
        self._product_catalog = ExternalActionProductRouteCatalogService(repository)
        self._sql_route = sql_route or ExternalActionSqlRouteSelectionService(repository)
        self._refinement_route = refinement_route or ExternalActionRefinementRouteSelectionService(
            repository
        )
        self._generic_route = generic_route or ExternalActionGenericRouteSelectionService()
        self._operational_route = ExternalActionOperationalRouteSelectionService(
            self._product_catalog
        )

    def select(
        self,
        spec: OperationalApiRouteSpec,
        *,
        message: str,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        fallback_candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        method = spec.method or ChatOperationalApiDomainService.method_for_domain(spec.domain)
        candidates = self._find_candidates(
            spec,
            allowed_action_ids=allowed_action_ids,
            method=method,
        )

        if not candidates and fallback_candidates_loader:
            candidates = fallback_candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            candidates = self._filter_candidates(spec, candidates)

        candidates = ExternalActionCandidatePrioritizationService.apply(
            message,
            candidates,
            supplies_otd=spec.prioritize == "supplies_otd",
        )

        for action in candidates:
            if str(action.get("method") or "").upper() != method.upper():
                continue

            parameters = self.parameter_builder.build(
                spec,
                action,
                message,
                previous_messages=previous_messages,
                product_builder=None,
            )

            return {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": action["actionId"],
                    "parameters": parameters,
                },
                "reason": spec.reason,
            }

        return None

    def select_product(
        self,
        message: str,
        product_code: str,
        *,
        allowed_action_ids: list[str],
        intent: str = ChatProductQueryIntent.FULL,
        route_segment: str | None = None,
        preferred_action_id: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict | None:
        if preferred_action_id:
            preferred = self._select_preferred_product_action(
                message,
                product_code,
                allowed_action_ids,
                preferred_action_id=preferred_action_id,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
                drawing_analysis_mode=drawing_analysis_mode,
                attachment_ids=attachment_ids,
            )

            if preferred:
                return preferred

        selected = self._operational_route.select_product_with_code(
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

        if not selected:
            return None

        return self._apply_product_branch_reason(message, product_code, selected)

    def build_product_parameters(
        self,
        action: dict,
        code: str,
        *,
        message: str | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict:
        return self._product_catalog.build_product_parameters(
            action,
            code,
            message=message,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
        )

    def select_lmp(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        conversation_context: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return self._operational_route.select_lmp(
            message,
            normalized,
            allowed_action_ids,
            conversation_context=conversation_context,
            candidates_loader=candidates_loader,
            merge_date_parameters=merge_date_parameters,
        )

    def select_sql(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        sql: str | None = None,
        selection_reason_key: str | None = None,
        raw_message: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._sql_route.select(
            message,
            allowed_action_ids,
            sql=sql,
            selection_reason_key=selection_reason_key,
            raw_message=raw_message,
            candidates_loader=candidates_loader,
            rank_candidates=rank_candidates,
        )

    def select_kpi_without_product(
        self,
        message: str,
        normalized: str,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return None

    def select_metric_refinement(
        self,
        message: str,
        refinement,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if refinement.metric_kind == "supplies" and refinement.metric_path_token:
            spec = OperationalApiRouteSpec.from_supplies_metric(
                path_token=str(refinement.metric_path_token),
                operation_token=str(refinement.metric_path_token),
                reason=refinement.reason
                or ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "kpiMetricRefinementDefault",
                ),
            )

            return self.select(
                spec,
                message=message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                fallback_candidates_loader=candidates_loader,
            )

        if refinement.metric_kind == "department_kpi" and refinement.metric_path_token:
            from app.domain.services.chat_department_kpi_intent_service import (
                DepartmentKpiMatch,
            )

            match = DepartmentKpiMatch(
                path_token=str(refinement.metric_path_token),
                domain_prefix=str(refinement.metric_domain_prefix or ""),
                reason=refinement.reason
                or ExternalActionResponseContentService.get(
                    "selectionReasons",
                    "departmentKpiRefinement",
                ),
            )

            return self.select(
                OperationalApiRouteSpec.from_department_kpi(match),
                message=message,
                allowed_action_ids=allowed_action_ids,
                previous_messages=previous_messages,
                fallback_candidates_loader=candidates_loader,
            )

        return None

    def select_sale_orders(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        if not candidates_loader or not merge_date_parameters:
            return None

        return self._operational_route.select_sale_orders(
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
        if not candidates_loader or not build_date_branch_parameters:
            return None

        return self._operational_route.select_transforma(
            message,
            allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
        )

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        if not candidates_loader:
            return None

        return self._operational_route.select_system_metadata(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
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
        if not candidates_loader:
            return None

        return self._operational_route.select_product_search(
            message,
            normalized,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            description_override=description_override,
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
        return self._operational_route.select_production_operational(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            path_lookup_loader=path_lookup_loader,
        )

    def select_department_kpi(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._operational_route.select_by_department_kpi(
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
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._operational_route.select_registry_route_id(
            route_id,
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            previous_messages=previous_messages,
        )

    def select_operational_registry(
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
        return self._operational_route.select(
            message,
            normalized,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            previous_messages=previous_messages,
            path_lookup_loader=path_lookup_loader,
        )

    def select_intent_bound_route(
        self,
        message: str,
        product_code: str,
        *,
        intent: str,
        allowed_action_ids: list[str],
        route_segment: str | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._operational_route.select_by_intent(
            message,
            product_code,
            intent,
            allowed_action_ids,
            route_segment=route_segment,
            candidates_loader=candidates_loader,
        )

    def select_pagination_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
        select_product: Callable[..., dict | None] | None = None,
    ) -> dict | None:
        return self._refinement_route.select_pagination(
            refinement,
            allowed_action_ids=allowed_action_ids,
            message=message,
            select_product=select_product,
        )

    def select_operational_group_by_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
    ) -> dict | None:
        return self._refinement_route.select_operational_group_by(
            refinement,
            allowed_action_ids=allowed_action_ids,
        )

    def select_depth_refinement(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
        select_product: Callable[..., dict | None] | None = None,
        clamp_max_depth: Callable[[int, str], int] | None = None,
    ) -> dict | None:
        return self._refinement_route.select_depth(
            refinement,
            allowed_action_ids=allowed_action_ids,
            message=message,
            select_product=select_product,
            clamp_max_depth=clamp_max_depth,
        )

    def select_presentation_detail(
        self,
        plan,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._refinement_route.select_presentation_detail(
            plan,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )

    def select_generic(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        return self._generic_route.select(
            message,
            allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            rank_candidates=rank_candidates,
            build_date_branch_parameters=build_date_branch_parameters,
        )

    def select_auto_tier_c(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        return self._operational_route.select_auto_tier_c(
            message,
            allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            rank_candidates=rank_candidates,
            build_date_branch_parameters=build_date_branch_parameters,
        )

    @classmethod
    def clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        return ExternalActionProductRouteCatalogService.clamp_max_depth_for_path(
            value,
            path,
        )

    def _select_preferred_product_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        *,
        preferred_action_id: str,
        candidates_loader: Callable | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict | None:
        candidates = self._product_catalog.load_candidates(
            message,
            allowed_action_ids=allowed_action_ids,
            candidates_loader=candidates_loader,
        )
        action = next(
            (
                item
                for item in candidates
                if str(item.get("actionId") or "") == preferred_action_id
            ),
            None,
        )

        if not action or str(action.get("method") or "GET").upper() != "GET":
            return None

        parameters = self._product_catalog.build_product_parameters(
            action,
            product_code,
            message=message,
            previous_messages=previous_messages,
            drawing_analysis_mode=drawing_analysis_mode,
            attachment_ids=attachment_ids,
        )

        if not parameters:
            return None

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
            return None

        path = str(action.get("path") or "").lower()
        reason_key = (
            "productDirectives"
            if "/directives/" in path
            else "productOperational"
        )

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

    @staticmethod
    def _apply_product_branch_reason(
        message: str,
        product_code: str,
        selected: dict,
    ) -> dict:
        branch_code = ChatOperationalRefinementService.extract_branch_code(
            ChatMessageNormalizationService.normalize_for_matching(message)
        )

        if not branch_code:
            return selected

        return {
            **selected,
            "reason": ExternalActionResponseContentService.format(
                "selectionReasons",
                "productStockBranchRefinement",
                product_code=product_code,
                branch_code=branch_code,
            ),
        }

    def _find_candidates(
        self,
        spec: OperationalApiRouteSpec,
        *,
        allowed_action_ids: list[str],
        method: str,
    ) -> list[dict]:
        allowed = {str(item) for item in allowed_action_ids}

        if not allowed:
            return []

        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        matches: list[dict] = []

        for action in list_actions():
            if str(action.get("actionId")) not in allowed:
                continue

            if str(action.get("method") or "").upper() != method.upper():
                continue

            if self._action_matches_spec(action, spec):
                matches.append(action)

        return matches

    def _filter_candidates(
        self,
        spec: OperationalApiRouteSpec,
        candidates: list[dict],
    ) -> list[dict]:
        return [
            action
            for action in candidates
            if self._action_matches_spec(action, spec)
        ]

    def _action_matches_spec(self, action: dict, spec: OperationalApiRouteSpec) -> bool:
        path = str(action.get("path") or "").lower()
        operation_id = str(action.get("operationId") or "").lower()

        if spec.path_prefixes and not any(prefix in path for prefix in spec.path_prefixes):
            return False

        path_tokens = [token for token in spec.path_tokens if token]
        operation_tokens = [token for token in spec.operation_tokens if token]

        if not path_tokens and not operation_tokens:
            return ChatOperationalApiDomainService.classify_path(path) == spec.domain

        if path_tokens and any(token in path for token in path_tokens):
            return True

        if operation_tokens and any(token in operation_id for token in operation_tokens):
            return True

        if path_tokens and any(
            token.replace("-", "_") in operation_id for token in path_tokens
        ):
            return True

        return not path_tokens and not operation_tokens
