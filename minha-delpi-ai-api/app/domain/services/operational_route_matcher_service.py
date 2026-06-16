"""Matcher declarativo para entradas do operational_route_registry."""

from __future__ import annotations

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


def _looks_like_sale_orders_list_question(normalized: str) -> bool:
    exclude_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "saleOrdersList",
        "excludeTerms",
    )

    if any(term in normalized for term in exclude_terms):
        return False

    terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "saleOrdersList",
        "terms",
    )

    return any(term in normalized for term in terms)


def _looks_like_transforma_question(normalized: str) -> bool:
    return "transforma" in normalized


def _extract_lmp_sale_number(text: str | None) -> str | None:
    import re

    raw = str(text or "")

    patterns = [
        r"\bov\s*[#:\-]?\s*(\d{4,})\b",
        r"\bordem\s+de\s+venda\s*[#:\-]?\s*(\d{4,})\b",
        r"\blmp\s+(\d{4,})\b",
        r"\bamostra\s+(\d{4,})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)

        if match:
            return match.group(1)

    return None


def _looks_like_lmp_question(normalized: str) -> bool:
    if _looks_like_transforma_question(normalized):
        return False

    terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "lmpQuestion",
        "terms",
    )

    if any(term in normalized for term in terms):
        return True

    sale_order_phrases = ExternalActionResponseContentService.list(
        "actionSelection",
        "lmpQuestion",
        "saleOrderPhrases",
    )
    sale_order_markers = ExternalActionResponseContentService.list(
        "actionSelection",
        "lmpQuestion",
        "saleOrderMarkers",
    )

    if any(phrase in normalized for phrase in sale_order_phrases):
        return any(marker in normalized for marker in sale_order_markers) or bool(
            _extract_lmp_sale_number(normalized)
        )

    return False


def _lmp_has_ranking_terms(normalized: str, *keys: str) -> bool:
    for key in keys:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "lmpRanking",
            key,
        )

        if any(term in normalized for term in terms):
            return True

    return False


def _looks_like_lmp_catch_all(normalized: str) -> bool:
    if not _looks_like_lmp_question(normalized):
        return False

    if _extract_lmp_sale_number(normalized):
        return False

    if _lmp_has_ranking_terms(
        normalized,
        "dashboardSummaryTerms",
        "dashboardItemsTerms",
        "chartTerms",
        "dashboardTerms",
    ):
        return False

    return True


def _looks_like_system_metadata_question(normalized: str) -> bool:
    return ChatSystemMetadataIntentService.looks_like_question(normalized)


def _system_has_table_name(normalized: str) -> bool:
    return bool(ChatSystemMetadataIntentService.extract_table_name(normalized))


def _system_wants_columns(normalized: str) -> bool:
    return ChatSystemMetadataIntentService.wants_columns(normalized)


def _system_wants_relations(normalized: str) -> bool:
    return ChatSystemMetadataIntentService.wants_relations(normalized)


def _system_wants_table_search(normalized: str) -> bool:
    return ChatSystemMetadataIntentService.wants_table_search(normalized)


def _looks_like_supplies_otd_question(normalized: str) -> bool:
    if not any(
        term in normalized
        for term in (
            " otd",
            "otd ",
            "on-time delivery",
            "entrega no prazo",
            "entregas no prazo",
        )
    ) and not normalized.strip().startswith("otd"):
        return False

    supplies_markers = ("compra", "supriment", "fornecedor", "supplies")

    return any(marker in normalized for marker in supplies_markers)


def _looks_like_production_otd_detail_question(normalized: str) -> bool:
    detail_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionOtdDetailTerms",
    )
    production_terms = ("producao", "produção", "fabril", "manufatura", "op ", "ops")

    return any(term in normalized for term in detail_terms) and any(
        term in normalized for term in production_terms
    )


def _looks_like_production_oee_detail_question(normalized: str) -> bool:
    detail_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionOeeDetailTerms",
    )
    oee_terms = (
        "oee",
        "eficiencia",
        "eficiência",
        "equipamento",
        "equipamentos",
        "zefici",
    )
    fabril_block_terms = ("fabril", "resultado mod", "mod fabril", "dashboard eficiencia")

    return (
        any(term in normalized for term in detail_terms)
        and any(term in normalized for term in oee_terms)
        and not any(term in normalized for term in fabril_block_terms)
    )


