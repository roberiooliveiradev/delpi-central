"""Predicados declarativos de produto (routePredicates + playbookPredicates)."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


class ChatProductRoutePredicateService:
    _BUNDLE = "product_query_intent"
    _SECTIONS = ("routePredicates", "playbookPredicates")

    @classmethod
    def registered_predicates(cls) -> frozenset[str]:
        keys: set[str] = set()

        for section in cls._SECTIONS:
            node = ChatAssistantContentService.get_node(cls._BUNDLE, section) or {}

            if isinstance(node, dict):
                keys.update(str(key) for key in node.keys())

        return frozenset(keys)

    @classmethod
    def _resolve_spec(cls, predicate: str) -> dict | None:
        key = str(predicate or "").strip()

        if not key:
            return None

        for section in cls._SECTIONS:
            spec = ChatAssistantContentService.get_node(cls._BUNDLE, section, key)

            if isinstance(spec, dict) and spec:
                return spec

        return None

    @classmethod
    def matches(
        cls,
        predicate: str,
        normalized: str,
        *,
        message: str = "",
    ) -> bool:
        spec = cls._resolve_spec(predicate)

        if not spec:
            return False

        return OperationalRouteMatcherService._evaluate_spec(
            spec,
            message=message or normalized,
            normalized=normalized,
        )
