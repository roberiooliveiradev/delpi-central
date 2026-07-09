"""Delegate — intenção de consulta de produto."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_facade_access import (
    intent_service,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_models import (
    ChatProductQueryIntent,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_vocabulary import (
    ChatProductQueryIntentVocabulary as VOCAB,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"



class ChatProductQueryIntentPredicateService:
    @classmethod
    def looks_like_structure_exclusivity_question(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return cls._looks_like_structure_exclusivity_question(normalized)

    @classmethod
    def _looks_like_explicit_playbook_product_scope(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )

        return ChatProductQueryIntentDetectionService.looks_like_explicit_playbook_product_scope(
            normalized
        )

    @classmethod
    def _looks_like_stock_scope_reset_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("stockScopeResetQuestion", normalized)

    @classmethod
    def _looks_like_sales_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("salesQuestion", normalized)

    @classmethod
    def _looks_like_stock_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("stockQuestion", normalized)

    @classmethod
    def _has_product_scope_reference(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return bool(
            intent_service().extract_product_code(normalized)
            or ChatProductPluralPhrasingService.has_product_entity_reference(
                normalized
            )
        )

    @classmethod
    def _looks_like_billing_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return ChatProductRoutePredicateService.matches("billingRoute", normalized)

    @classmethod
    def _looks_like_factory_status_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("factoryStatus", normalized)

    @classmethod
    def _looks_like_production_status_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("productionStatus", normalized)

    @classmethod
    def _looks_like_production_status_date_required(cls, normalized: str) -> bool:
        if not normalized:
            return False

        return any(
            term in normalized
            for term in ChatAssistantContentService.list(
                "product_query_intent",
                "productionStatus",
                "dateRequiredTerms",
            )
        )

    @classmethod
    def _looks_like_shipping_status_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("shippingStatus", normalized)

    @classmethod
    def _looks_like_exclusive_raw_material_catalog_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("exclusiveRawMaterialCatalog", normalized)

    @classmethod
    def _looks_like_structure_exclusivity_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("structureExclusivity", normalized)

    @classmethod
    def _looks_like_sale_pricing_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("salePricingRoute", normalized)

    @classmethod
    def _looks_like_price_analysis_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("priceAnalysisRoute", normalized)

    @classmethod
    def _looks_like_raw_material_price_intelligence_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("rawMaterialPriceIntelligence", normalized)

    @classmethod
    def _looks_like_cost_impact_simulation_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("costImpactSimulation", normalized)

    @classmethod
    def _looks_like_directives_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("directives", normalized)

    @classmethod
    def _looks_like_last_purchase_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("lastPurchase", normalized)

    @classmethod
    def _looks_like_purchase_price_history_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("purchasePriceHistory", normalized)

    @classmethod
    def _looks_like_purchase_budget_history_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("purchaseBudgetHistory", normalized)

    @classmethod
    def _looks_like_generic_product_analysis_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )

        return (
            ChatProductQueryIntentDetectionService.looks_like_generic_product_analysis_question(
                normalized
            )
        )

    @classmethod
    def _looks_like_full_analyser_question(cls, message: str) -> bool:
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )

        return ChatProductQueryIntentDetectionService.looks_like_full_analyser_question(
            message
        )

    @classmethod
    def _looks_like_product_summary_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )

        return ChatProductQueryIntentDetectionService.looks_like_product_summary_question(
            normalized
        )

    @classmethod
    def _looks_like_description_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("descriptionQuestion", normalized)

    @classmethod
    def has_actionable_product_route_intent(cls,
        message: str,
        *,
        normalized: str | None = None,
        route_segment: str | None = None,
    ) -> bool:
        """Indica se a mensagem tem escopo operacional explícito para ranking heurístico."""
        if route_segment:
            return True

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if (
            intent_service().refine_operational_intent_from_full(message, normalized=normalized_text)
            != ChatProductQueryIntent.FULL
        ):
            return True

        from app.domain.services.operational_route_registry_service import (
            OperationalRouteRegistryService,
        )
        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        if any(
            OperationalRouteMatcherService.matches_custom_predicate(
                predicate,
                normalized_text,
            )
            for predicate in OperationalRouteRegistryService.actionable_product_predicates()
        ):
            return True

        if cls._looks_like_full_analyser_question(message):
            return True

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.is_product_overview_message(message):
            return True

        return False

    @classmethod
    def _matches_product_predicate(cls, predicate: str, normalized: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return ChatProductRoutePredicateService.matches(predicate, normalized)

    @classmethod
    def _matches_route_predicate(cls, predicate: str, normalized: str) -> bool:
        return cls._matches_product_predicate(predicate, normalized)

    @classmethod
    def _looks_like_purchases_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("purchasesRoute", normalized)

    @classmethod
    def _looks_like_product_summary_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("productSummaryRoute", normalized)

    @classmethod
    def _looks_like_guide_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("guideRoute", normalized)

    @classmethod
    def _looks_like_generic_pricing_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("genericPricingRoute", normalized)

    @classmethod
    def _looks_like_invoices_route_question(cls, normalized: str) -> bool:
        return any(term in normalized for term in ChatProductQueryIntentContentService._terms("invoices", "terms"))

    @classmethod
    def _looks_like_suppliers_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("suppliersRoute", normalized)

    @classmethod
    def _looks_like_inspection_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("inspectionRoute", normalized)

    @classmethod
    def _looks_like_inbound_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("inboundInvoiceRoute", normalized)

    @classmethod
    def _looks_like_outbound_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("outboundInvoiceRoute", normalized)

    @classmethod
    def _looks_like_generic_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("genericInvoiceRoute", normalized)

    @classmethod
    def _looks_like_customers_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("customersRoute", normalized)

    @classmethod
    def _looks_like_internal_movements_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("internalMovementsRoute", normalized)

    @classmethod
    def _looks_like_open_orders_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate("openOrdersRoute", normalized)

    @classmethod
    def _looks_like_parents_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("parentsQuestion", normalized)

    @classmethod
    def _looks_like_structure_question(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("structureQuestion", normalized)

    @classmethod
    def _looks_like_product_sub_intent(cls, normalized: str) -> bool:
        return cls._matches_product_predicate("productSubIntentRoute", normalized)