def _looks_like_production_oee_appointment_question(normalized: str) -> bool:
    appointment_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionOeeAppointmentTerms",
    )
    oee_terms = (
        "oee",
        "eficiencia",
        "eficiência",
        "equipamento",
        "equipamentos",
        "zefici",
    )
    appointment_context_terms = (
        "apontamento",
        "apontamentos",
        "sh6010",
        "h6_zefici",
    )

    return any(term in normalized for term in appointment_terms) and (
        any(term in normalized for term in oee_terms)
        or any(term in normalized for term in appointment_context_terms)
    )


def _looks_like_production_eficiencia_fabril_question(normalized: str) -> bool:
    fabril_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionEficienciaFabrilTerms",
    )

    return any(term in normalized for term in fabril_terms)


def _looks_like_product_search_question(normalized: str) -> bool:
    from app.domain.services.chat_product_search_intent_service import (
        ChatProductSearchIntentService,
    )

    return ChatProductSearchIntentService.looks_like_product_search(normalized)


def _looks_like_product_search_with_group_code(normalized: str) -> bool:
    from app.domain.services.chat_product_search_intent_service import (
        ChatProductSearchIntentService,
    )

    if not ChatProductSearchIntentService.looks_like_product_search(normalized):
        return False

    return bool(
        ChatProductSearchIntentService.extract_search_group_code(normalized, normalized)
    )


class OperationalRouteMatcherService:
    _CUSTOM_PREDICATES: dict[str, Callable[[str], bool]] = {
        "exclusiveRawMaterialCatalog": (
            ChatProductQueryIntentService._looks_like_exclusive_raw_material_catalog_question
        ),
        "factoryStatus": ChatProductQueryIntentService._looks_like_factory_status_question,
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
        "saleOrdersList": _looks_like_sale_orders_list_question,
        "transformaQuestion": _looks_like_transforma_question,
        "systemMetadataQuestion": _looks_like_system_metadata_question,
        "suppliesOtdRoute": _looks_like_supplies_otd_question,
        "productionOtdDetailRoute": _looks_like_production_otd_detail_question,
        "productionOeeDetailRoute": _looks_like_production_oee_detail_question,
        "productionOeeAppointmentRoute": _looks_like_production_oee_appointment_question,
        "productionEficienciaFabrilRoute": _looks_like_production_eficiencia_fabril_question,
        "lmpQuestion": _looks_like_lmp_question,
        "lmpHasSaleNumber": lambda normalized: bool(_extract_lmp_sale_number(normalized)),
        "lmpCatchAll": _looks_like_lmp_catch_all,
        "productSearchQuestion": _looks_like_product_search_question,
        "productSearchWithGroupCode": _looks_like_product_search_with_group_code,
        "priceAnalysisRoute": lambda normalized: ChatProductQueryIntentService._looks_like_price_analysis_question(
            normalized
        ),
        "structureQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_structure_question(
            normalized
        ),
        "stockQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_stock_question(
            normalized
        ),
        "salesQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_sales_question(
            normalized
        ),
        "parentsQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_parents_question(
            normalized
        ),
        "descriptionQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_description_question(
            normalized
        ),
        "productSubIntentRoute": lambda normalized: ChatProductQueryIntentService._looks_like_product_sub_intent(
            normalized
        ),
        "stockScopeResetQuestion": lambda normalized: ChatProductQueryIntentService._looks_like_stock_scope_reset_question(
            normalized
        ),
        "systemHasTableName": _system_has_table_name,
        "systemWantsColumns": _system_wants_columns,
        "systemWantsRelations": _system_wants_relations,
        "systemWantsTableSearch": _system_wants_table_search,
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
            if not cls._match_custom_predicate(
                custom_predicate,
                normalized,
                message=message,
            ):
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

    @classmethod
    def looks_like_sale_orders_list_question(cls, normalized: str) -> bool:
        return _looks_like_sale_orders_list_question(normalized)

    @classmethod
    def looks_like_transforma_question(cls, normalized: str) -> bool:
        return _looks_like_transforma_question(normalized)

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
        return _looks_like_system_metadata_question(normalized)
