"""Intenção efetiva pós turn-prep (estágios reais do pipeline)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_intent_router.chat_intent_router_classify_service import (
    ChatIntentRouterClassifyService,
)
from app.domain.services.chat_intent_router.chat_intent_router_models import IntentRouteResult
from app.domain.services.chat_intent_router.chat_intent_router_support_service import (
    ChatIntentRouterSupportService,
)


class ChatIntentRouterExecutedService:
    @classmethod
    def resolve_executed(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        analysis_mode: bool = False,
        text_task_pure: bool = False,
        text_task_category: str | None = None,
        skip_rag: bool = False,
        direct_answer: str | None = None,
        tool_calls: list | None = None,
        attachment_ids: list[str] | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> IntentRouteResult:
        """Intenção efetiva após o turn prep (estágios reais do pipeline)."""
        stages = list(pipeline_stages or [])
        predicted = ChatIntentRouterClassifyService.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            attachment_ids=attachment_ids,
            allowed_action_ids=allowed_action_ids,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            analysis_mode=analysis_mode,
        )

        web_executed = ChatIntentRouterSupportService.tool_calls_include_web(tool_calls)

        best: IntentRouteResult | None = None

        for stage in stages:
            if stage.startswith("intent:"):
                continue

            if stage == "tools" and not tool_calls:
                if predicted.intent in {"attachment_document", "attachment_task"}:
                    continue

            mapping = ChatIntentRouterSupportService.STAGE_INTENT.get(stage)

            if not mapping:
                continue

            intent, sub_intent, priority = mapping
            flags: list[str] = [f"stage:{stage}"]

            if stage == "tools" and tool_calls:
                flags.append("tools_executed")

            requires_web = web_executed or predicted.requires_web
            requires_canvas = predicted.requires_canvas or stage == "canvas"

            candidate = IntentRouteResult(
                intent=intent,
                sub_intent=sub_intent or predicted.sub_intent,
                is_follow_up=predicted.is_follow_up,
                confidence=max(predicted.confidence, 0.85),
                requires_tool=bool(tool_calls) or predicted.requires_tool,
                requires_rag=not skip_rag and stage == "rag",
                requires_web=requires_web,
                requires_canvas=requires_canvas,
                requires_llm=not bool(direct_answer)
                or stage
                not in (
                    "small_talk",
                    "utility_direct",
                    "capabilities",
                    "text_task",
                    "unclear_request",
                ),
                priority_applied=priority,
                flags=tuple(flags),
                resolved_params=predicted.resolved_params,
                ambiguous=predicted.ambiguous,
                candidates=predicted.candidates,
                mixed_steps=predicted.mixed_steps,
                decision=predicted.decision,
                reason=predicted.reason,
            )

            if best is None or priority < best.priority_applied:
                best = candidate

        if web_executed and (best is None or best.priority_applied > 7):
            best = ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent="web_search",
                    confidence=0.9,
                    requires_web=True,
                    requires_tool=True,
                    requires_rag=False,
                    requires_llm=not bool(direct_answer),
                    priority_applied=7,
                    flags=("web_search_executed",),
                    resolved_params=predicted.resolved_params,
                ),
                decision="web_search",
                reason="web_search_tool_executed",
            )

        if text_task_pure and (best is None or best.priority_applied > 3):
            sub = text_task_category or predicted.sub_intent
            intent = "email_task" if sub == "email" else "text_task"

            return ChatIntentRouterSupportService.with_decision(
                IntentRouteResult(
                    intent=intent,
                    sub_intent=sub,
                    confidence=0.9,
                    requires_rag=False,
                    requires_llm=True,
                    priority_applied=3,
                    flags=("text_task_pure", "skip_tools"),
                    resolved_params=predicted.resolved_params,
                ),
                decision="skip_tools",
                reason="explicit_text_task",
            )

        if best is not None:
            return ChatIntentRouterSupportService.with_decision(best, decision=best.decision, reason=best.reason)

        return predicted

