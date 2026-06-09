"""Montagem pós-preparação e pré-LLM — paridade send/stream."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
    from app.application.services.chat_web_search_synthesis_service import (
        ChatWebSearchSynthesisService,
    )
    from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


@dataclass(frozen=True)
class ChatTurnLlmAssemblyResult:
    direct_answer: str | None
    pipeline_stages: list[str]
    intelligence_metadata: dict
    admin_guidelines_prompt: str
    active_guidelines: list[dict]
    llm_messages: list
    admin_debug_payload: dict | None


class ChatTurnLlmAssemblyService:
    @classmethod
    def assemble(
        cls,
        *,
        request: SendChatMessageRequest,
        message: str,
        user_id: UUID,
        workspace_context: dict,
        attachments: list,
        previous_messages: list,
        prepared: Any,
        user_message: Any | None,
        chat_repository: ChatSessionRepositoryPort,
        prompt_builder_service: ChatPromptBuilderService,
        web_search_synthesis_service: ChatWebSearchSynthesisService,
        build_attachment_context,
        resolve_llm_user_context,
        build_admin_guidelines_prompt,
        embedding_cache_stats,
        channel: Literal["send", "stream"] = "send",
        patch_user_metadata: bool = True,
    ) -> ChatTurnLlmAssemblyResult:
        direct_answer = prepared.direct_answer
        pipeline_stages = list(prepared.pipeline_stages)
        tool_context = prepared.tool_context
        tool_calls = prepared.tool_calls
        sources = prepared.sources
        pipeline_timings = prepared.pipeline_timings
        operational_optimize = prepared.operational_optimize
        analysis_mode = prepared.analysis_mode
        fast_path = prepared.fast_path
        skip_rag = prepared.skip_rag
        history = prepared.history
        history_summary = prepared.history_summary
        rag = prepared.rag

        from app.application.services.chat_drawing_turn_enrichment_service import (
            ChatDrawingTurnEnrichmentService,
        )

        attachment_ids = getattr(request, "attachment_ids", None)
        tool_context = ChatDrawingTurnEnrichmentService.enrich_tool_context(
            tool_context,
            message=message,
            attachment_ids=attachment_ids,
        )

        report_direct = ChatDrawingTurnEnrichmentService.resolve_report_direct_answer(
            tool_context
        )

        if report_direct and not str(direct_answer or "").strip():
            direct_answer = report_direct

        if direct_answer and isinstance(tool_context, dict):
            tool_context = {**tool_context, "directAnswer": direct_answer}

        direct_answer, pipeline_stages = web_search_synthesis_service.enhance_prepared_turn(
            message=message,
            tool_context=tool_context,
            direct_answer=direct_answer,
            pipeline_stages=pipeline_stages,
        )

        intelligence_metadata = ChatIntelligenceMetadataService.build(
            sources=sources,
            tool_context=tool_context,
            embedding_cache_stats=embedding_cache_stats(),
            pipeline_timings=pipeline_timings.to_dict(),
            pipeline=ChatIntelligenceMetadataService.build_pipeline_flags(
                fast_path=fast_path,
                operational_optimize=operational_optimize,
                tool_context=tool_context,
                skip_rag=skip_rag,
                analysis_mode=analysis_mode,
                stages=pipeline_stages,
                direct_answer=direct_answer,
            ),
        )

        if patch_user_metadata and user_message is not None:
            chat_repository.patch_message_metadata(
                user_message.id,
                {
                    "rag": {
                        "sources": sources,
                    },
                    "toolCalls": tool_calls,
                    "intelligence": intelligence_metadata,
                    "delivery": {"status": "processing"},
                },
            )

        skip_admin_guidelines = operational_optimize or direct_answer

        if channel == "send":
            skip_admin_guidelines = skip_admin_guidelines or fast_path

        if skip_admin_guidelines:
            admin_guidelines_prompt, active_guidelines = "", []
        else:
            admin_guidelines_prompt, active_guidelines = build_admin_guidelines_prompt(
                workspace_context,
            )

        if direct_answer:
            llm_messages: list = []
        elif (
            channel == "send"
            and fast_path
            and Settings.CHAT_FAST_PATH_SLIM_PROMPT
            and not ChatAgentSkillsService.preserves_rag_on_fast_path(
                workspace_context.get("skills") or {}
            )
        ):
            llm_messages = prompt_builder_service.build_fast_path_messages(
                current_message=message,
                history=history[-2:] if history else [],
                skills=workspace_context.get("skills") or {},
            )
        else:
            user_context = resolve_llm_user_context(
                request.access_token,
                message,
                operational_optimize=operational_optimize,
                analysis_mode=analysis_mode,
            )
            from app.application.services.chat_email_turn_service import ChatEmailTurnService
            from app.application.services.chat_text_correction_turn_service import (
                ChatTextCorrectionTurnService,
            )

            email_supplement = ChatEmailTurnService.build_prompt_supplement(
                message=message,
                workspace_context=workspace_context,
                email_writing_mode=bool(prepared.email_writing_mode),
                email_subtype=prepared.email_subtype,
            )
            correction_supplement = ChatTextCorrectionTurnService.build_prompt_supplement(
                message=message,
                text_correction_mode=bool(prepared.text_correction_mode),
                text_correction_subtype=prepared.text_correction_subtype,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
            )

            from app.domain.services.chat_drawing_intent_service import (
                ChatDrawingIntentService,
            )

            drawing_policy_addon = ChatDrawingIntentService.build_llm_fallback_policy_addon(
                message,
                attachment_ids=attachment_ids,
            )
            merged_admin_guidelines = admin_guidelines_prompt

            if drawing_policy_addon:
                merged_admin_guidelines = (
                    f"{admin_guidelines_prompt}\n\n{drawing_policy_addon}".strip()
                    if admin_guidelines_prompt
                    else drawing_policy_addon
                )

            llm_messages = prompt_builder_service.build_messages(
                history=history,
                current_message=message,
                rag_context=rag["context"],
                tool_context=tool_context["context"],
                project_prompt=workspace_context.get("projectPrompt"),
                agent_prompt=workspace_context.get("agentPrompt"),
                admin_guidelines_prompt=merged_admin_guidelines,
                attachments=attachments,
                attachment_context=build_attachment_context(
                    user_id=user_id,
                    session_id=UUID(request.session_id),
                    request=request,
                ),
                history_summary=history_summary,
                operational_mode=operational_optimize,
                analysis_mode=analysis_mode,
                data_interpretation_mode=ChatAnalysisIntentService.is_data_interpretation_request(
                    message,
                    previous_messages,
                ),
                text_task_mode=bool(prepared.text_task_mode),
                email_writing_mode=bool(prepared.email_writing_mode),
                text_correction_mode=bool(prepared.text_correction_mode),
                email_prompt_supplement=email_supplement,
                text_correction_prompt_supplement=correction_supplement,
                text_task_attachment_context=build_attachment_context(
                    user_id=user_id,
                    session_id=UUID(request.session_id),
                    request=request,
                )
                if prepared.text_task_mode
                else None,
                user_context=user_context,
                skills=workspace_context.get("skills"),
            )

        admin_debug_payload = ChatAdminDebugService.build_for_turn(
            request,
            workspace_context=workspace_context,
            tool_context=tool_context,
            rag=rag,
            llm_messages=llm_messages,
            history_summary=history_summary,
            operational_optimize=operational_optimize,
            analysis_mode=analysis_mode,
            fast_path=fast_path,
            skip_rag=skip_rag,
            intent_route=prepared.intent_route,
        )

        from app.application.services.chat_drawing_admin_debug_service import (
            ChatDrawingAdminDebugService,
        )

        pipeline_stages = ChatDrawingAdminDebugService.extend_pipeline_stages(
            pipeline_stages,
            (admin_debug_payload or {}).get("drawingAnalysisTrace"),
        )

        return ChatTurnLlmAssemblyResult(
            direct_answer=direct_answer,
            pipeline_stages=pipeline_stages,
            intelligence_metadata=intelligence_metadata,
            admin_guidelines_prompt=admin_guidelines_prompt,
            active_guidelines=active_guidelines,
            llm_messages=llm_messages,
            admin_debug_payload=admin_debug_payload,
        )
