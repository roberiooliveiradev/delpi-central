"""Preparação determinística do turno antes do LLM.

Objetivo: centralizar as camadas pré-LLM (canvas, capabilities, tools, direct-answer, RAG)
em um único serviço, evitando duplicação entre stream/send e simulação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_fast_path_service import ChatFastPathService


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


class ChatTurnPreparationService:
    """Orquestra a preparação do turno até o ponto de chamar o LLM."""

    def __init__(
        self,
        *,
        rag_context_service,
        knowledge_scope_service: ChatKnowledgeScopeService | None = None,
    ):
        self.rag_context_service = rag_context_service
        self.knowledge_scope_service = knowledge_scope_service or ChatKnowledgeScopeService()

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
        resolve_assistant_identity_answer,
        resolve_capabilities_answer,
        max_external_action_calls: int | None = None,
    ) -> ChatTurnPreparationResult:
        """Prepara tools, resposta direta e RAG.

        `previous_messages` é usado para apresentação/histórico. `history_source` define
        o conjunto que alimenta decisões que dependem do histórico (ex.: resend).
        """

        history_source = history_source or previous_messages or []
        previous_messages = previous_messages or []

        canvas_action = ChatCanvasContentService.resolve(
            message,
            history_source,
            workspace_context,
        )
        canvas_open_payload = (
            canvas_action.open_payload if canvas_action and canvas_action.open_payload else None
        )

        attachment_ids = getattr(request, "attachment_ids", None)
        allowed_action_ids = workspace_context.get("allowedActionIds") or []

        pre_tool = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
            message,
            allowed_action_ids,
            attachment_ids=attachment_ids,
        )
        operational_optimize = pre_tool.operational_optimize
        analysis_mode = pre_tool.analysis_mode

        if canvas_action:
            operational_optimize = False
            analysis_mode = False

        if operational_optimize:
            keep = max(1, int(history_keep))
            history_summary, history = "", list(history_source[-keep:])
        else:
            history_summary, history = prepare_history(history_source)

        pipeline_timings = ChatPipelineTimings()

        pre_capability_answer = ChatCapabilitiesService.resolve_capability_answer(
            message=message,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
            action_catalog=ChatCapabilitiesService.load_action_catalog_for_agent(
                allowed_action_ids,
            ),
        )

        fast_path = ChatFastPathService.should_use(
            message,
            enabled=fast_path_enabled,
            max_chars=fast_path_max_chars,
            attachment_ids=attachment_ids,
        )

        if canvas_action:
            fast_path = True

        if canvas_action or pre_capability_answer:
            tool_context = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            }
            tool_calls = []
            post_tool = ChatIntelligencePipelineService.finalize_after_tools(
                message,
                history_source,
                tool_context,
            )
            tool_context = post_tool.tool_context
            analysis_mode = post_tool.analysis_mode
            pipeline_timings.mark("tools_done")
        else:
            tool_context = build_tool_context(
                request,
                allowed_action_ids=workspace_context.get("allowedActionIds"),
                capabilities=workspace_context.get("capabilities") or {},
                specialization=workspace_context.get("specialization"),
                fast_path=fast_path,
                previous_messages=history_source,
                max_external_action_calls=max_external_action_calls,
            )
            tool_context = maybe_extend_tool_context(
                request=request,
                workspace_context=workspace_context,
                tool_context=tool_context,
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

        resolved_skills = workspace_context.get("skills") or {}

        skip_rag = (
            (
                fast_path
                and not ChatAgentSkillsService.preserves_rag_on_fast_path(resolved_skills)
            )
            or operational_optimize
            or ChatExternalActionDirectResponseService.should_skip_rag(tool_context)
        )

        if canvas_action:
            direct_answer = canvas_action.answer
        elif pre_capability_answer:
            direct_answer = pre_capability_answer
        elif analysis_mode:
            direct_answer = ChatIntelligencePipelineService.resolve_analysis_direct_answer(
                message,
                history_source,
                current_tool_calls=tool_calls,
            )
            if not direct_answer:
                direct_answer = ChatIntelligencePipelineService.resolve_direct_answer(
                    tool_context,
                    analysis_mode=analysis_mode,
                )
        else:
            direct_answer = ChatIntelligencePipelineService.resolve_direct_answer(
                tool_context,
                analysis_mode=analysis_mode,
            )

        if canvas_action or pre_capability_answer or (analysis_mode and direct_answer):
            skip_rag = True

        # Casos de identidade/capacidades gerais ainda são resolvidos no use case,
        # pois dependem de token e/ou workspace_context completos.

        if not direct_answer:
            user_direct = resolve_user_identity_answer(message)
            if user_direct:
                direct_answer = user_direct
                skip_rag = True

        if not direct_answer:
            assistant_direct = resolve_assistant_identity_answer(message)
            if assistant_direct:
                direct_answer = assistant_direct
                skip_rag = True

        if not direct_answer:
            caps_direct = resolve_capabilities_answer(message)
            if caps_direct:
                direct_answer = caps_direct
                skip_rag = True

        if skip_rag:
            rag = {"context": "", "sources": []}
        else:
            rag = self.rag_context_service.build_context(
                message,
                filters=self.knowledge_scope_service.build_filters(
                    user_id=user_id,
                    session=session,
                    workspace_context=workspace_context,
                    attachment_ids=attachment_ids,
                ),
            )
        sources = rag["sources"]
        pipeline_timings.mark("rag_done")

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
        )

