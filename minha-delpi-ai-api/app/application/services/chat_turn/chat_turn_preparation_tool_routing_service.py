"""Decisão de skip-tools e execução da fase de ferramentas — Fase 3C lote 17."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)


@dataclass(frozen=True)
class ChatTurnPreparationSkipToolFlags:
    skip_tools_for_user_identity: bool
    skip_tools_for_data_interpretation: bool
    skip_tools_for_attachment_document: bool
    request_attachment_ids: list[str]


@dataclass(frozen=True)
class ChatTurnPreparationOperationalGuards:
    missing_product_code_answer: str | None
    ambiguous_period_answer: str | None


@dataclass(frozen=True)
class ChatTurnPreparationToolPhaseResult:
    tool_context: dict
    tool_calls: list
    analysis_mode: bool
    operational_optimize: bool


class ChatTurnPreparationToolRoutingService:
    @classmethod
    def resolve_operational_guards(
        cls,
        *,
        message: str,
        history_source: list,
        conversation_context: str,
        working_memory_snapshot: dict,
        canvas_action,
        pre_capability_answer: str | None,
        analysis_mode: bool,
        text_task_pure: bool,
    ) -> ChatTurnPreparationOperationalGuards:
        if canvas_action or pre_capability_answer or analysis_mode or text_task_pure:
            return ChatTurnPreparationOperationalGuards(
                missing_product_code_answer=None,
                ambiguous_period_answer=None,
            )

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        skip_missing_product_prompt = (
            ChatSqlOperationalIntentService.requires_sql_knowledge(message)
            and not ChatProductQueryIntentService.extract_product_code(message)
        )

        if skip_missing_product_prompt:
            missing_product_code_answer = None
        else:
            missing_product_code_answer = (
                ChatOperationalParameterService.resolve_missing_product_code_answer(
                    message,
                    conversation_context=conversation_context,
                    previous_messages=history_source,
                    memory_snapshot=working_memory_snapshot,
                )
            )

        ambiguous_period_answer = (
            ChatOperationalParameterService.resolve_ambiguous_period_answer(
                message,
                previous_messages=history_source,
            )
        )

        return ChatTurnPreparationOperationalGuards(
            missing_product_code_answer=missing_product_code_answer,
            ambiguous_period_answer=ambiguous_period_answer,
        )

    @classmethod
    def resolve_skip_tool_flags(
        cls,
        *,
        message: str,
        request,
        history_source: list,
    ) -> ChatTurnPreparationSkipToolFlags:
        skip_tools_for_user_identity = bool(
            getattr(request, "access_token", None)
            and ChatUserContextService.is_user_identity_question(message)
        )
        skip_tools_for_data_interpretation = (
            ChatAnalysisIntentService.is_data_interpretation_request(
                message,
                history_source,
            )
            and ChatConversationContextService.has_recent_tool_data(history_source)
        )

        request_attachment_ids = list(getattr(request, "attachment_ids", None) or [])
        from app.domain.services.chat_attachment_document_intent_service import (
            ChatAttachmentDocumentIntentService,
        )
        from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

        skip_tools_for_attachment_document = bool(
            request_attachment_ids
            and ChatAttachmentDocumentIntentService.is_document_content_question(message)
            and not ChatDrawingIntentService.is_drawing_analysis_request(
                message,
                attachment_ids=request_attachment_ids,
            )
        )

        return ChatTurnPreparationSkipToolFlags(
            skip_tools_for_user_identity=skip_tools_for_user_identity,
            skip_tools_for_data_interpretation=skip_tools_for_data_interpretation,
            skip_tools_for_attachment_document=skip_tools_for_attachment_document,
            request_attachment_ids=request_attachment_ids,
        )

    @classmethod
    def should_skip_tools(
        cls,
        *,
        canvas_action,
        canvas_operational_update: bool,
        pre_capability_answer: str | None,
        missing_product_code_answer: str | None,
        ambiguous_period_answer: str | None,
        routing_disambiguation_answer: str | None,
        interpretation_without_data_answer: str | None,
        skip_flags: ChatTurnPreparationSkipToolFlags,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
    ) -> bool:
        return bool(
            (
                canvas_action
                or pre_capability_answer
                or missing_product_code_answer
                or ambiguous_period_answer
                or routing_disambiguation_answer
                or interpretation_without_data_answer
                or skip_flags.skip_tools_for_user_identity
                or skip_flags.skip_tools_for_data_interpretation
                or skip_flags.skip_tools_for_attachment_document
                or small_talk_direct
                or utility_direct
                or web_save_sources_direct
                or web_post_search_direct
                or attachment_welcome_direct
                or unclear_direct
                or text_task_pure
            )
            and not canvas_operational_update
        )

    @classmethod
    def _append_skip_tool_stage(
        cls,
        *,
        message: str,
        pipeline_stages: list[str],
        skip_flags: ChatTurnPreparationSkipToolFlags,
        canvas_action,
        pre_capability_answer: str | None,
        missing_product_code_answer: str | None,
        ambiguous_period_answer: str | None,
        routing_disambiguation_answer: str | None,
        interpretation_without_data_answer: str | None,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
    ) -> None:
        if skip_flags.skip_tools_for_user_identity:
            pipeline_stages.append("identity_shortcut")
        elif skip_flags.skip_tools_for_data_interpretation:
            pipeline_stages.append("data_interpretation")
        elif canvas_action:
            pipeline_stages.append("canvas")
        elif pre_capability_answer:
            from app.application.services.chat_onboarding_service import (
                ChatOnboardingService,
            )

            if ChatOnboardingService.is_training_request(message):
                pipeline_stages.append("onboarding_training")
            else:
                pipeline_stages.append("capabilities")
        elif missing_product_code_answer:
            pipeline_stages.append("operational_parameter")
        elif ambiguous_period_answer:
            pipeline_stages.append("operational_parameter")
        elif routing_disambiguation_answer:
            pipeline_stages.append("intent_disambiguation")
        elif interpretation_without_data_answer:
            pipeline_stages.append("data_interpretation_empty")
        elif small_talk_direct:
            pipeline_stages.append("small_talk")
        elif utility_direct:
            pipeline_stages.append("utility_direct")
        elif web_save_sources_direct:
            pipeline_stages.append("web_save_sources")
        elif web_post_search_direct:
            pipeline_stages.append("web_post_search_follow_up")
        elif attachment_welcome_direct:
            pipeline_stages.append("attachment_welcome")
        elif skip_flags.skip_tools_for_attachment_document:
            pipeline_stages.append("attachment_document")
        elif unclear_direct:
            pipeline_stages.append("unclear_request")
        elif text_task_pure:
            pipeline_stages.append("text_task")

    @classmethod
    def run_tool_phase(
        cls,
        *,
        message: str,
        request,
        history_source: list,
        workspace_context: dict,
        conversation_context: str,
        pipeline_stages: list[str],
        pipeline_timings: ChatPipelineTimings,
        canvas_action,
        canvas_operational_update: bool,
        pre_capability_answer: str | None,
        operational_guards: ChatTurnPreparationOperationalGuards,
        routing_disambiguation_answer: str | None,
        interpretation_without_data_answer: str | None,
        skip_flags: ChatTurnPreparationSkipToolFlags,
        small_talk_direct: str | None,
        utility_direct: str | None,
        web_save_sources_direct: str | None,
        web_post_search_direct: str | None,
        attachment_welcome_direct: str | None,
        unclear_direct: str | None,
        text_task_pure: bool,
        fast_path: bool,
        operational_optimize: bool,
        analysis_mode: bool,
        build_tool_context: Callable[..., dict],
        maybe_extend_tool_context: Callable[..., dict],
        max_external_action_calls: int | None,
        on_stream_activity=None,
    ) -> ChatTurnPreparationToolPhaseResult:
        if skip_flags.skip_tools_for_attachment_document:
            operational_optimize = False
            analysis_mode = False

        if cls.should_skip_tools(
            canvas_action=canvas_action,
            canvas_operational_update=canvas_operational_update,
            pre_capability_answer=pre_capability_answer,
            missing_product_code_answer=operational_guards.missing_product_code_answer,
            ambiguous_period_answer=operational_guards.ambiguous_period_answer,
            routing_disambiguation_answer=routing_disambiguation_answer,
            interpretation_without_data_answer=interpretation_without_data_answer,
            skip_flags=skip_flags,
            small_talk_direct=small_talk_direct,
            utility_direct=utility_direct,
            web_save_sources_direct=web_save_sources_direct,
            web_post_search_direct=web_post_search_direct,
            attachment_welcome_direct=attachment_welcome_direct,
            unclear_direct=unclear_direct,
            text_task_pure=text_task_pure,
        ):
            cls._append_skip_tool_stage(
                message=message,
                pipeline_stages=pipeline_stages,
                skip_flags=skip_flags,
                canvas_action=canvas_action,
                pre_capability_answer=pre_capability_answer,
                missing_product_code_answer=operational_guards.missing_product_code_answer,
                ambiguous_period_answer=operational_guards.ambiguous_period_answer,
                routing_disambiguation_answer=routing_disambiguation_answer,
                interpretation_without_data_answer=interpretation_without_data_answer,
                small_talk_direct=small_talk_direct,
                utility_direct=utility_direct,
                web_save_sources_direct=web_save_sources_direct,
                web_post_search_direct=web_post_search_direct,
                attachment_welcome_direct=attachment_welcome_direct,
                unclear_direct=unclear_direct,
                text_task_pure=text_task_pure,
            )
            tool_context: dict[str, Any] = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            }

            if skip_flags.skip_tools_for_attachment_document:
                from app.application.services.chat_document_vision_service import (
                    ChatDocumentVisionService,
                )

                vision_meta = ChatDocumentVisionService.build_attachment_vision_metadata(
                    user_id=str(getattr(request, "user_id", "") or ""),
                    session_id=str(getattr(request, "session_id", "") or ""),
                    attachment_ids=[
                        str(item) for item in skip_flags.request_attachment_ids
                    ],
                    skills=workspace_context.get("skills"),
                )

                if vision_meta:
                    tool_context["documentVision"] = vision_meta

            tool_calls: list = []
            post_tool = ChatIntelligencePipelineService.finalize_after_tools(
                message,
                history_source,
                tool_context,
            )
            tool_context = post_tool.tool_context
            analysis_mode = post_tool.analysis_mode
            pipeline_timings.mark("tools_done")
        else:
            pipeline_stages.append("tools")
            tool_context = build_tool_context(
                request,
                allowed_action_ids=workspace_context.get("allowedActionIds"),
                capabilities=workspace_context.get("capabilities") or {},
                specialization=workspace_context.get("specialization"),
                fast_path=fast_path and not operational_optimize,
                previous_messages=history_source,
                max_external_action_calls=max_external_action_calls,
                on_stream_activity=on_stream_activity,
                working_memory=workspace_context.get("workingMemory"),
            )
            tool_context = maybe_extend_tool_context(
                request=request,
                workspace_context=workspace_context,
                tool_context=tool_context,
                conversation_context=conversation_context,
                previous_messages=history_source,
                on_stream_activity=on_stream_activity,
            )
            post_tool = ChatIntelligencePipelineService.finalize_after_tools(
                message,
                history_source,
                tool_context,
            )
            tool_context = post_tool.tool_context
            analysis_mode = post_tool.analysis_mode
            tool_calls = tool_context["toolCalls"]
            pipeline_timings.mark("tools_done")

        return ChatTurnPreparationToolPhaseResult(
            tool_context=tool_context,
            tool_calls=tool_calls,
            analysis_mode=analysis_mode,
            operational_optimize=operational_optimize,
        )
