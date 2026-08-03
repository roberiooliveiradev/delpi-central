"""Clarificação quando select_action retorna None e o intent exige tool."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionCatalogMissClarificationService:
    @classmethod
    def resolve_direct_answer(
        cls,
        message: str,
        *,
        allowed_action_ids: list[str] | None,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
    ) -> str | None:
        if not allowed_action_ids:
            return None

        route = ChatIntentRouterService.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
        )

        if not route.requires_tool:
            return None

        if route.intent in {"assistant_identity", "capabilities", "llm_general", "rag"}:
            return None

        answer = ExternalActionResponseContentService.get(
            "actionSelection",
            "routeClarification",
            "catalogMissDirectAnswer",
        )
        return answer.strip() or None
