"""Parâmetros obrigatórios em consultas operacionais (produto, OV, etc.)."""

from __future__ import annotations

from datetime import date
from functools import lru_cache

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@lru_cache(maxsize=1)
def _parameter_content() -> dict:
    return ChatAssistantContentService.load_bundle("operational_parameters")


class ChatOperationalParameterService:
    """Detecta consultas operacionais incompletas e evita tools/LLM desnecessários."""

    _INTENTS_REQUIRING_CODE = frozenset(
        {
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.STRUCTURE,
            ChatProductQueryIntent.PARENTS,
            ChatProductQueryIntent.DESCRIPTION,
            ChatProductQueryIntent.ANALYSER,
            ChatProductQueryIntent.SUMMARY,
        }
    )

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
        intent = cls._missing_product_code_intent(
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
    def should_skip_tools(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> bool:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ) and ChatConversationContextService.has_recent_tool_data(previous_messages):
            return True

        return cls._missing_product_code_intent(
            message,
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        ) is not None

    @classmethod
    def should_skip_agentic_loop(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        tool_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> bool:
        from app.domain.services.chat_fast_path_service import ChatFastPathService

        if ChatFastPathService.is_small_talk(message):
            return True

        from app.domain.services.chat_follow_up_chip_query_service import (
            ChatFollowUpChipQueryService,
        )

        if ChatFollowUpChipQueryService.is_explicit_chip_query(message):
            return True

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return True

        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatWebSearchIntentService.blocks_external_action_selection(message):
            return True

        if cls.should_skip_tools(message, conversation_context=conversation_context):
            return True

        if ChatOperationalRefinementService.is_operational_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        if not tool_context:
            return False

        from app.application.services.chat_tool_context_service import (
            ChatToolContextService,
        )

        tool_calls = tool_context.get("toolCalls") or []

        if isinstance(tool_context.get("directAnswer"), str) and str(
            tool_context.get("directAnswer") or ""
        ).strip():
            return True

        if ChatToolContextService.should_answer_with_presentation_only(tool_calls):
            return True

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.should_force_llm_synthesis(message, tool_calls):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if metadata.get("agenticStep"):
                continue

            if metadata.get("ok"):
                return True

        return False

    @classmethod
    def should_block_semantic_action_fallback(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
    ) -> bool:
        return cls.should_skip_tools(message, conversation_context=conversation_context)

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

        if intent not in cls._INTENTS_REQUIRING_CODE:
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
    def resolve_ambiguous_period_answer(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
        today: date | None = None,
    ) -> str | None:
        from datetime import date as date_cls

        from app.domain.services.chat_date_range_intent_service import (
            ChatDateRangeIntentService,
        )

        reference = today or date_cls.today()

        if ChatDateRangeIntentService.is_year_clarification_reply(
            message,
            previous_messages,
        ):
            return None

        if not ChatDateRangeIntentService.looks_like_period_metric_question(message):
            return None

        ambiguous = ChatDateRangeIntentService.detect_ambiguous_named_month(
            message,
            today=reference,
        )

        if not ambiguous:
            return None

        template = (_parameter_content().get("ambiguousPeriodYear") or "").strip()

        if template:
            return template.format(
                month_label=ambiguous.month_label,
                current_year=ambiguous.current_year,
                previous_year=ambiguous.previous_year,
            )

        return ChatDateRangeIntentService.build_ambiguity_clarification(
            message,
            today=reference,
        )

    @classmethod
    def should_skip_tools_for_ambiguous_period(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        return cls.resolve_ambiguous_period_answer(
            message,
            previous_messages=previous_messages,
        ) is not None

    @classmethod
    def resolve_missing_date_answer(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        from app.domain.services.chat_operational_date_parameter_service import (
            ChatOperationalDateParameterService,
        )

        return ChatOperationalDateParameterService.resolve_missing_date_answer(
            message,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            conversation_context=conversation_context,
        )

    @classmethod
    def should_skip_tools_for_missing_date(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> bool:
        return cls.resolve_missing_date_answer(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        ) is not None

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
                or any(term in normalized for term in cls._product_context_terms())
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
