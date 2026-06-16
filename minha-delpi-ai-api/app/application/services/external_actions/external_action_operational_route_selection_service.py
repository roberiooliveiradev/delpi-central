"""Motor declarativo de fast paths — operational_route_registry (DOCIE Fase 0–1)."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ExternalActionOperationalRouteSelectionService:
    def __init__(self, product_route) -> None:
        self._product_route = product_route

    def select(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        for route in OperationalRouteRegistryService.routes():
            selected = self._try_route(
                route,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def _try_route(
        self,
        route: dict,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        match_spec = route.get("match")

        if not isinstance(match_spec, dict):
            return None

        if not OperationalRouteMatcherService.matches(
            match_spec,
            message=message,
            normalized=normalized,
        ):
            return None

        route_spec = route.get("route")

        if not isinstance(route_spec, dict):
            return None

        path_markers = [
            str(marker).lower()
            for marker in (route_spec.get("pathMarkers") or [])
            if str(marker).strip()
        ]
        operation_markers = [
            str(marker).lower()
            for marker in (route_spec.get("operationIdMarkers") or [])
            if str(marker).strip()
        ]

        if not path_markers and not operation_markers:
            return None

        identifier = None
        match_spec = route.get("match") or {}

        if match_spec.get("requiresProductIdentifier"):
            identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return None

        candidates = self._product_route._find_allowed_actions_by_markers(
            path_markers=path_markers,
            operation_markers=operation_markers,
            allowed_action_ids=allowed_action_ids,
        )

        if not candidates:
            candidates = self._product_route._load_candidates(
                message,
                allowed_action_ids=allowed_action_ids,
                candidates_loader=candidates_loader,
            )

        expected_method = str(route_spec.get("method") or "GET").upper()

        for action in candidates:
            if str(action.get("method") or "GET").upper() != expected_method:
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if path_markers and not any(marker in path for marker in path_markers):
                continue

            if operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                if path_markers:
                    continue

            if not path_markers and operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                continue

            parameters = self._build_parameters(
                route,
                action,
                message=message,
                normalized=normalized,
                identifier=identifier,
            )

            if not parameters:
                continue

            presentation = route.get("presentation") or {}
            reason_key = str(presentation.get("reasonKey") or route.get("id") or "").strip()

            if not reason_key:
                continue

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

        return None

    def _build_parameters(
        self,
        route: dict,
        action: dict,
        *,
        message: str,
        normalized: str,
        identifier: str | None,
    ) -> dict | None:
        parameters_spec = route.get("parameters") or {}
        strategy = str(parameters_spec.get("strategy") or "").strip()

        if strategy == "product_code":
            if not identifier:
                identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return None

            return self._product_route._build_product_parameters(
                action,
                identifier,
                message=message,
            )

        if strategy == "exclusive_catalog":
            return self._product_route._build_exclusive_catalog_parameters(
                action,
                message=message,
                normalized=normalized,
            )

        return None
