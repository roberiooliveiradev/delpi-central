"""Fast-path declarativo por vocabulário — rotas OpenAPI de qualquer provider."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionVocabularyRouteSelectionService:
    _MATCHERS: dict[str, Callable[[str], bool]] = {
        "directives": ChatProductQueryIntentService._looks_like_directives_question,
        "exclusiveRawMaterialCatalog": (
            ChatProductQueryIntentService._looks_like_exclusive_raw_material_catalog_question
        ),
    }

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
        entries = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "vocabularyFastPaths",
        )

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            selected = self._try_entry(
                entry,
                message,
                normalized,
                allowed_action_ids,
                candidates_loader=candidates_loader,
            )

            if selected:
                return selected

        return None

    def _try_entry(
        self,
        entry: dict,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
    ) -> dict | None:
        matcher_key = str(entry.get("matcher") or "").strip()

        if not matcher_key:
            return None

        matcher = self._MATCHERS.get(matcher_key)

        if not matcher or not matcher(normalized):
            return None

        path_markers = [
            str(marker).lower()
            for marker in (entry.get("pathMarkers") or [])
            if str(marker).strip()
        ]
        operation_markers = [
            str(marker).lower()
            for marker in (entry.get("operationIdMarkers") or [])
            if str(marker).strip()
        ]

        if not path_markers and not operation_markers:
            return None

        identifier = None

        if entry.get("requiresProductIdentifier"):
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

        for action in candidates:
            if action.get("method") != "GET":
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
                str(entry.get("parameterStrategy") or ""),
                action,
                message=message,
                normalized=normalized,
                identifier=identifier,
            )

            if not parameters:
                continue

            reason_key = str(entry.get("reasonKey") or "").strip()

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
        strategy: str,
        action: dict,
        *,
        message: str,
        normalized: str,
        identifier: str | None,
    ) -> dict | None:
        if strategy == "product_code":
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
