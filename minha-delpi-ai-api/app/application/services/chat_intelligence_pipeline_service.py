"""Pipeline base de inteligência do chat — compartilhado por stream, send, agentes e simulação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)


@dataclass(frozen=True)
class ChatPreToolDecisions:
    operational_optimize: bool
    analysis_mode: bool


@dataclass(frozen=True)
class ChatPostToolDecisions:
    tool_context: dict
    analysis_mode: bool


class ChatIntelligencePipelineService:
    """Orquestra decisões de inteligência do chat base (independente de agente/projeto)."""

    @classmethod
    def resolve_pre_tool_decisions(
        cls,
        message: str,
        allowed_action_ids: list[str] | None,
        *,
        attachment_ids: list[str] | None = None,
        previous_messages: list[Any] | None = None,
    ) -> ChatPreToolDecisions:
        operational_optimize = ChatOperationalPipelineService.should_optimize(
            message,
            allowed_action_ids,
            attachment_ids=attachment_ids,
        )
        analysis_mode = ChatAnalysisIntentService.is_comparison_or_insight_request(message)

        if (
            not analysis_mode
            and previous_messages
            and ChatAnalysisIntentService.is_data_interpretation_request(
                message,
                previous_messages,
            )
        ):
            analysis_mode = True

        if analysis_mode:
            operational_optimize = False
        elif (
            not operational_optimize
            and previous_messages
            and ChatOperationalPipelineService.is_enabled()
            and not attachment_ids
            and allowed_action_ids
        ):
            conversation_context = cls.build_conversation_context(previous_messages)

            if ChatOperationalRefinementService.is_operational_follow_up(
                message,
                conversation_context=conversation_context or None,
                previous_messages=previous_messages,
            ):
                operational_optimize = True

        return ChatPreToolDecisions(
            operational_optimize=operational_optimize,
            analysis_mode=analysis_mode,
        )

    @classmethod
    def build_conversation_context(
        cls,
        previous_messages: list[Any] | None,
        *,
        limit: int = 8,
    ) -> str:
        if not previous_messages:
            return ""

        return ChatConversationContextService.build_text_context(
            previous_messages,
            limit=limit,
        )

    @classmethod
    def finalize_after_tools(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        tool_context: dict | None,
    ) -> ChatPostToolDecisions:
        if not previous_messages:
            analysis_mode = ChatAnalysisIntentService.is_comparison_or_insight_request(message)
            return ChatPostToolDecisions(
                tool_context=dict(tool_context or {}),
                analysis_mode=analysis_mode,
            )

        analysis_mode, updated = ChatConversationContextService.apply_analysis_mode(
            message,
            previous_messages,
            dict(tool_context or {}),
        )

        return ChatPostToolDecisions(
            tool_context=updated,
            analysis_mode=analysis_mode,
        )

    @classmethod
    def resolve_analysis_direct_answer(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        *,
        current_tool_calls: list | None = None,
    ) -> str | None:
        from app.application.services.chat_structure_comparison_service import (
            ChatStructureComparisonService,
        )

        return ChatStructureComparisonService.build_comparison_answer(
            message,
            previous_messages,
            current_tool_calls=current_tool_calls,
        )

    @classmethod
    def resolve_direct_answer(
        cls,
        tool_context: dict | None,
        *,
        analysis_mode: bool,
    ) -> str | None:
        if analysis_mode:
            return None

        return ChatExternalActionDirectResponseService.resolve_answer(tool_context)

    @classmethod
    def analysis_mode_from_tool_context(cls, tool_context: dict | None) -> bool:
        if not tool_context:
            return False

        if tool_context.get("analysisMode"):
            return True

        return ChatAnalysisIntentService.is_comparison_or_insight_request(
            str(tool_context.get("currentMessage") or "")
        )
