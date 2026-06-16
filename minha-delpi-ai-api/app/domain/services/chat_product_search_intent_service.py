"""Intenção de busca de produtos por descrição ou grupo — vocabulário JSON."""

from __future__ import annotations

import re

from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatProductSearchIntentService:
    @staticmethod
    def looks_like_product_search(value: str) -> bool:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )

        if ChatSqlIntentService.is_sql_conversation_turn(value):
            return False

        if ChatWebSearchIntentService.matches(value):
            return False

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(value):
            return False

        if ChatSqlOperationalIntentService.requires_sql_knowledge(value):
            return False

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(value):
            return False

        audit5s_terms = ExternalActionResponseContentService.list(
            "actionSelection",
            "productSearch",
            "audit5sExcludeTerms",
        )

        if any(term in value for term in audit5s_terms):
            return False

        search_triggers = ExternalActionResponseContentService.list(
            "actionSelection",
            "productSearch",
            "searchTriggers",
        )
        product_context = ExternalActionResponseContentService.list(
            "actionSelection",
            "productSearch",
            "productContextTerms",
        )

        has_trigger = any(term in value for term in search_triggers)
        has_product_context = any(term in value for term in product_context)

        if has_trigger and has_product_context:
            return True

        if has_trigger and len(value.split()) >= 3:
            exclude_terms = ExternalActionResponseContentService.list(
                "actionSelection",
                "productSearch",
                "broadSearchExcludeTerms",
            )

            if not any(term in value for term in exclude_terms):
                return True

        return False

    @staticmethod
    def extract_search_group_code(message: str, normalized: str) -> str | None:
        patterns = (
            r"\bgrupo\s+de\s+produtos?\s+([A-Za-z0-9]{1,12})\b",
            r"\bgrupo\s+([A-Za-z0-9]{1,12})\b",
            r"\bgroup_code\s+([A-Za-z0-9]{1,12})\b",
            r"\bdo\s+grupo\s+([A-Za-z0-9]{1,12})\b",
            r"\bpelo\s+grupo\s+([A-Za-z0-9]{1,12})\b",
        )

        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)

            if match:
                code = str(match.group(1)).strip().upper()

                if code.lower() in {"de", "do", "da", "produto", "produtos"}:
                    continue

                return code

        return None
