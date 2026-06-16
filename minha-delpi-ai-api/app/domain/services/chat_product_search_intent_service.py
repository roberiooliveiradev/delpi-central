"""Intenção de busca de produtos por descrição ou grupo — vocabulário JSON."""

from __future__ import annotations

import re

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatProductSearchIntentService:
    @staticmethod
    def looks_like_product_search(value: str) -> bool:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        normalized = str(value or "")

        return ChatProductRoutePredicateService.matches(
            "productSearchQuestion",
            normalized,
            message=normalized,
        )

    @staticmethod
    def extract_search_group_code(message: str, normalized: str) -> str | None:
        patterns = ExternalActionResponseContentService.list(
            "actionSelection",
            "productSearch",
            "groupCodePatterns",
        )
        exclude_tokens = {
            str(token).strip().lower()
            for token in ExternalActionResponseContentService.list(
                "actionSelection",
                "productSearch",
                "groupCodeExcludeTokens",
            )
            if str(token).strip()
        }

        for pattern in patterns:
            match = re.search(str(pattern), message, flags=re.IGNORECASE)

            if match:
                code = str(match.group(1)).strip().upper()

                if code.lower() in exclude_tokens:
                    continue

                return code

        return None
