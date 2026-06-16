"""Fast-path declarativo por vocabulário — operational_route_registry (DOCIE Fase 4)."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)


class ExternalActionVocabularyRouteSelectionService:
    def __init__(self, operational_route: ExternalActionOperationalRouteSelectionService) -> None:
        self._operational_route = operational_route

    def select(
        self,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return self._operational_route.select(
            message,
            normalized,
            allowed_action_ids,
            candidates_loader=candidates_loader,
            build_date_branch_parameters=build_date_branch_parameters,
            previous_messages=previous_messages,
        )
