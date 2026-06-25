"""Match de rotas vocabulary + delegação à resolução de action."""

from __future__ import annotations

from typing import Callable

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


class OperationalRouteVocabularyMatcherService:
    def __init__(self, catalog, resolver) -> None:
        self._catalog = catalog
        self._resolver = resolver

    def try_vocabulary_route(
        self,
        route: dict,
        message: str,
        normalized: str,
        allowed_action_ids: list[str],
        *,
        candidates_loader: Callable[..., list[dict]] | None = None,
        previous_messages: list | None = None,
        build_date_branch_parameters: Callable[..., dict] | None = None,
        merge_date_parameters: Callable[..., dict] | None = None,
        conversation_context: str | None = None,
        description_override: str | None = None,
        identifier: str | None = None,
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

        resolved_identifier = str(identifier or "").strip()

        if match_spec.get("requiresProductIdentifier"):
            if not resolved_identifier:
                resolved_identifier = str(
                    ChatProductQueryIntentService.extract_product_code(message or "") or ""
                ).strip()

            if not resolved_identifier:
                return None

        parameters_spec = route.get("parameters")

        if (
            not resolved_identifier
            and isinstance(parameters_spec, dict)
            and str(parameters_spec.get("strategy") or "").strip().lower() == "product_code"
        ):
            resolved_identifier = str(
                ChatProductQueryIntentService.resolve_product_code(
                    message,
                    conversation_context,
                    previous_messages=previous_messages,
                )
                or ""
            ).strip()

            if not resolved_identifier:
                return None

        return self._resolver.resolve_route_action(
            route,
            message,
            allowed_action_ids,
            identifier=resolved_identifier or None,
            candidates_loader=candidates_loader,
            previous_messages=previous_messages,
            build_date_branch_parameters=build_date_branch_parameters,
            merge_date_parameters=merge_date_parameters,
            conversation_context=conversation_context,
            description_override=description_override,
        )
