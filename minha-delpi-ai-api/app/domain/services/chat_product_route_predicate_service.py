"""Predicados declarativos de rota (produto + domínio) via JSON."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)

_PREDICATE_SOURCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "product_query_intent",
        ("routePredicates", "playbookPredicates", "subIntentPredicates"),
    ),
    ("external_action_responses", ("domainPredicates", "systemPredicates", "productSearchPredicates")),
)


class ChatProductRoutePredicateService:
    @classmethod
    def registered_predicates(cls) -> frozenset[str]:
        keys: set[str] = set()

        for bundle, sections in _PREDICATE_SOURCES:
            for section in sections:
                node = ChatAssistantContentService.get_node(bundle, section) or {}

                if isinstance(node, dict):
                    keys.update(str(key) for key in node.keys())

        return frozenset(keys)

    @classmethod
    def _resolve_spec(cls, predicate: str) -> dict | None:
        key = str(predicate or "").strip()

        if not key:
            return None

        for bundle, sections in _PREDICATE_SOURCES:
            for section in sections:
                spec = ChatAssistantContentService.get_node(bundle, section, key)

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

    _VOCABULARY_TERM_HINT_KEYS: tuple[str, ...] = (
        "terms",
        "exclusivityMarkers",
        "shippingMarkers",
        "factoryOnlyMarkers",
        "colloquialTerms",
        "scopeMarkers",
    )

    @classmethod
    def partially_matches(
        cls,
        predicate: str,
        normalized: str,
        *,
        message: str = "",
    ) -> bool:
        """Termos do predicado aparecem na mensagem, mas o match completo (escopo/identificador) falhou."""
        if cls.matches(predicate, normalized, message=message or normalized):
            return False

        return cls._vocabulary_terms_overlap(predicate, normalized)

    @classmethod
    def _vocabulary_terms_overlap(cls, predicate: str, normalized: str) -> bool:
        for term in cls._vocabulary_term_hints(predicate):
            if len(term) < 4:
                continue

            if term in normalized:
                return True

        return False

    @classmethod
    def _vocabulary_term_hints(cls, predicate: str) -> tuple[str, ...]:
        key = str(predicate or "").strip()
        node = ChatAssistantContentService.get_node("product_query_intent", key)

        if not isinstance(node, dict):
            return ()

        collected: list[str] = []

        for hint_key in cls._VOCABULARY_TERM_HINT_KEYS:
            values = node.get(hint_key)

            if not isinstance(values, list):
                continue

            collected.extend(str(item).strip() for item in values if str(item).strip())

        return tuple(collected)
