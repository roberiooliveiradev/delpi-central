"""Seleção de rotas de produto com código — motor operacional registry (DOCIE Fase 9)."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionProductRouteSelectionService:
    """Resolve rotas de produto via registry; catálogo/parâmetros no catalog service."""

    HIERARCHICAL_PRODUCT_MAX_DEPTH = (
        ExternalActionProductRouteCatalogService.HIERARCHICAL_PRODUCT_MAX_DEPTH
    )

    def __init__(
        self,
        repository,
        *,
        catalog: ExternalActionProductRouteCatalogService | None = None,
        operational_route: ExternalActionOperationalRouteSelectionService | None = None,
    ) -> None:
        self.repository = repository
        self._catalog = catalog or ExternalActionProductRouteCatalogService(repository)
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
        if preferred_action_id:
            preferred = self._select_preferred_action(
                message,
                product_code,
                allowed_action_ids,
                preferred_action_id=preferred_action_id,
                candidates_loader=candidates_loader,
                previous_messages=previous_messages,
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
        )

        if not selected:
            return None

        return self._apply_branch_reason(message, product_code, selected)

    def _select_preferred_action(
        self,
        message: str,
        product_code: str,
        allowed_action_ids: list[str],
        *,
        preferred_action_id: str,
        candidates_loader: Callable | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = self._catalog.load_candidates(
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

        parameters = self._catalog.build_product_parameters(
            action,
            product_code,
            message=message,
            previous_messages=previous_messages,
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
    def _apply_branch_reason(
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
