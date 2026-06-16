"""Matcher declarativo para entradas do operational_route_registry."""

from __future__ import annotations

import re

from collections.abc import Callable
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_system_metadata_intent_service import (
    ChatSystemMetadataIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


def _lmp_sale_number_patterns() -> list[str]:
    return ExternalActionResponseContentService.list(
        "actionSelection",
        "lmpSaleNumberPatterns",
    )


def _extract_lmp_sale_number(text: str | None) -> str | None:
    raw = str(text or "")

    for pattern in _lmp_sale_number_patterns():
        match = re.search(str(pattern), raw, flags=re.IGNORECASE)

        if match:
            return match.group(1)

    return None


def _extract_product_search_group_code(message: str, normalized: str) -> str | None:
    from app.domain.services.chat_product_search_intent_service import (
        ChatProductSearchIntentService,
    )

    return ChatProductSearchIntentService.extract_search_group_code(message, normalized)


def _department_kpi_resolved(normalized: str) -> bool:
    from app.domain.services.chat_department_kpi_intent_service import (
        ChatDepartmentKpiIntentService,
    )

    return bool(ChatDepartmentKpiIntentService.resolve(normalized))


def _technical_normas_description_block(normalized: str) -> bool:
    from app.domain.services.chat_technical_description_intent_service import (
        ChatTechnicalDescriptionIntentService,
    )

    return ChatTechnicalDescriptionIntentService.requires_normas_knowledge(normalized)


class OperationalRouteMatcherService:
    _CUSTOM_PREDICATES: dict[str, Callable[[str], bool]] = {
        "departmentKpiResolved": _department_kpi_resolved,
        "technicalNormasDescriptionBlock": _technical_normas_description_block,
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
            if not cls._match_custom_predicate(
                custom_predicate,
                normalized,
                message=message,
            ):
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

        any_of = spec.get("anyOf")

        if isinstance(any_of, list) and any_of:
            if not any(
                cls._evaluate_spec(branch, message=message, normalized=normalized)
                for branch in any_of
                if isinstance(branch, dict)
            ):
                return False

        terms_from = str(spec.get("termsFrom") or "").strip()

        if terms_from and not cls._message_has_terms(terms_from, normalized):
            return False

        exclude_terms_from = str(spec.get("excludeTermsFrom") or "").strip()

        if exclude_terms_from and cls._message_has_terms(exclude_terms_from, normalized):
            return False

        exclude_terms_unless = spec.get("excludeTermsUnless")

        if isinstance(exclude_terms_unless, dict):
            if not cls._passes_exclude_terms_unless(exclude_terms_unless, normalized):
                return False

        regex_patterns = spec.get("regexPatterns")

        if isinstance(regex_patterns, list) and regex_patterns:
            if not any(
                re.search(str(pattern), normalized)
                for pattern in regex_patterns
                if str(pattern or "").strip()
            ):
                return False

        regex_patterns_from = str(spec.get("regexPatternsFrom") or "").strip()

        if regex_patterns_from:
            patterns = cls._resolve_terms(regex_patterns_from)

            if not patterns or not any(
                re.search(str(pattern), normalized)
                for pattern in patterns
                if str(pattern or "").strip()
            ):
                return False

        plural_scope = str(spec.get("pluralScopeLinked") or "").strip()

        if plural_scope:
            from app.domain.services.chat_product_plural_phrasing_service import (
                ChatProductPluralPhrasingService,
            )

            if not ChatProductPluralPhrasingService.matches_scope_linked_to_products(
                normalized,
                scope=plural_scope,
            ):
                return False

        if spec.get("hasProductEntityReference"):
            from app.domain.services.chat_product_plural_phrasing_service import (
                ChatProductPluralPhrasingService,
            )

            if not ChatProductPluralPhrasingService.has_product_entity_reference(normalized):
                return False

        if spec.get("lacksProductIdentifier"):
            if ChatProductQueryIntentService.extract_product_code(message or ""):
                return False

        if spec.get("hasLmpSaleNumber"):
            if not _extract_lmp_sale_number(message or normalized):
                return False

        if spec.get("lacksLmpSaleNumber"):
            if _extract_lmp_sale_number(message or normalized):
                return False

        if spec.get("hasSystemTableName"):
            if not ChatSystemMetadataIntentService.extract_table_name(message or normalized):
                return False

        if spec.get("hasProductSearchGroupCode"):
            if not _extract_product_search_group_code(message or normalized, normalized):
                return False

        min_word_count = spec.get("minWordCount")

        if min_word_count is not None:
            if len(str(normalized or "").split()) < int(min_word_count):
                return False

        exclusion_probe = cls._matches_intent_exclusion_probe(
            spec,
            normalized=normalized,
            message=message,
        )

        if exclusion_probe is not None:
            return exclusion_probe

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
            and not isinstance(any_of, list)
            and not spec.get("hasProductIdentifier")
            and not spec.get("hasProductScope")
            and not spec.get("lacksProductIdentifier")
            and not spec.get("hasLmpSaleNumber")
            and not spec.get("lacksLmpSaleNumber")
            and not spec.get("hasSystemTableName")
            and not spec.get("hasProductSearchGroupCode")
            and min_word_count is None
            and not spec.get("excludeIfSqlConversation")
            and not spec.get("excludeIfWebSearch")
            and not spec.get("excludeIfSqlOperational")
            and not spec.get("excludeIfProductionRestRoute")
            and not plural_scope
            and not spec.get("hasProductEntityReference")
            and not regex_patterns_from
            and not (
                isinstance(regex_patterns, list) and regex_patterns
            )
        ):
            return False

        return True

    @classmethod
    def _matches_intent_exclusion_probe(
        cls,
        spec: dict[str, Any],
        *,
        normalized: str,
        message: str,
    ) -> bool | None:
        probes = (
            ("excludeIfSqlConversation", cls._is_sql_conversation_turn),
            ("excludeIfWebSearch", cls._is_web_search_turn),
            ("excludeIfSqlOperational", cls._requires_sql_operational_knowledge),
            ("excludeIfProductionRestRoute", cls._matches_production_rest_route),
        )

        for key, checker in probes:
            if spec.get(key):
                return checker(normalized, message=message)

        return None

    @staticmethod
    def _is_sql_conversation_turn(normalized: str, *, message: str = "") -> bool:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        return ChatSqlIntentService.is_sql_conversation_turn(normalized)

    @staticmethod
    def _is_web_search_turn(normalized: str, *, message: str = "") -> bool:
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        return ChatWebSearchIntentService.matches(normalized)

    @staticmethod
    def _requires_sql_operational_knowledge(normalized: str, *, message: str = "") -> bool:
        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        return ChatSqlOperationalIntentService.requires_sql_knowledge(normalized)

    @staticmethod
    def _matches_production_rest_route(normalized: str, *, message: str = "") -> bool:
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        return ChatProductionOperationalIntentService.matches_rest_route(normalized)

    @classmethod
    def _passes_exclude_terms_unless(
        cls,
        spec: dict[str, Any],
        normalized: str,
    ) -> bool:
        terms_from = str(spec.get("termsFrom") or "").strip()

        if not terms_from or not cls._message_has_terms(terms_from, normalized):
            return True

        unless_terms_from = str(spec.get("unlessTermsFrom") or "").strip()

        if unless_terms_from and cls._message_has_terms(unless_terms_from, normalized):
            return True

        return False

    @classmethod
    def _evaluate_node(
        cls,
        node: dict[str, Any],
        *,
        message: str,
        normalized: str,
    ) -> bool:
        if not isinstance(node, dict):
            return False

        return cls._evaluate_spec(node, message=message, normalized=normalized)

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

    @classmethod
    def looks_like_sale_orders_list_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return ChatProductRoutePredicateService.matches("saleOrdersList", normalized)

    @classmethod
    def looks_like_transforma_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return ChatProductRoutePredicateService.matches("transformaQuestion", normalized)

    @classmethod
    def _match_custom_predicate(
        cls,
        predicate: str,
        normalized: str,
        *,
        message: str = "",
    ) -> bool:
        key = str(predicate or "").strip()

        if not key:
            return False

        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        if key in ChatProductRoutePredicateService.registered_predicates():
            return ChatProductRoutePredicateService.matches(
                key,
                normalized,
                message=message or normalized,
            )

        matcher = cls._CUSTOM_PREDICATES.get(key)

        return bool(matcher and matcher(normalized))

    @classmethod
    def matches_custom_predicate(cls, predicate: str, normalized: str) -> bool:
        return cls._match_custom_predicate(predicate, normalized, message=normalized)

    @staticmethod
    def extract_lmp_sale_number(text: str | None) -> str | None:
        return _extract_lmp_sale_number(text)

    @classmethod
    def looks_like_system_metadata_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return ChatProductRoutePredicateService.matches(
            "systemMetadataQuestion",
            normalized,
        )
