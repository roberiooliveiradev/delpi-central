"""Fachada de pesquisa web confiável — Playbook 08 (chat base)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.chat_web_search_planning_service import (
    ChatWebSearchPlanningService,
    WebSearchPlan,
)
from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
    WebSearchQuerySecurityResult,
)
from app.domain.services.chat_web_search_source_evaluation_service import (
    ChatWebSearchSourceEvaluationService,
    WebSourceEvaluation,
)


class ChatWebSearchResearchService:
    """Orquestra intenção, planejamento, segurança e avaliação de fontes."""

    @classmethod
    def should_use_web(
        cls,
        message: str,
        *,
        text_task_pure: bool = False,
    ) -> bool:
        raw = str(message or "").strip()

        if not raw:
            return False

        if ChatIntentRouterService._blocks_web_search(raw):
            return False

        is_explicit_web = ChatWebSearchIntentService.is_explicit_request(raw)

        if not is_explicit_web and (
            text_task_pure or ChatTextTaskIntentService.is_pure_text_task(raw)
        ):
            return False

        return ChatWebSearchIntentService.should_use_web_research(raw)

    @classmethod
    def should_decline_web(cls, message: str) -> bool:
        return ChatIntentRouterService._blocks_web_search(str(message or ""))

    @classmethod
    def plan(
        cls,
        message: str,
        *,
        integration: object | None = None,
    ) -> WebSearchPlan | None:
        if not cls.should_use_web(message):
            return None

        return ChatWebSearchPlanningService.plan(message, integration=integration)

    @classmethod
    def sanitize_query(
        cls,
        message: str,
        *,
        extracted_query: str | None = None,
    ) -> WebSearchQuerySecurityResult:
        return ChatWebSearchQuerySecurityService.sanitize(
            message,
            extracted_query=extracted_query,
        )

    @classmethod
    def evaluate_source(cls, url: str, *, title: str = "") -> WebSourceEvaluation:
        return ChatWebSearchSourceEvaluationService.evaluate_url(url, title=title)

    @classmethod
    def source_quality_metadata(cls, evaluation: WebSourceEvaluation) -> dict[str, Any]:
        confidence = "high"

        if evaluation.quality_score < 0.5:
            confidence = "low"
        elif evaluation.quality_score < 0.8:
            confidence = "medium"

        type_map = {
            "manufacturer": "official_manufacturer",
            "government": "government",
            "official": "official_pdf",
            "recognized_distributor": "recognized_distributor",
            "technical_article": "technical_article",
            "news": "news",
            "forum": "forum",
            "unknown": "unknown",
        }

        return {
            "hostname": evaluation.hostname,
            "type": type_map.get(evaluation.source_type, evaluation.source_type),
            "confidence": confidence,
        }

    @classmethod
    def resolve_tool_selection(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        if not cls.should_use_web(message):
            return None

        return ChatWebSearchIntentService.resolve(
            message,
            attachment_context=attachment_context,
            previous_messages=previous_messages,
        )
