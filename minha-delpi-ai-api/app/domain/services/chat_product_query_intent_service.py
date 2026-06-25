"""Fachada pública — intenção de consulta de produto (DOCIE)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_product_query_intent.chat_product_query_intent_code_service import (
    ChatProductQueryIntentCodeService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_context_service import (
    ChatProductQueryIntentContextService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_direct_answer_service import (
    ChatProductQueryIntentDirectAnswerService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_models import (
    ChatProductQueryIntent,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_predicate_service import (
    ChatProductQueryIntentPredicateService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_resolution_service import (
    ChatProductQueryIntentResolutionService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_support_service import (
    ChatProductQueryIntentSupportService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_vocabulary import (
    ChatProductQueryIntentVocabulary,
)
from app.domain.services.chat_product_query_intent_detection_service import (
    ChatProductQueryIntentDetectionService,
)

__all__ = ["ChatProductQueryIntent", "ChatProductQueryIntentService"]


class ChatProductQueryIntentService:
    """API estável — detect, resolução de código/intent e predicados de rota."""

    _ZERO_RECORDS_RE = ChatProductQueryIntentVocabulary.ZERO_RECORDS_RE
    _PRODUCT_CODE_RE = ChatProductQueryIntentVocabulary.PRODUCT_CODE_RE
    _CALENDAR_YEAR_RE = ChatProductQueryIntentVocabulary.CALENDAR_YEAR_RE

    @classmethod
    def detect(cls, message: str) -> str:
        return ChatProductQueryIntentDetectionService.detect(message)

    @classmethod
    def refine_operational_intent_from_full(
        cls,
        message: str,
        *,
        normalized: str | None = None,
    ) -> str:
        return ChatProductQueryIntentDetectionService.refine_operational_intent_from_full(
            message,
            normalized=normalized,
        )

    @classmethod
    def references_previous_product(cls, message: str) -> bool:
        return ChatProductQueryIntentContextService.references_previous_product(message)

    @classmethod
    def looks_like_scope_reset_operational_query(cls, message: str | None) -> bool:
        return ChatProductQueryIntentContextService.looks_like_scope_reset_operational_query(
            message
        )

    @classmethod
    def should_inherit_product_code(cls, message: str | None) -> bool:
        return ChatProductQueryIntentContextService.should_inherit_product_code(message)

    @classmethod
    def infer_intent_from_recent_tool(cls, previous_messages: list | None) -> str | None:
        return ChatProductQueryIntentContextService.infer_intent_from_recent_tool(
            previous_messages
        )

    @classmethod
    def normalize_product_code(cls, raw: str) -> str:
        return ChatProductQueryIntentCodeService.normalize_product_code(raw)

    @classmethod
    def is_plausible_product_code(cls, code: str | None) -> bool:
        return ChatProductQueryIntentCodeService.is_plausible_product_code(code)

    @classmethod
    def extract_product_code(cls, text: str | None) -> str | None:
        return ChatProductQueryIntentCodeService.extract_product_code(text)

    @classmethod
    def extract_product_group_code(cls, text: str | None) -> str | None:
        return ChatProductQueryIntentCodeService.extract_product_group_code(text)

    @classmethod
    def extract_last_product_code(cls, text: str | None) -> str | None:
        return ChatProductQueryIntentCodeService.extract_last_product_code(text)

    @classmethod
    def extract_last_product_code_from_messages(
        cls,
        previous_messages: list | None,
    ) -> str | None:
        return ChatProductQueryIntentCodeService.extract_last_product_code_from_messages(
            previous_messages
        )

    @classmethod
    def looks_like_production_schedule_membership_question(cls, message: str | None) -> bool:
        return ChatProductQueryIntentCodeService.looks_like_production_schedule_membership_question(
            message
        )

    @classmethod
    def looks_like_structure_exclusivity_question(cls, message: str | None) -> bool:
        return ChatProductQueryIntentPredicateService.looks_like_structure_exclusivity_question(
            message
        )

    @classmethod
    def resolve_schedule_product_group_code(cls, *args, **kwargs) -> str | None:
        return ChatProductQueryIntentCodeService.resolve_schedule_product_group_code(
            *args, **kwargs
        )

    @classmethod
    def resolve_schedule_product_filter_code(cls, *args, **kwargs) -> str | None:
        return ChatProductQueryIntentCodeService.resolve_schedule_product_filter_code(
            *args, **kwargs
        )

    @classmethod
    def resolve_product_intent(cls, *args, **kwargs) -> str:
        return ChatProductQueryIntentResolutionService.resolve_product_intent(*args, **kwargs)

    @classmethod
    def resolve_product_code(cls, *args, **kwargs) -> str | None:
        return ChatProductQueryIntentResolutionService.resolve_product_code(*args, **kwargs)

    @classmethod
    def format_direct_answer(cls, *args, **kwargs) -> str | None:
        return ChatProductQueryIntentDirectAnswerService.format_direct_answer(*args, **kwargs)

    @classmethod
    def has_actionable_product_route_intent(cls, *args, **kwargs) -> bool:
        return ChatProductQueryIntentPredicateService.has_actionable_product_route_intent(
            *args, **kwargs
        )

    # --- Conteúdo / predicados (consumidores legados) ---

    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return ChatProductQueryIntentContentService._terms(*path)

    @classmethod
    def _header(cls, key: str, *, default: str = "") -> str:
        return ChatProductQueryIntentContentService._header(key, default=default)

    @classmethod
    def _matches_predicate(cls, predicate: str, normalized: str) -> bool:
        return ChatProductQueryIntentContentService._matches_predicate(predicate, normalized)

    @classmethod
    def _matches_any_predicates(
        cls,
        predicates: list[str] | tuple[str, ...],
        normalized: str,
    ) -> bool:
        return ChatProductQueryIntentContentService._matches_any_predicates(
            predicates,
            normalized,
        )

    @classmethod
    def _matches_product_predicate(cls, predicate: str, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_product_predicate(
            predicate,
            normalized,
        )

    @classmethod
    def _matches_route_predicate(cls, predicate: str, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._matches_route_predicate(
            predicate,
            normalized,
        )

    @classmethod
    def _looks_like_mixed_documental_operational(cls, normalized: str) -> bool:
        return ChatProductQueryIntentContextService._looks_like_mixed_documental_operational(
            normalized
        )

    @classmethod
    def _looks_like_explicit_playbook_product_scope(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_explicit_playbook_product_scope(
            normalized
        )

    @classmethod
    def _looks_like_stock_scope_reset_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_stock_scope_reset_question(
            normalized
        )

    @classmethod
    def _looks_like_sales_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_sales_question(normalized)

    @classmethod
    def _looks_like_stock_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_stock_question(normalized)

    @classmethod
    def _has_product_scope_reference(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._has_product_scope_reference(normalized)

    @classmethod
    def _looks_like_billing_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_billing_question(normalized)

    @classmethod
    def _looks_like_factory_status_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_factory_status_question(
            normalized
        )

    @classmethod
    def _looks_like_production_status_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_production_status_question(
            normalized
        )

    @classmethod
    def _looks_like_shipping_status_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_shipping_status_question(
            normalized
        )

    @classmethod
    def _looks_like_exclusive_raw_material_catalog_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_exclusive_raw_material_catalog_question(
            normalized
        )

    @classmethod
    def _looks_like_structure_exclusivity_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_structure_exclusivity_question(
            normalized
        )

    @classmethod
    def _looks_like_sale_pricing_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_sale_pricing_question(normalized)

    @classmethod
    def _looks_like_price_analysis_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_price_analysis_question(
            normalized
        )

    @classmethod
    def _looks_like_raw_material_price_intelligence_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_raw_material_price_intelligence_question(
            normalized
        )

    @classmethod
    def _looks_like_cost_impact_simulation_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_cost_impact_simulation_question(
            normalized
        )

    @classmethod
    def _looks_like_directives_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_directives_question(normalized)

    @classmethod
    def _looks_like_last_purchase_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_last_purchase_question(
            normalized
        )

    @classmethod
    def _looks_like_purchase_price_history_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_purchase_price_history_question(
            normalized
        )

    @classmethod
    def _looks_like_purchase_budget_history_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_purchase_budget_history_question(
            normalized
        )

    @classmethod
    def _looks_like_generic_product_analysis_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_generic_product_analysis_question(
            normalized
        )

    @classmethod
    def _looks_like_full_analyser_question(cls, message: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_full_analyser_question(message)

    @classmethod
    def _looks_like_product_summary_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_product_summary_question(
            normalized
        )

    @classmethod
    def _looks_like_description_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_description_question(normalized)

    @classmethod
    def _looks_like_purchases_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_purchases_route_question(
            normalized
        )

    @classmethod
    def _looks_like_product_summary_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_product_summary_route_question(
            normalized
        )

    @classmethod
    def _looks_like_guide_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_guide_route_question(normalized)

    @classmethod
    def _looks_like_generic_pricing_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_generic_pricing_route_question(
            normalized
        )

    @classmethod
    def _looks_like_invoices_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_invoices_route_question(
            normalized
        )

    @classmethod
    def _looks_like_suppliers_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_suppliers_route_question(
            normalized
        )

    @classmethod
    def _looks_like_inspection_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_inspection_route_question(
            normalized
        )

    @classmethod
    def _looks_like_inbound_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_inbound_invoice_route_question(
            normalized
        )

    @classmethod
    def _looks_like_outbound_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_outbound_invoice_route_question(
            normalized
        )

    @classmethod
    def _looks_like_generic_invoice_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_generic_invoice_route_question(
            normalized
        )

    @classmethod
    def _looks_like_customers_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_customers_route_question(
            normalized
        )

    @classmethod
    def _looks_like_internal_movements_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_internal_movements_route_question(
            normalized
        )

    @classmethod
    def _looks_like_open_orders_route_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_open_orders_route_question(
            normalized
        )

    @classmethod
    def _looks_like_parents_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_parents_question(normalized)

    @classmethod
    def _looks_like_structure_question(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_structure_question(normalized)

    @classmethod
    def _looks_like_product_sub_intent(cls, normalized: str) -> bool:
        return ChatProductQueryIntentPredicateService._looks_like_product_sub_intent(normalized)

    @classmethod
    def _is_group_code_numeric_token(cls, text: str, match) -> bool:
        return ChatProductQueryIntentCodeService._is_group_code_numeric_token(text, match)

    @classmethod
    def _is_date_numeric_token(cls, token: str) -> bool:
        return ChatProductQueryIntentCodeService._is_date_numeric_token(token)

    @classmethod
    def _is_example_product_code_token(cls, text: str, match) -> bool:
        return ChatProductQueryIntentCodeService._is_example_product_code_token(text, match)

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        return ChatProductQueryIntentSupportService._message_metadata(message)

    @classmethod
    def _message_content(cls, message: Any) -> str:
        return ChatProductQueryIntentSupportService._message_content(message)

    @classmethod
    def _message_field_role(cls, message: Any) -> str:
        return ChatProductQueryIntentSupportService._message_field_role(message)
