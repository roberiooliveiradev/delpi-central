"""Predicados declarativos de rota de produto (product_query_intent.routePredicates)."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


class ChatProductRoutePredicateService:
    _BUNDLE = "product_query_intent"
    _SECTION = "routePredicates"

    @classmethod
    def registered_predicates(cls) -> frozenset[str]:
        node = ChatAssistantContentService.get_node(cls._BUNDLE, cls._SECTION) or {}

        if not isinstance(node, dict):
            return frozenset()

        return frozenset(str(key) for key in node.keys())

    @classmethod
    def matches(
        cls,
        predicate: str,
        normalized: str,
        *,
        message: str = "",
    ) -> bool:
        spec = ChatAssistantContentService.get_node(
            cls._BUNDLE,
            cls._SECTION,
            str(predicate or "").strip(),
        )

        if not isinstance(spec, dict) or not spec:
            return False

        return OperationalRouteMatcherService._evaluate_spec(
            spec,
            message=message or normalized,
            normalized=normalized,
        )
