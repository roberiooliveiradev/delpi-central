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
from app.application.services.external_actions.external_action_product_route_selection_service import (
    ExternalActionProductRouteSelectionService,
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
    ):
        self.repository = repository
        self.parameter_builder = parameter_builder or OperationalApiParameterBuilderService()
        self._product_route = product_route or ExternalActionProductRouteSelectionService(
            repository
        )
        self._lmp_route = lmp_route or ExternalActionLmpRouteSelectionService(repository)

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
    ) -> dict | None:
        return self._product_route.select(
            message,
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
            route_segment=route_segment,
            preferred_action_id=preferred_action_id,
            candidates_loader=candidates_loader,
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
