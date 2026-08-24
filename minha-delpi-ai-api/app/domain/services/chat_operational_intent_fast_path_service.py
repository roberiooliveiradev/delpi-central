"""Fast-path operacional: código de produto + intent com intentBinding no registry."""

from __future__ import annotations

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)

_INTENT_BOUND_INTENTS = frozenset(
    {
        ChatProductQueryIntent.PARENTS,
        ChatProductQueryIntent.STRUCTURE,
        ChatProductQueryIntent.STOCK,
        ChatProductQueryIntent.SALES,
        ChatProductQueryIntent.SUMMARY,
        ChatProductQueryIntent.ANALYSER,
        ChatProductQueryIntent.DESCRIPTION,
    }
)

_REGISTRY_INTENT_BINDINGS = frozenset(
    {
        str(route.get("intentBinding") or "").strip().lower()
        for route in OperationalRouteRegistryService.intent_bound_routes()
        if str(route.get("intentBinding") or "").strip()
    }
)


class ChatOperationalIntentFastPathService:
    @classmethod
    def registry_intent_bindings(cls) -> frozenset[str]:
        return _REGISTRY_INTENT_BINDINGS

    @classmethod
    def is_intent_bound_eligible(cls, intent: str | None) -> bool:
        normalized = str(intent or "").strip().lower()

        if not normalized or normalized == ChatProductQueryIntent.FULL:
            return False

        return normalized in _INTENT_BOUND_INTENTS and normalized in _REGISTRY_INTENT_BINDINGS

    @classmethod
    def resolve_operational_fast_path(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
        forced_product_code: str | None = None,
        forced_intent: str | None = None,
    ) -> tuple[str | None, str | None]:
        product_code = (
            str(forced_product_code).strip()
            if forced_product_code
            else ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
            )
        )
        intent = (
            str(forced_intent).strip()
            if forced_intent
            else ChatProductQueryIntentService.resolve_product_intent(
                message,
                previous_messages=previous_messages,
            )
        )

        if not product_code or not cls.is_intent_bound_eligible(intent):
            return None, None

        return product_code, intent

    @classmethod
    def should_skip_llm_tool_selection(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
        drawing_analysis_mode: bool = False,
        web_search_exclusive: bool = False,
    ) -> bool:
        if drawing_analysis_mode or web_search_exclusive:
            return False

        product_code, intent = cls.resolve_operational_fast_path(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        return bool(product_code and intent)
