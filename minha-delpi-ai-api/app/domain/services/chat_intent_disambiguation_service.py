"""Desambiguação de consulta operacional (Playbook 02 §20–21, §25)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_INTENT_DISAMBIGUATION_BUNDLE = "intent_disambiguation"


class ChatIntentDisambiguationService:
    @classmethod
    def _scope_options(cls) -> tuple[tuple[str, str, str], ...]:
        raw = ChatAssistantContentService.get_node(
            _INTENT_DISAMBIGUATION_BUNDLE,
            "scopeOptions",
        )

        if not isinstance(raw, list):
            return ()

        options: list[tuple[str, str, str]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or "").strip()
            sub_intent = str(item.get("subIntent") or "").strip()
            query_template = str(item.get("queryTemplate") or "").strip()

            if label and sub_intent and query_template:
                options.append((label, sub_intent, query_template))

        return tuple(options)

    @classmethod
    def try_build(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_intent_router_service import ChatIntentRouterService

        route = ChatIntentRouterService.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
        )

        if not route.ambiguous or route.intent != "operational_query":
            return None

        product_code = str((route.resolved_params or {}).get("productCode") or "").strip()

        if not product_code:
            return None

        suggestions = cls.build_suggestions(product_code)
        direct_answer = ChatAssistantContentService.format(
            _INTENT_DISAMBIGUATION_BUNDLE,
            "directAnswer",
            productCode=product_code,
        )

        if not direct_answer:
            return None

        return {
            "directAnswer": direct_answer,
            "suggestions": suggestions,
            "productCode": product_code,
            "intentRoute": route.to_dict(),
        }

    @classmethod
    def build_suggestions(cls, product_code: str) -> list[dict[str, str]]:
        code = str(product_code or "").strip()
        suggestions: list[dict[str, str]] = []

        for label, _sub_intent, template in cls._scope_options():
            query = template.format(productCode=code)

            suggestions.append({"label": label, "query": query, "subIntent": _sub_intent})

        return suggestions
