"""Seleção de refinamentos de paginação e profundidade — Fase 3B lote 19."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionRefinementRouteSelectionService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def select_pagination(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
        select_product: Callable[..., dict | None] | None = None,
    ) -> dict | None:
        action_id = str(refinement.action_id or "").strip()
        allowed = set(allowed_action_ids or [])

        if action_id and action_id in allowed:
            selected = self.build_pagination_action(
                refinement,
                action_id=action_id,
                allowed_action_ids=allowed_action_ids,
            )

            if selected:
                return selected

        product_code = str(refinement.product_code or "").strip()
        route_segment = str(refinement.route_segment or "").strip()

        if not product_code or not route_segment or not select_product:
            return None

        intent_by_segment = {
            "parents": ChatProductQueryIntent.PARENTS,
            "structure": ChatProductQueryIntent.STRUCTURE,
            "stock": ChatProductQueryIntent.STOCK,
        }
        intent = intent_by_segment.get(route_segment)

        if not intent:
            return None

        selected = select_product(
            message
            or ExternalActionResponseContentService.get(
                "actionSelection",
                "refinementFallbackMessages",
                "pagination",
            ),
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
        )

        if not selected:
            return None

        resolved_action_id = str(
            (selected.get("arguments") or {}).get("actionId") or ""
        ).strip()

        if not resolved_action_id:
            return None

        return self.build_pagination_action(
            refinement,
            action_id=resolved_action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=dict(
                refinement.previous_parameters
                or (selected.get("arguments") or {}).get("parameters")
                or {}
            ),
            fallback_reason=selected.get("reason"),
        )

    def select_depth(
        self,
        refinement,
        *,
        allowed_action_ids: list[str],
        message: str = "",
        select_product: Callable[..., dict | None] | None = None,
        clamp_max_depth: Callable[[int, str], int] | None = None,
    ) -> dict | None:
        action_id = str(refinement.action_id or "").strip()
        allowed = set(allowed_action_ids or [])

        if action_id and action_id in allowed:
            selected = self.build_depth_action(
                refinement,
                action_id=action_id,
                allowed_action_ids=allowed_action_ids,
                clamp_max_depth=clamp_max_depth,
            )

            if selected:
                return selected

        product_code = str(refinement.product_code or "").strip()
        route_segment = str(refinement.route_segment or "").strip()

        if not product_code or route_segment not in {"parents", "structure"}:
            return None

        if not select_product:
            return None

        intent_by_segment = {
            "parents": ChatProductQueryIntent.PARENTS,
            "structure": ChatProductQueryIntent.STRUCTURE,
        }
        intent = intent_by_segment.get(route_segment)

        if not intent:
            return None

        selected = select_product(
            message
            or ExternalActionResponseContentService.get(
                "actionSelection",
                "refinementFallbackMessages",
                "depth",
            ),
            product_code,
            allowed_action_ids=allowed_action_ids,
            intent=intent,
        )

        if not selected:
            return None

        resolved_action_id = str(
            (selected.get("arguments") or {}).get("actionId") or ""
        ).strip()

        if not resolved_action_id:
            return None

        return self.build_depth_action(
            refinement,
            action_id=resolved_action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=dict(
                refinement.previous_parameters
                or (selected.get("arguments") or {}).get("parameters")
                or {}
            ),
            fallback_reason=selected.get("reason"),
            clamp_max_depth=clamp_max_depth,
        )

    def build_depth_action(
        self,
        refinement,
        *,
        action_id: str,
        allowed_action_ids: list[str],
        base_parameters: dict | None = None,
        fallback_reason: str | None = None,
        clamp_max_depth: Callable[[int, str], int] | None = None,
    ) -> dict | None:
        selected = self.build_pagination_action(
            refinement,
            action_id=action_id,
            allowed_action_ids=allowed_action_ids,
            base_parameters=base_parameters,
            fallback_reason=fallback_reason,
        )

        if not selected or refinement.max_depth is None:
            return selected

        candidates = self.repository.find_candidate_actions(
            "",
            limit=80,
            allowed_action_ids=allowed_action_ids,
        )

        action = next(
            (
                item
                for item in candidates
                if str(item.get("actionId") or "") == action_id
            ),
            None,
        )

        if not action:
            return selected

        parameters = dict((selected.get("arguments") or {}).get("parameters") or {})
        clamp = clamp_max_depth or (lambda value, path: value)

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"max_depth", "maxdepth", "depth", "nivel", "levels"}:
                parameters[name] = clamp(
                    refinement.max_depth,
                    str(action.get("path") or ""),
                )

        reason = fallback_reason or refinement.reason or ExternalActionResponseContentService.get(
            "selectionReasons",
            "depthRefinementDefault",
        )

        return {
            **selected,
            "arguments": {
                **(selected.get("arguments") or {}),
                "parameters": parameters,
            },
            "reason": reason,
        }

    def build_pagination_action(
        self,
        refinement,
        *,
        action_id: str,
        allowed_action_ids: list[str],
        base_parameters: dict | None = None,
        fallback_reason: str | None = None,
    ) -> dict | None:
        candidates = self.repository.find_candidate_actions(
            "",
            limit=80,
            allowed_action_ids=allowed_action_ids,
        )

        action = next(
            (
                item
                for item in candidates
                if str(item.get("actionId") or "") == action_id
            ),
            None,
        )

        if not action:
            return None

        parameters = dict(base_parameters or refinement.previous_parameters or {})

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if refinement.page_size is not None and lowered in {
                "page_size",
                "pagesize",
                "limit",
            }:
                parameters[name] = refinement.page_size
            elif refinement.page is not None and lowered == "page":
                parameters[name] = refinement.page

        reason = fallback_reason or refinement.reason or ExternalActionResponseContentService.get(
            "selectionReasons",
            "paginationRefinementDefault",
        )

        if refinement.page_size is not None:
            reason = ExternalActionResponseContentService.format(
                "selectionReasons",
                "paginationRefinementPageSize",
                page_size=refinement.page_size,
            )
        elif refinement.page is not None:
            reason = ExternalActionResponseContentService.format(
                "selectionReasons",
                "paginationRefinementPage",
                page=refinement.page,
            )

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action_id,
                "parameters": parameters,
            },
            "reason": reason,
        }
