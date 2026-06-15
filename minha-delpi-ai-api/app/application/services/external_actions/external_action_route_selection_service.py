"""Seleção unificada de actions OpenAPI a partir de OperationalApiRouteSpec."""

from __future__ import annotations

from typing import Callable

from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
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
from app.application.services.external_actions.external_action_lmp_route_selection_service import (
    ExternalActionLmpRouteSelectionService,
)
from app.application.services.external_actions.external_action_sql_route_selection_service import (
    ExternalActionSqlRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_selection_service import (
    ExternalActionProductRouteSelectionService,
)
from app.application.services.external_actions.external_action_kpi_route_selection_service import (
    ExternalActionKpiRouteSelectionService,
)
from app.application.services.external_actions.external_action_domain_route_selection_service import (
    ExternalActionDomainRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_refinement_route_selection_service import (
    ExternalActionRefinementRouteSelectionService,
)
from app.application.services.external_actions.external_action_generic_route_selection_service import (
    ExternalActionGenericRouteSelectionService,
)
from app.application.services.external_actions.external_action_production_operational_route_selection_service import (
    ExternalActionProductionOperationalRouteSelectionService,
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
        product_route: ExternalActionProductRouteSelectionService | None = None,
        lmp_route: ExternalActionLmpRouteSelectionService | None = None,
        sql_route: ExternalActionSqlRouteSelectionService | None = None,
        kpi_route: ExternalActionKpiRouteSelectionService | None = None,
        domain_route: ExternalActionDomainRouteSelectionService | None = None,
        product_search_route: ExternalActionProductSearchRouteSelectionService | None = None,
        refinement_route: ExternalActionRefinementRouteSelectionService | None = None,
        generic_route: ExternalActionGenericRouteSelectionService | None = None,
        production_operational_route: ExternalActionProductionOperationalRouteSelectionService | None = None,
    ):
        self.repository = repository
        self.parameter_builder = parameter_builder or OperationalApiParameterBuilderService()
        self._product_route = product_route or ExternalActionProductRouteSelectionService(
            repository
        )
        self._lmp_route = lmp_route or ExternalActionLmpRouteSelectionService(repository)
        self._sql_route = sql_route or ExternalActionSqlRouteSelectionService(repository)
        self._kpi_route = kpi_route or ExternalActionKpiRouteSelectionService(self)
        self._domain_route = domain_route or ExternalActionDomainRouteSelectionService(
            repository
        )
        self._product_search_route = (
            product_search_route or ExternalActionProductSearchRouteSelectionService()
        )
        self._refinement_route = refinement_route or ExternalActionRefinementRouteSelectionService(
            repository
        )
        self._generic_route = generic_route or ExternalActionGenericRouteSelectionService()
        self._production_operational_route = (
            production_operational_route
            or ExternalActionProductionOperationalRouteSelectionService()
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

        if spec.prioritize == "supplies_otd":
            candidates = self._prioritize_supplies_otd_candidates(message, candidates)

        candidates = self._prioritize_production_otd_detail_candidates(message, candidates)
        candidates = self._prioritize_production_oee_appointment_candidates(message, candidates)
        candidates = self._prioritize_production_oee_detail_candidates(message, candidates)

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
    ) -> dict | None:
        return self._product_route.select(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
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
        return self._lmp_route.select(
            message,
            allowed_action_ids,
            conversation_context,
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
        return self._kpi_route.try_select_without_product_code(
            message,
            normalized,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
        )

    def select_metric_refinement(
        self,
        message: str,
        refinement,
        *,
        allowed_action_ids: list[str],
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._kpi_route.select_metric_refinement(
            message,
            refinement,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
        )

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

        return self._domain_route.select_sale_orders(
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

        return self._domain_route.select_transforma(
            message,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            previous_messages=previous_messages,
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

        return self._domain_route.select_system_metadata(
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

        return self._product_search_route.select(
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
        return self._production_operational_route.try_select(
            message,
            allowed_action_ids=allowed_action_ids,
            previous_messages=previous_messages,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            path_lookup_loader=path_lookup_loader,
        )

    def select_exclusive_raw_material_catalog(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        return self._product_route.select_exclusive_raw_material_catalog(
            message,
            normalized,
            allowed_action_ids,
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

    @classmethod
    def clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        return ExternalActionProductRouteSelectionService._clamp_max_depth_for_path(
            value,
            path,
        )

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

    def _prioritize_supplies_otd_candidates(
        self,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        supplies_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "suppliesOtdSuppliesDomainTerms",
        )
        supplies_prefix = ExternalActionResponseContentService.get(
            "actionSelection",
            "suppliesOtdPathPrefix",
            default="/supplies/",
        ).lower()

        if any(term in normalized for term in supplies_terms):
            supplies = [
                action
                for action in candidates
                if supplies_prefix in str(action.get("path") or "").lower()
            ]

            if supplies:
                return supplies

        production_terms = ("producao", "produção", "fabril", "manufatura")
        commercial_terms = ("comercial", "venda", "pedido de venda")

        if any(term in normalized for term in production_terms):
            production = [
                action
                for action in candidates
                if "/production/" in str(action.get("path") or "").lower()
            ]

            if production:
                return production

        if any(term in normalized for term in commercial_terms):
            commercial = [
                action
                for action in candidates
                if "/commercial/" in str(action.get("path") or "").lower()
            ]

            if commercial:
                return commercial

        return candidates

    def _prioritize_production_otd_detail_candidates(
        self,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        detail_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOtdDetailTerms",
        )
        production_terms = ("producao", "produção", "fabril", "manufatura", "op ", "ops")

        if not any(term in normalized for term in detail_terms):
            return candidates
        if not any(term in normalized for term in production_terms):
            return candidates

        detail_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOtdDetailPath",
            default="/production/otd",
        ).lower()
        detail_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOtdDetailOperationId",
            default="get_production_otd",
        ).lower()

        detail_actions = [
            action
            for action in candidates
            if (
                str(action.get("path") or "").lower().rstrip("/") == detail_path.rstrip("/")
                or detail_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return detail_actions or candidates

    def _prioritize_production_oee_appointment_candidates(
        self,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        appointment_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeAppointmentTerms",
        )
        oee_terms = ("oee", "eficiencia", "eficiência", "equipamento", "equipamentos", "zefici")
        appointment_context_terms = ("apontamento", "apontamentos", "sh6010", "h6_zefici")

        if not any(term in normalized for term in appointment_terms):
            return candidates
        if not any(term in normalized for term in oee_terms):
            if not any(term in normalized for term in appointment_context_terms):
                return candidates

        appointment_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeAppointmentPath",
            default="/production/oee/appointments/",
        ).lower()
        appointment_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeAppointmentOperationId",
            default="get_production_oee_appointment_by_id",
        ).lower()

        appointment_actions = [
            action
            for action in candidates
            if (
                appointment_path.rstrip("/")
                in str(action.get("path") or "").lower().rstrip("/")
                or appointment_operation
                in str(action.get("operationId") or "").lower()
            )
        ]

        return appointment_actions or candidates

    def _prioritize_production_oee_detail_candidates(
        self,
        message: str,
        candidates: list[dict],
    ) -> list[dict]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        detail_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productionOeeDetailTerms",
        )
        oee_terms = ("oee", "eficiencia", "eficiência", "equipamento", "equipamentos", "zefici")

        if not any(term in normalized for term in detail_terms):
            return candidates
        if not any(term in normalized for term in oee_terms):
            return candidates

        detail_path = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeDetailPath",
            default="/production/oee",
        ).lower()
        detail_operation = ExternalActionResponseContentService.get(
            "actionSelection",
            "productionOeeDetailOperationId",
            default="get_production_oee",
        ).lower()

        detail_actions = [
            action
            for action in candidates
            if (
                str(action.get("path") or "").lower().rstrip("/") == detail_path.rstrip("/")
                or detail_operation in str(action.get("operationId") or "").lower()
            )
        ]

        return detail_actions or candidates
