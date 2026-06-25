"""Delegate — parâmetros operacionais."""

from __future__ import annotations

from datetime import date

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_constants import (
    INTENTS_REQUIRING_CODE,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_facade_access import (
    operational_parameter_service,
)
from app.domain.services.chat_operational_parameter.chat_operational_parameter_types import (
    _parameter_content,
)



class ChatOperationalParameterProductCodeService:
    @classmethod
    def _product_context_terms(cls) -> tuple[str, ...]:
        return tuple(_parameter_content().get("productContextTerms") or [])

    @classmethod
    def resolve_missing_product_code_answer(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        intent = operational_parameter_service()._missing_product_code_intent(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if not intent:
            return None

        templates = (_parameter_content().get("missingProductCode") or {})
        return (
            templates.get(intent)
            or templates.get("default")
            or (
                "Para consultar dados do produto, informe o código "
                "(ex.: 10080099)."
            )
        )

    @classmethod
    def _missing_product_code_intent(
        cls,
        message: str,
        conversation_context: str | None,
        *,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        message = ChatMessageNormalizationService.normalize_for_matching(message) or message
        normalized = message

        if ChatProductQueryIntentService._looks_like_exclusive_raw_material_catalog_question(
            normalized
        ):
            return None

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return None

        if ChatProductQueryIntentService.extract_product_code(message):
            return None

        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            if not ChatProductQueryIntentService.references_previous_product(message):
                inherited = ChatProductQueryIntentService.resolve_product_code(
                    message,
                    conversation_context,
                    previous_messages=previous_messages,
                    memory_snapshot=memory_snapshot,
                )

                if not inherited:
                    return None

        intent = ChatProductQueryIntentService.detect(message)
        playbook_sub_intent = None

        if intent not in INTENTS_REQUIRING_CODE:
            playbook_sub_intent = cls._playbook_missing_product_code_sub_intent(normalized)

            if not playbook_sub_intent:
                return None
        elif not cls._requires_explicit_product_context(normalized, intent):
            return None

        if previous_messages:
            code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
                previous_messages,
            )

            if code:
                return None

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if product_code:
            return None

        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )
        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        context_codes: list[str] = []

        if isinstance(memory_snapshot, dict):
            context_codes = ChatUserContextItemService.resolve_all_product_codes_from_items(
                memory_snapshot.get("userContextItems"),
            )

        if not context_codes and conversation_context:
            context_codes = ChatUserContextItemService.resolve_all_product_codes_from_context_prompt(
                conversation_context,
            )

        if (
            context_codes
            and ChatAnalysisIntentService._message_uses_active_context_products(message)
        ):
            return None

        # «estoque do produto» sem código explícito não herda exemplo do assistente.
        if not ChatProductQueryIntentService.references_previous_product(message):
            if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
                return None

            return playbook_sub_intent or intent

        return playbook_sub_intent or intent

    @classmethod
    def _playbook_missing_product_code_sub_intent(cls, normalized: str) -> str | None:
        checks = (
            (
                ChatProductQueryIntentService._looks_like_raw_material_price_intelligence_question,
                "raw_material_price_intelligence",
            ),
            (
                ChatProductQueryIntentService._looks_like_cost_impact_simulation_question,
                "cost_impact_simulation",
            ),
            (
                ChatProductQueryIntentService._looks_like_last_purchase_question,
                "last_purchase",
            ),
            (
                ChatProductQueryIntentService._looks_like_purchase_price_history_question,
                "purchase_price_history",
            ),
            (
                ChatProductQueryIntentService._looks_like_purchase_budget_history_question,
                "purchase_budget_history",
            ),
            (
                ChatProductQueryIntentService._looks_like_sale_pricing_question,
                "sale_pricing",
            ),
            (
                ChatProductQueryIntentService._looks_like_structure_exclusivity_question,
                "structure_exclusivity",
            ),
        )

        for matcher, sub_intent in checks:
            if matcher(normalized):
                return sub_intent

        return None

    @classmethod
    def _requires_explicit_product_context(cls, normalized: str, intent: str) -> bool:
        if intent == ChatProductQueryIntent.STOCK:
            return ChatProductQueryIntentService._looks_like_stock_question(normalized)

        if intent == ChatProductQueryIntent.STRUCTURE:
            return ChatProductQueryIntentService._looks_like_structure_question(normalized)

        if intent == ChatProductQueryIntent.PARENTS:
            return ChatProductQueryIntentService._looks_like_parents_question(normalized)

        if intent == ChatProductQueryIntent.DESCRIPTION:
            return (
                ChatProductQueryIntentService._looks_like_description_question(normalized)
                or any(term in normalized for term in operational_parameter_service()._product_context_terms())
            )

        if intent == ChatProductQueryIntent.ANALYSER:
            return ChatProductQueryIntentService._looks_like_full_analyser_question(
                normalized
            ) or ChatProductQueryIntentService._looks_like_product_summary_question(
                normalized
            )

        if intent == ChatProductQueryIntent.SUMMARY:
            return ChatProductQueryIntentService._looks_like_product_summary_question(
                normalized
            )

        return False

