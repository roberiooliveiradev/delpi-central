"""Intent Playbook produto — matching declarativo via registry operacional."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


class ChatPlaybookProductIntentService:
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
