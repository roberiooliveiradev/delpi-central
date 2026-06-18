"""Montagem de intent route e resultado final do turno — Fase 3C lote 20."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.domain.services.chat_intent_router_service import ChatIntentRouterService


class ChatTurnPreparationResultService:
    @classmethod
    def finalize(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        history_source: list,
        workspace_context: dict,
        analysis_mode: bool,
        text_task_pure: bool,
        text_task_category: str | None,
        skip_rag: bool,
        direct_answer: str | None,
        tool_calls: list,
        request_attachment_ids: list[str],
        allowed_action_ids: list[str],
        operational_optimize: bool,
        fast_path: bool,
        history: list,
        history_summary: str,
        tool_context: dict,
        rag: dict,
        sources: list,
        canvas_open_payload,
        pipeline_timings: ChatPipelineTimings,
        email_writing_mode: bool,
        email_subtype: str | None,
        text_correction_mode: bool,
        text_correction_subtype: str | None,
        routing_disambiguation_suggestions: list | None,
    ) -> Any:
        from app.application.services.chat_turn.chat_turn_preparation_service import (
            ChatTurnPreparationResult,
        )

        intent_route = ChatIntentRouterService.resolve_executed(
            message=message,
            pipeline_stages=pipeline_stages,
            previous_messages=history_source,
            workspace_context=workspace_context,
            analysis_mode=bool(analysis_mode),
            text_task_pure=bool(text_task_pure),
            text_task_category=text_task_category if text_task_pure else None,
            skip_rag=bool(skip_rag),
            direct_answer=direct_answer,
            tool_calls=tool_calls,
            attachment_ids=request_attachment_ids or None,
            allowed_action_ids=allowed_action_ids,
        ).to_dict()

        if f"intent:{intent_route['intent']}" not in pipeline_stages:
            pipeline_stages.append(f"intent:{intent_route['intent']}")

        return ChatTurnPreparationResult(
            operational_optimize=bool(operational_optimize),
            analysis_mode=bool(analysis_mode),
            fast_path=bool(fast_path),
            skip_rag=bool(skip_rag),
            history=history,
            history_summary=history_summary,
            tool_context=tool_context,
            tool_calls=tool_calls,
            direct_answer=direct_answer,
            rag=rag,
            sources=sources,
            canvas_open_payload=canvas_open_payload,
            pipeline_timings=pipeline_timings,
            pipeline_stages=pipeline_stages,
            text_task_mode=bool(text_task_pure),
            text_task_category=text_task_category if text_task_pure else None,
            email_writing_mode=bool(email_writing_mode),
            email_subtype=email_subtype,
            text_correction_mode=bool(text_correction_mode),
            text_correction_subtype=text_correction_subtype,
            intent_route=intent_route,
            routing_disambiguation_suggestions=routing_disambiguation_suggestions,
            workspace_context=dict(workspace_context),
        )
