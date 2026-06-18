"""Diagnóstico quando intent Playbook produto bate mas nenhuma action REST é selecionada."""

from __future__ import annotations

from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.external_actions.external_action_selection_support_service import (
    ExternalActionSelectionSupportService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ChatPlaybookProductActionReadinessService:
    @classmethod
    def matches_playbook_product_intent(cls, message: str | None) -> bool:
        return cls.resolve_playbook_route(message) is not None

    @classmethod
    def resolve_playbook_route(cls, message: str | None) -> dict | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        playbook_predicates = set(OperationalRouteRegistryService.playbook_product_predicates())

        for route in OperationalRouteRegistryService.routes():
            match_spec = route.get("match")

            if not isinstance(match_spec, dict):
                continue

            predicate = str(match_spec.get("customPredicate") or "").strip()

            if predicate not in playbook_predicates:
                continue

            if OperationalRouteMatcherService.matches(
                match_spec,
                message=message or "",
                normalized=normalized,
            ):
                return route

        return None

    @classmethod
    def resolve_gap_direct_answer(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str],
        repository,
        provider_key: str = "api-delpi",
    ) -> str | None:
        route = cls.resolve_playbook_route(message)

        if not route:
            return None

        route_spec = route.get("route") or {}
        path_markers = [
            str(marker).strip()
            for marker in (route_spec.get("pathMarkers") or [])
            if str(marker).strip()
        ]
        operation_markers = [
            str(marker).strip()
            for marker in (route_spec.get("operationIdMarkers") or [])
            if str(marker).strip()
        ]

        path_token = path_markers[0] if path_markers else ""
        operation_token = operation_markers[0] if operation_markers else ""

        if not path_token and not operation_token:
            return None

        support = ExternalActionSelectionSupportService(repository)
        catalog_actions = support.find_catalog_actions_by_path_token(
            path_token=path_token,
            operation_token=operation_token,
            provider_key=provider_key,
            method=str(route_spec.get("method") or "GET"),
        )

        path_label = path_token or operation_token

        if not catalog_actions:
            return ChatTurnPreparationContentService.format(
                "directAnswers",
                "productionOperational",
                "actionMissingFromCatalog",
                pathLabel=path_label,
                providerKey=provider_key,
            )

        allowed = {str(item) for item in allowed_action_ids}
        enabled_matches = [
            action
            for action in catalog_actions
            if str(action.get("actionId")) in allowed
        ]

        if enabled_matches:
            return None

        sample = catalog_actions[0]
        action_id = str(sample.get("actionId") or sample.get("operationId") or path_label)

        return ChatTurnPreparationContentService.format(
            "directAnswers",
            "productionOperational",
            "actionNotEnabledOnAgent",
            pathLabel=path_label,
            actionId=action_id,
        )
