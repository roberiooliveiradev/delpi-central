"""Matcher declarativo para entradas do operational_route_registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class OperationalRouteMatcherService:
    _CUSTOM_PREDICATES: dict[str, Callable[[str], bool]] = {
        "directives": ChatProductQueryIntentService._looks_like_directives_question,
        "exclusiveRawMaterialCatalog": (
            ChatProductQueryIntentService._looks_like_exclusive_raw_material_catalog_question
        ),
        "factoryStatus": ChatProductQueryIntentService._looks_like_factory_status_question,
        "productionStatus": ChatProductQueryIntentService._looks_like_production_status_question,
        "shippingStatus": ChatProductQueryIntentService._looks_like_shipping_status_question,
        "structureExclusivity": (
            ChatProductQueryIntentService._looks_like_structure_exclusivity_question
        ),
        "rawMaterialPriceIntelligence": (
            ChatProductQueryIntentService._looks_like_raw_material_price_intelligence_question
        ),
        "costImpactSimulation": (
            ChatProductQueryIntentService._looks_like_cost_impact_simulation_question
        ),
        "lastPurchase": ChatProductQueryIntentService._looks_like_last_purchase_question,
        "purchasePriceHistory": (
            ChatProductQueryIntentService._looks_like_purchase_price_history_question
        ),
        "purchaseBudgetHistory": (
            ChatProductQueryIntentService._looks_like_purchase_budget_history_question
        ),
    }

    @classmethod
    def matches(
        cls,
        match_spec: dict[str, Any] | None,
        *,
        message: str,
        normalized: str,
    ) -> bool:
        if not isinstance(match_spec, dict) or not match_spec:
            return False

        if not cls._evaluate_spec(match_spec, message=message, normalized=normalized):
            return False

        if match_spec.get("requiresProductIdentifier"):
            identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return False

        return True

    @classmethod
    def _evaluate_spec(
        cls,
        spec: dict[str, Any],
        *,
        message: str,
        normalized: str,
    ) -> bool:
        custom_predicate = str(spec.get("customPredicate") or "").strip()

        if custom_predicate:
            matcher = cls._CUSTOM_PREDICATES.get(custom_predicate)

            if not matcher or not matcher(normalized):
                return False

        all_of = spec.get("allOf")

        if isinstance(all_of, list):
            for node in all_of:
                if not isinstance(node, dict):
                    return False

                if not cls._evaluate_node(node, message=message, normalized=normalized):
                    return False

        none_of = spec.get("noneOf")

        if isinstance(none_of, list):
            for node in none_of:
                if not isinstance(node, dict):
                    continue

                if cls._evaluate_node(node, message=message, normalized=normalized):
                    return False

        terms_from = str(spec.get("termsFrom") or "").strip()

        if terms_from and not cls._message_has_terms(terms_from, normalized):
            return False

        exclude_terms_from = str(spec.get("excludeTermsFrom") or "").strip()

        if exclude_terms_from and cls._message_has_terms(exclude_terms_from, normalized):
            return False

        if spec.get("hasProductIdentifier"):
            identifier = ChatProductQueryIntentService.extract_product_code(message or "")

            if not identifier:
                return False

        if spec.get("hasProductScope") and not cls._has_product_scope(normalized):
            return False

        if (
            not custom_predicate
            and not terms_from
            and not isinstance(all_of, list)
            and not isinstance(none_of, list)
        ):
            return False

        return True

    @classmethod
    def _evaluate_node(
        cls,
        node: dict[str, Any],
        *,
        message: str,
        normalized: str,
    ) -> bool:
        if node.get("hasProductIdentifier"):
            if not ChatProductQueryIntentService.extract_product_code(message or ""):
                return False

        if node.get("hasProductScope") and not cls._has_product_scope(normalized):
            return False

        custom_predicate = str(node.get("customPredicate") or "").strip()

        if custom_predicate:
            matcher = cls._CUSTOM_PREDICATES.get(custom_predicate)

            if not matcher or not matcher(normalized):
                return False

        terms_from = str(node.get("termsFrom") or "").strip()

        if terms_from and not cls._message_has_terms(terms_from, normalized):
            return False

        exclude_terms_from = str(node.get("excludeTermsFrom") or "").strip()

        if exclude_terms_from and cls._message_has_terms(exclude_terms_from, normalized):
            return False

        return bool(
            custom_predicate
            or terms_from
            or exclude_terms_from
            or node.get("hasProductIdentifier")
            or node.get("hasProductScope")
        )

    @classmethod
    def _message_has_terms(cls, terms_from: str, normalized: str) -> bool:
        terms = cls._resolve_terms(terms_from)

        if not terms:
            return False

        return any(term in normalized for term in terms)

    @classmethod
    def _resolve_terms(cls, terms_from: str) -> list[str]:
        parts = [part.strip() for part in str(terms_from or "").split(".") if part.strip()]

        if len(parts) < 2:
            return []

        bundle = parts[0]
        return ChatAssistantContentService.list(bundle, *parts[1:])

    @classmethod
    def _has_product_scope(cls, normalized: str) -> bool:
        return ChatProductQueryIntentService._has_product_scope_reference(normalized)
