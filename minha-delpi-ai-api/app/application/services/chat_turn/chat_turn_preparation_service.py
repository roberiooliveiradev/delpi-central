"""Preparação determinística do turno antes do LLM.

Objetivo: centralizar as camadas pré-LLM (canvas, capabilities, tools, direct-answer, RAG)
em um único serviço, evitando duplicação entre stream/send e simulação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_turn.chat_turn_preparation_pre_tool_context_service import (
    ChatTurnPreparationPreToolContextService,
)
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)
from app.application.services.chat_turn.chat_turn_preparation_post_tool_resolution_service import (
    ChatTurnPreparationPostToolResolutionService,
)
from app.application.services.chat_turn.chat_turn_preparation_rag_service import (
    ChatTurnPreparationRagService,
)
from app.application.services.chat_turn.chat_turn_preparation_rag_web_fallback_service import (
    ChatTurnPreparationRagWebFallbackService,
)
from app.application.services.chat_turn.chat_turn_preparation_result_service import (
    ChatTurnPreparationResultService,
)
from app.application.services.chat_turn.chat_turn_preparation_ingress_service import (
    ChatTurnPreparationIngressService,
)
@dataclass(frozen=True)
class ChatTurnPreparationResult:
    # Flags
    operational_optimize: bool
    analysis_mode: bool
    fast_path: bool
    skip_rag: bool

    # Contexto de conversa usado para o LLM
    history: list[Any]
    history_summary: str

    # Tooling
    tool_context: dict
    tool_calls: list

    # Resposta direta (sem LLM)
    direct_answer: str | None

    # RAG
    rag: dict
    sources: list[dict]

    # Canvas (se solicitado)
    canvas_open_payload: Any | None

    # Métricas / debug
    pipeline_timings: ChatPipelineTimings
    pipeline_stages: list[str]
    text_task_mode: bool = False
    text_task_category: str | None = None
    email_writing_mode: bool = False
    email_subtype: str | None = None
    text_correction_mode: bool = False
    text_correction_subtype: str | None = None
    intent_route: dict | None = None
    routing_disambiguation_suggestions: list[dict[str, str]] | None = None


class ChatTurnPreparationService:
    """Orquestra a preparação do turno até o ponto de chamar o LLM."""

    def __init__(
        self,
        *,
        rag_context_service,
        knowledge_scope_service: ChatKnowledgeScopeService | None = None,
        session_memory_service=None,
        semantic_memory_service=None,
    ):
        self.rag_context_service = rag_context_service
        self.knowledge_scope_service = knowledge_scope_service or ChatKnowledgeScopeService()
        self.session_memory_service = session_memory_service

        if semantic_memory_service is None:
            from app.application.services.chat_semantic_memory_service import (
                ChatSemanticMemoryService,
            )

            semantic_memory_service = ChatSemanticMemoryService(rag_context_service)

        self.semantic_memory_service = semantic_memory_service

    def prepare(
        self,
        *,
        message: str,
        request,
        session,
        user_id,
        workspace_context: dict,
        attachments: list[dict],
        previous_messages: list[Any] | None,
        history_source: list[Any] | None,
        build_tool_context,
        maybe_extend_tool_context,
        prepare_history,
        history_keep: int,
        fast_path_enabled: bool,
        fast_path_max_chars: int,
        resolve_user_identity_answer,
        resolve_capabilities_answer,
        max_external_action_calls: int | None = None,
        on_stream_activity=None,
        run_post_rag_web_fallback=None,
    ) -> ChatTurnPreparationResult:
        """Prepara tools, resposta direta e RAG.

        `previous_messages` é usado para apresentação/histórico. `history_source` define
        o conjunto que alimenta decisões que dependem do histórico (ex.: resend).
        """

        history_source = history_source or previous_messages or []
        previous_messages = previous_messages or []

        ingress = ChatTurnPreparationIngressService.prepare(
            message=message,
            request=request,
            workspace_context=workspace_context,
            history_source=history_source,
            prepare_history=prepare_history,
            history_keep=history_keep,
            on_stream_activity=on_stream_activity,
        )
        canvas_action = ingress.canvas_action
        canvas_open_payload = ingress.canvas_open_payload
        canvas_operational_update = ingress.canvas_operational_update
        attachment_ids = ingress.attachment_ids
        allowed_action_ids = ingress.allowed_action_ids
        operational_optimize = ingress.operational_optimize
        analysis_mode = ingress.analysis_mode
        text_task_category = ingress.text_task_category
        text_task_pure = ingress.text_task_pure
        history = ingress.history
        history_summary = ingress.history_summary
        pipeline_timings = ingress.pipeline_timings
        pipeline_stages = list(ingress.pipeline_stages)
        fast_path = ingress.fast_path

        pre_tool = ChatTurnPreparationPreToolContextService.build(
            message=message,
            workspace_context=workspace_context,
            history_source=history_source,
            attachments=attachments,
            attachment_ids=attachment_ids,
            session=session,
            user_id=user_id,
            allowed_action_ids=allowed_action_ids,
            canvas_action=canvas_action,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            fast_path_enabled=fast_path_enabled,
            fast_path_max_chars=fast_path_max_chars,
            ingress_fast_path=fast_path,
            session_memory_service=self.session_memory_service,
        )

        workspace_context = pre_tool.workspace_context
        working_memory_snapshot = pre_tool.working_memory_snapshot
        conversation_context = pre_tool.conversation_context
        canvas_action = pre_tool.canvas_action
        fast_path = pre_tool.fast_path
        pre_capability_answer = pre_tool.pre_capability_answer
        small_talk_direct = pre_tool.small_talk_direct
        utility_direct = pre_tool.utility_direct
        unclear_direct = pre_tool.unclear_direct
        web_save_sources_direct = pre_tool.web_save_sources_direct
        web_post_search_direct = pre_tool.web_post_search_direct
        attachment_welcome_direct = pre_tool.attachment_welcome_direct
        routing_disambiguation = pre_tool.routing_disambiguation
        routing_disambiguation_answer = pre_tool.routing_disambiguation_answer
        routing_disambiguation_suggestions = pre_tool.routing_disambiguation_suggestions
        session_memory_direct = pre_tool.session_memory_direct
        email_writing_mode = pre_tool.email_writing_mode
        email_subtype = pre_tool.email_subtype
        text_correction_mode = pre_tool.text_correction_mode
        text_correction_subtype = pre_tool.text_correction_subtype
        interpretation_without_data_answer = pre_tool.interpretation_without_data_answer

        for stage in pre_tool.pipeline_stage_additions:
            if stage not in pipeline_stages:
                pipeline_stages.append(stage)

        operational_guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
            message=message,
            history_source=history_source,
            conversation_context=conversation_context,
            working_memory_snapshot=working_memory_snapshot,
            workspace_context=workspace_context,
            canvas_action=canvas_action,
            pre_capability_answer=pre_capability_answer,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
        )
        missing_product_code_answer = operational_guards.missing_product_code_answer
        ambiguous_period_answer = operational_guards.ambiguous_period_answer
        common_chat_operational_answer = operational_guards.common_chat_operational_answer

        skip_tool_flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
            message=message,
            request=request,
            history_source=history_source,
            workspace_context=workspace_context,
        )
        skip_tools_for_data_interpretation = (
            skip_tool_flags.skip_tools_for_data_interpretation
        )

        tool_phase = ChatTurnPreparationToolRoutingService.run_tool_phase(
            message=message,
            request=request,
            history_source=history_source,
            workspace_context=workspace_context,
            conversation_context=conversation_context,
            pipeline_stages=pipeline_stages,
            pipeline_timings=pipeline_timings,
            canvas_action=canvas_action,
            canvas_operational_update=canvas_operational_update,
            pre_capability_answer=pre_capability_answer,
            operational_guards=operational_guards,
            routing_disambiguation_answer=routing_disambiguation_answer,
            interpretation_without_data_answer=interpretation_without_data_answer,
            skip_flags=skip_tool_flags,
            small_talk_direct=small_talk_direct,
            utility_direct=utility_direct,
            web_save_sources_direct=web_save_sources_direct,
            web_post_search_direct=web_post_search_direct,
            attachment_welcome_direct=attachment_welcome_direct,
            unclear_direct=unclear_direct,
            text_task_pure=text_task_pure,
            fast_path=fast_path,
            operational_optimize=operational_optimize,
            analysis_mode=analysis_mode,
            build_tool_context=build_tool_context,
            maybe_extend_tool_context=maybe_extend_tool_context,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
        )

        tool_context = tool_phase.tool_context
        tool_calls = tool_phase.tool_calls
        analysis_mode = tool_phase.analysis_mode
        operational_optimize = tool_phase.operational_optimize

        if canvas_operational_update and not canvas_action:
            canvas_action = ChatCanvasContentService.build_update_from_tools(
                message,
                tool_calls,
                history_source,
                workspace_context,
            )

            if canvas_action and canvas_action.open_payload:
                canvas_open_payload = canvas_action.open_payload
                fast_path = True

                if "canvas" not in pipeline_stages:
                    pipeline_stages.append("canvas")

        if isinstance(tool_context, dict) and tool_context.get("drawingAnalysisMode"):
            if "drawing_analysis" not in pipeline_stages:
                pipeline_stages.append("drawing_analysis")

        pipeline_stages.append("post_tool")

        post_tool = ChatTurnPreparationPostToolResolutionService.resolve(
            message=message,
            workspace_context=workspace_context,
            history_source=history_source,
            pipeline_stages=pipeline_stages,
            tool_context=tool_context,
            tool_calls=tool_calls,
            fast_path=fast_path,
            analysis_mode=analysis_mode,
            operational_optimize=operational_optimize,
            text_task_pure=text_task_pure,
            canvas_action=canvas_action,
            pre_capability_answer=pre_capability_answer,
            small_talk_direct=small_talk_direct,
            utility_direct=utility_direct,
            web_post_search_direct=web_post_search_direct,
            web_save_sources_direct=web_save_sources_direct,
            attachment_welcome_direct=attachment_welcome_direct,
            session_memory_direct=session_memory_direct,
            interpretation_without_data_answer=interpretation_without_data_answer,
            unclear_direct=unclear_direct,
            missing_product_code_answer=missing_product_code_answer,
            ambiguous_period_answer=ambiguous_period_answer,
            common_chat_operational_answer=common_chat_operational_answer,
            routing_disambiguation_answer=routing_disambiguation_answer,
            skip_tools_for_data_interpretation=skip_tools_for_data_interpretation,
            resolve_user_identity_answer=resolve_user_identity_answer,
            resolve_capabilities_answer=resolve_capabilities_answer,
        )
        direct_answer = post_tool.direct_answer
        skip_rag = post_tool.skip_rag
        tool_context = post_tool.tool_context

        rag_phase = ChatTurnPreparationRagService.build(
            message=message,
            skip_rag=skip_rag,
            workspace_context=workspace_context,
            conversation_context=conversation_context,
            tool_context=tool_context,
            pipeline_stages=pipeline_stages,
            pipeline_timings=pipeline_timings,
            user_id=user_id,
            session=session,
            attachment_ids=attachment_ids,
            rag_context_service=self.rag_context_service,
            knowledge_scope_service=self.knowledge_scope_service,
            semantic_memory_service=self.semantic_memory_service,
            on_stream_activity=on_stream_activity,
        )
        rag = rag_phase.rag
        sources = rag_phase.sources
        workspace_context = rag_phase.workspace_context
        conversation_context = rag_phase.conversation_context

        rag_web_fallback = ChatTurnPreparationRagWebFallbackService.apply(
            message=message,
            skip_rag=skip_rag,
            direct_answer=direct_answer,
            rag=rag,
            tool_calls=tool_calls,
            tool_context=tool_context,
            sources=sources,
            text_task_pure=text_task_pure,
            pipeline_stages=pipeline_stages,
            run_web_search_fallback=run_post_rag_web_fallback,
        )

        if rag_web_fallback.applied:
            direct_answer = rag_web_fallback.direct_answer
            tool_context = rag_web_fallback.tool_context or tool_context
            tool_calls = rag_web_fallback.tool_calls or tool_calls
            sources = rag_web_fallback.sources or sources

        return ChatTurnPreparationResultService.finalize(
            message=message,
            pipeline_stages=pipeline_stages,
            history_source=history_source,
            workspace_context=workspace_context,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
            text_task_category=text_task_category,
            skip_rag=skip_rag,
            direct_answer=direct_answer,
            tool_calls=tool_calls,
            request_attachment_ids=skip_tool_flags.request_attachment_ids,
            allowed_action_ids=allowed_action_ids,
            operational_optimize=operational_optimize,
            fast_path=fast_path,
            history=history,
            history_summary=history_summary,
            tool_context=tool_context,
            rag=rag,
            sources=sources,
            canvas_open_payload=canvas_open_payload,
            pipeline_timings=pipeline_timings,
            email_writing_mode=email_writing_mode,
            email_subtype=email_subtype,
            text_correction_mode=text_correction_mode,
            text_correction_subtype=text_correction_subtype,
            routing_disambiguation_suggestions=routing_disambiguation_suggestions,
        )

