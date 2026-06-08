"""Seleção genérica por ranking semântico — Fase 3B lote 19."""

from __future__ import annotations

from typing import Callable

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionGenericRouteSelectionService:
    def select(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        previous_messages: list | None = None,
        candidates_loader: Callable[..., list[dict]] | None = None,
        rank_candidates: Callable[..., list[dict]] | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
    ) -> dict | None:
        if not allowed_action_ids or not candidates_loader or not rank_candidates:
            return None

        candidates = candidates_loader(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=120,
        )

        if not candidates:
            return None

        ranked = rank_candidates(
            message,
            candidates,
            allowed_action_ids=allowed_action_ids,
        )

        if not ranked:
            return None

        action = ranked[0]

        if action.get("selectionScore") is None:
            return None

        parameters = {}

        if build_date_branch_parameters:
            parameters = build_date_branch_parameters(
                action,
                message,
                previous_messages=previous_messages,
            )

        arguments: dict = {
            "actionId": action["actionId"],
            "body": {
                "message": message,
            },
        }

        if parameters:
            arguments["parameters"] = parameters

        return {
            "name": "execute_external_action",
            "arguments": arguments,
            "reason": action.get("selectionReason")
            or ExternalActionResponseContentService.get(
                "selectionReasons",
                "genericSemanticFallback",
            ),
        }
