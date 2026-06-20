"""Perguntas abertas sobre o produto («me fale do produto X») — narrativa + insights."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_OVERVIEW_BUNDLE = "product_overview_intent"


class ChatProductOverviewIntentService:
    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_OVERVIEW_BUNDLE, *path))

    @classmethod
    def is_product_overview_message(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not ChatProductQueryIntentService.extract_product_code(message or ""):
            return False

        if any(term in normalized for term in cls._terms("narrowTerms")):
            return False

        if ChatProductQueryIntentService._looks_like_stock_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_structure_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_sales_question(normalized):
            return False

        if ChatProductQueryIntentService._looks_like_full_analyser_question(normalized):
            return False

        if any(term in normalized for term in cls._terms("overviewTerms")):
            return True

        if any(marker in normalized for marker in cls._terms("resumoOverviewMarkers")):
            return True

        if cls._me_fale_with_product(normalized):
            return True

        return False

    @classmethod
    def _me_fale_with_product(cls, normalized: str) -> bool:
        import re

        if not re.search(r"\bme fale\b", normalized):
            return False

        return any(token in normalized for token in cls._terms("meFaleProductTokens"))

    @classmethod
    def should_force_llm_synthesis(
        cls,
        message: str | None,
        tool_calls: list | None = None,
    ) -> bool:
        if not cls.is_product_overview_message(message):
            return False

        if not tool_calls:
            return True

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata") or {}

            if metadata.get("ok"):
                return True

        return False

    @classmethod
    def blocks_presentation_only_shortcut(cls, message: str | None) -> bool:
        return cls.is_product_overview_message(message)

    @classmethod
    def build_prompt_policy_addon(
        cls,
        message: str | None,
        *,
        response_mode: str | None = None,
    ) -> str:
        from app.domain.services.chat_operational_narrative_synthesis_service import (
            ChatOperationalNarrativeSynthesisService,
        )

        return ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
            message,
            response_mode=response_mode,
        )

    @classmethod
    def _overview_policy_for_mode(cls, response_mode: str | None) -> str:
        from app.domain.services.chat_response_mode_service import ChatResponseModeService

        normalized = ChatResponseModeService.normalize(response_mode)

        if normalized == "fast":
            return "product-overview-fast.md"

        if normalized == "thinker":
            return "product-overview-thinker.md"

        return "product-overview.md"
