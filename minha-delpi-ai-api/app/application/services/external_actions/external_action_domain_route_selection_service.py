"""Seleção de rotas comerciais, Transforma e metadados Protheus — Fase 3B lote 18."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_system_metadata_intent_service import (
    ChatSystemMetadataIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionDomainRouteSelectionService:
    def __init__(self, repository) -> None:
        self.repository = repository

    @staticmethod
    def looks_like_sale_orders_list_question(value: str) -> bool:
        exclude_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "saleOrdersList",
            "excludeTerms",
        )

        if any(term in value for term in exclude_terms):
            return False

        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "saleOrdersList",
            "terms",
        )

        return any(term in value for term in terms)

    @staticmethod
    def looks_like_transforma_question(value: str) -> bool:
        return "transforma" in value

    @staticmethod
    def looks_like_system_metadata_question(value: str) -> bool:
        return ChatSystemMetadataIntentService.looks_like_question(value)

    def select_sale_orders(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
        merge_date_parameters: Callable[..., dict],
    ) -> dict | None:
        candidates = candidates_loader(
            message,
            allowed_action_ids=allowed_action_ids,
            limit=80,
        )

        best = None

        for action in candidates:
            if action.get("method") != "GET":
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if not (
                path.rstrip("/").endswith("/sales")
                or "list_sale_orders" in operation_id
            ):
                continue

            if "/lmps" in path or "lmp" in path:
                continue

            if "/products/" in path or "{code}" in path:
                continue

            best = action

            if "list_sale_orders" in operation_id or "{" not in path:
                break

        if not best:
            return None

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": best["actionId"],
                "parameters": self._build_sale_orders_parameters(
                    best,
                    message,
                    merge_date_parameters=merge_date_parameters,
                ),
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "saleOrdersList",
            ),
        }

    def select_transforma(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
        build_date_branch_parameters: Callable[..., dict],
        previous_messages: list | None = None,
    ) -> dict | None:
        candidates = [
            action
            for action in candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            if action.get("method") == "GET"
            and "transforma-mais" in str(action.get("path") or "").lower()
        ]

        if not candidates:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        wants_summary = any(
            term in normalized
            for term in ("resumo", "summary", "indicadores", "kpis")
        )

        def score(action: dict) -> int:
            path = str(action.get("path") or "").lower()
            value = 0

            if wants_summary and "/summary" in path:
                value += 100

            if not wants_summary and "/processes" in path and "/summary" not in path:
                value += 80

            if "/summary" in path and not wants_summary:
                value -= 20

            return value

        action = sorted(candidates, key=score, reverse=True)[0]

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": build_date_branch_parameters(
                    action,
                    message,
                    previous_messages=previous_messages,
                ),
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "transformaMais",
            ),
        }

    def select_system_metadata(
        self,
        message: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]],
    ) -> dict | None:
        allowed = {str(item) for item in allowed_action_ids}
        candidates = [
            action
            for action in candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )
            if action.get("method") == "GET"
            and str(action.get("path") or "").lower().startswith("/system/")
        ]

        if not candidates and allowed:
            list_actions = getattr(self.repository, "list_actions", None)

            if callable(list_actions):
                candidates = [
                    action
                    for action in list_actions()
                    if str(action.get("actionId")) in allowed
                    if action.get("method") == "GET"
                    and str(action.get("path") or "").lower().startswith("/system/")
                ]

        if not candidates:
            return None

        ranked = sorted(
            candidates,
            key=lambda action: ChatSystemMetadataIntentService.score_action(
                message,
                action,
            ),
            reverse=True,
        )

        if ChatSystemMetadataIntentService.score_action(message, ranked[0]) <= 0:
            return None

        action = ranked[0]

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action["actionId"],
                "parameters": ChatSystemMetadataIntentService.build_parameters(
                    message,
                    action,
                ),
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "systemMetadata",
            ),
        }

    @staticmethod
    def _build_sale_orders_parameters(
        action: dict,
        message: str,
        *,
        merge_date_parameters: Callable[..., dict],
    ) -> dict:
        parameters = {}

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {"page"}:
                parameters[name] = 1
            elif lowered in {"page_size", "pagesize", "limit"}:
                parameters[name] = 50

        return merge_date_parameters(action, message, parameters)
