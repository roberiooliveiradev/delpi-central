"""Heurísticas de despacho em external_action_selection — Fase 3B lote 21."""

from __future__ import annotations

from typing import Callable

from app.application.services.external_actions.external_action_domain_route_selection_service import (
    ExternalActionDomainRouteSelectionService,
)
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionSelectionHeuristicsService:
    @staticmethod
    def looks_like_product_question(value: str) -> bool:
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productQuestionTerms",
        )

        return any(term in value for term in terms)

    @staticmethod
    def looks_like_lmp_question(
        value: str,
        *,
        extract_sale_number: Callable[[str | None], str | None] | None = None,
    ) -> bool:
        if ExternalActionDomainRouteSelectionService.looks_like_transforma_question(value):
            return False

        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "lmpQuestion",
            "terms",
        )

        if any(term in value for term in terms):
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

        if any(phrase in value for phrase in sale_order_phrases):
            return any(marker in value for marker in sale_order_markers) or bool(
                extract_sale_number(value) if extract_sale_number else None
            )

        return False

    @staticmethod
    def looks_like_sql_or_data_query(message: str) -> bool:
        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return True

        normalized = str(message or "").lower()
        terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "sqlOrDataQueryTerms",
        )

        return any(term in normalized for term in terms)
