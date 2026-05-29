"""Parâmetros obrigatórios em consultas operacionais (produto, OV, etc.)."""

from __future__ import annotations

from functools import lru_cache

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
from app.infrastructure.content.content_service import ContentService

_PRODUCT_CONTEXT_TERMS = (
    "produto",
    "product",
    "item",
    "material",
    "insumo",
    "sku",
    "código",
    "codigo",
)


@lru_cache(maxsize=1)
def _parameter_content() -> dict:
    return ContentService.load_json("assistant/operational_parameters")


class ChatOperationalParameterService:
    """Detecta consultas operacionais incompletas e evita tools/LLM desnecessários."""

    _INTENTS_REQUIRING_CODE = frozenset(
        {
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.STRUCTURE,
            ChatProductQueryIntent.PARENTS,
            ChatProductQueryIntent.DESCRIPTION,
        }
    )

    @classmethod
    def resolve_missing_product_code_answer(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
    ) -> str | None:
        intent = cls._missing_product_code_intent(message, conversation_context)

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
    ) -> bool:
        return cls._missing_product_code_intent(message, conversation_context) is not None

    @classmethod
    def should_skip_agentic_loop(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        tool_context: dict | None = None,
        previous_messages: list | None = None,
    ) -> bool:
        if cls.should_skip_tools(message, conversation_context=conversation_context):
            return True

        return ChatOperationalRefinementService.is_operational_follow_up(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

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
    ) -> str | None:
        message = ChatMessageNormalizationService.normalize_for_matching(message) or message
        normalized = message

        if ChatProductQueryIntentService.extract_product_code(message):
            return None

        intent = ChatProductQueryIntentService.detect(message)

        if intent not in cls._INTENTS_REQUIRING_CODE:
            return None

        if not cls._requires_explicit_product_context(normalized, intent):
            return None

        # «estoque do produto» sem código explícito não herda exemplo do assistente.
        if not ChatProductQueryIntentService.references_previous_product(message):
            return intent

        product_code = ChatProductQueryIntentService.resolve_product_code(
            message,
            conversation_context,
        )

        if product_code:
            return None

        return intent

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
                or any(term in normalized for term in _PRODUCT_CONTEXT_TERMS)
            )

        return False
