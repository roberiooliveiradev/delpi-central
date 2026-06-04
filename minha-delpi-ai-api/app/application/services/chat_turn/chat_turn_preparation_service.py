"""Preparação determinística do turno antes do LLM.

Objetivo: centralizar as camadas pré-LLM (canvas, capabilities, tools, direct-answer, RAG)
em um único serviço, evitando duplicação entre stream/send e simulação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_meta_direct_answer_service import (
    ChatMetaDirectAnswerService,
)
from app.application.services.chat_small_talk_service import ChatSmallTalkService
from app.application.services.chat_utility_direct_answer_service import (
    ChatUtilityDirectAnswerService,
)
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_project_conversation_context_service import (
    ChatProjectConversationContextService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService
from app.infrastructure.config.settings import Settings


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
    ) -> ChatTurnPreparationResult:
        """Prepara tools, resposta direta e RAG.

        `previous_messages` é usado para apresentação/histórico. `history_source` define
        o conjunto que alimenta decisões que dependem do histórico (ex.: resend).
        """

        history_source = history_source or previous_messages or []
        previous_messages = previous_messages or []

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target="pergunta e histórico",
                    message="Entendendo o seu pedido...",
                    entry_id="think-question-history",
                    state="active",
                )
            )

        canvas_action = ChatCanvasContentService.resolve(
            message,
            history_source,
            workspace_context,
        )
        canvas_open_payload = (
            canvas_action.open_payload if canvas_action and canvas_action.open_payload else None
        )
        canvas_operational_update = ChatCanvasIntentService.is_canvas_operational_update_request(
            message
        )

        attachment_ids = getattr(request, "attachment_ids", None)
        allowed_action_ids = workspace_context.get("allowedActionIds") or []

        pre_tool = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
            message,
            allowed_action_ids,
            attachment_ids=attachment_ids,
            previous_messages=history_source,
        )
        operational_optimize = pre_tool.operational_optimize
        analysis_mode = pre_tool.analysis_mode
        text_task_category = ChatTextTaskIntentService.classify(message)
        text_task_pure = ChatTextTaskIntentService.is_pure_text_task(
            message,
            previous_messages=history_source,
        )

        if text_task_pure:
            operational_optimize = False
            analysis_mode = False

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            if analysis_mode:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="comparação ou insights",
                        message="Analisando os dados para comparar...",
                        detail="Modo análise: síntese com base em consultas e histórico.",
                    )
                )
            elif operational_optimize:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="resposta operacional direta",
                        message="Buscando a resposta mais direta...",
                        detail="Fast path operacional sem RAG completo.",
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="intenção e rota OpenAPI",
                        message="Vendo a melhor forma de te ajudar...",
                        detail="Identificando se a pergunta exige dados DELPI ou conhecimento documental.",
                        entry_id="think-openapi-route",
                        state="active",
                    )
                )

        if canvas_action or canvas_operational_update:
            operational_optimize = False
            analysis_mode = False

        if canvas_action:
            fast_path = True

        if operational_optimize:
            keep = max(1, int(history_keep))
            history_summary, history = "", list(history_source[-keep:])
        else:
            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="histórico da conversa",
                        message="Revendo o que já conversamos...",
                        entry_id="think-history-summary",
                        state="active",
                    )
                )

            history_summary, history = prepare_history(history_source)

            if on_stream_activity:
                from app.application.services.chat_stream_activity_service import (
                    ChatStreamActivityService,
                )

                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="histórico da conversa",
                        message="Tudo certo com o nosso histórico.",
                        entry_id="think-history-summary",
                        state="done",
                        level="success",
                    )
                )

        if on_stream_activity and not analysis_mode and not operational_optimize and not canvas_action:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target="intenção e rota OpenAPI",
                    message="Já sei como te ajudar.",
                    detail="Rota operacional e modo de resposta definidos.",
                    entry_id="think-openapi-route",
                    state="done",
                    level="success",
                )
            )

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target="pergunta e histórico",
                    message="Entendi o que você precisa.",
                    entry_id="think-question-history",
                    state="done",
                    level="success",
                )
            )

        pipeline_timings = ChatPipelineTimings()
        pipeline_stages: list[str] = ["ingress"]

        meta_intents = ChatMetaDirectAnswerService.detect_intents(message)
        compound_meta_question = meta_intents.count >= 2

        pre_capability_answer = None
        if not compound_meta_question:
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

        small_talk_direct = ChatSmallTalkService.build_direct_answer(
            message=message,
            workspace_context=workspace_context,
            previous_messages=history_source,
        )
        utility_direct = ChatUtilityDirectAnswerService.build_direct_answer(
            message=message,
        )

        from app.domain.services.chat_unclear_request_service import (
            ChatUnclearRequestService,
        )

        # Fallback honesto (Playbook, seções 11/28): só ativa em pedidos vagos curtos,
        # sem termos operacionais/anexo/lousa/web. Mantém o turno sem ferramentas.
        unclear_direct = None
        if not attachment_ids and not small_talk_direct and not utility_direct:
            unclear_direct = ChatUnclearRequestService.build_direct_answer(
                message=message,
                previous_messages=history_source,
            )

        from app.application.services.chat_web_search_save_sources_service import (
            ChatWebSearchSaveSourcesService,
        )

        web_save_sources_direct = ChatWebSearchSaveSourcesService.build_direct_answer(
            message=message,
            user_id=str(user_id),
            session=session,
            previous_messages=history_source,
        )

        from app.domain.services.chat_web_search_source_follow_up_service import (
            ChatWebSearchSourceFollowUpService,
        )

        web_post_search_direct = (
            ChatWebSearchSourceFollowUpService.build_post_search_follow_up_answer(
                message,
                history_source,
            )
        )

        from app.application.services.chat_attachment_welcome_service import (
            ChatAttachmentWelcomeService,
        )

        attachment_welcome_direct = None

        if ChatAttachmentWelcomeService.should_welcome(
            message,
            attachment_ids=attachment_ids,
        ):
            attachment_welcome_direct = ChatAttachmentWelcomeService.build_direct_answer(
                attachments=attachments,
            )

        from app.domain.services.chat_conversation_memory_service import (
            ChatConversationMemoryService,
        )

        previous_agent_id = str(workspace_context.get("agentId") or "") or None

        working_memory_snapshot = ChatConversationMemoryService.build_pre_turn(
            message=message,
            previous_messages=history_source,
            session_memory_service=self.session_memory_service,
            session_id=getattr(session, "id", None) if session is not None else None,
            agent_id=str(workspace_context.get("agentId") or "") or None,
            project_id=str((workspace_context.get("project") or {}).get("id") or "")
            or None,
            attachments=attachments,
            previous_agent_id=previous_agent_id,
        )

        peer_context = ChatProjectConversationContextService.build(
            project=workspace_context.get("project"),
            session_id=getattr(session, "id", None) if session is not None else None,
            user_id=user_id,
        )

        if peer_context:
            working_memory_snapshot = ChatProjectConversationContextService.merge_memory_overlay(
                working_memory_snapshot,
                peer_context.memory_overlay,
            )

        workspace_context = dict(workspace_context)

        if peer_context:
            workspace_context["projectPeerSessionIds"] = peer_context.peer_session_ids

        workspace_context["workingMemory"] = working_memory_snapshot

        from app.domain.services.chat_intent_disambiguation_service import (
            ChatIntentDisambiguationService,
        )

        routing_disambiguation = None
        routing_disambiguation_answer = None
        routing_disambiguation_suggestions: list[dict[str, str]] | None = None

        if (
            not canvas_action
            and not pre_capability_answer
            and not analysis_mode
            and not text_task_pure
        ):
            routing_disambiguation = ChatIntentDisambiguationService.try_build(
                message,
                previous_messages=history_source,
                workspace_context=workspace_context,
                allowed_action_ids=allowed_action_ids,
            )

            if routing_disambiguation:
                routing_disambiguation_answer = routing_disambiguation.get("directAnswer")
                raw_suggestions = routing_disambiguation.get("suggestions")

                if isinstance(raw_suggestions, list):
                    routing_disambiguation_suggestions = [
                        dict(item) for item in raw_suggestions if isinstance(item, dict)
                    ]

        from app.application.services.chat_session_memory_direct_answer_service import (
            ChatSessionMemoryDirectAnswerService,
        )

        session_memory_direct = ChatSessionMemoryDirectAnswerService.build(
            message=message,
            workspace_context=workspace_context,
        )

        from app.domain.services.chat_email_intent_service import ChatEmailIntentService

        email_writing_mode = bool(
            text_task_pure and ChatEmailIntentService.is_email_writing(message)
        )
        email_subtype = (
            ChatEmailIntentService.classify_subtype(message) if email_writing_mode else None
        )

        if text_task_pure:
            workspace_context["textTaskMode"] = True
            workspace_context["textTaskCategory"] = text_task_category

        if email_writing_mode:
            workspace_context["emailWritingMode"] = True
            workspace_context["emailSubtype"] = email_subtype
            if "email_writing" not in pipeline_stages:
                pipeline_stages.append("email_writing")

        if session_memory_direct and "session_memory" not in pipeline_stages:
            pipeline_stages.append("session_memory")

        from app.domain.services.chat_text_correction_intent_service import (
            ChatTextCorrectionIntentService,
        )

        text_correction_mode = bool(
            text_task_pure
            and not email_writing_mode
            and ChatTextCorrectionIntentService.is_text_correction(message)
        )
        text_correction_subtype = (
            ChatTextCorrectionIntentService.classify_subtype(message)
            if text_correction_mode
            else None
        )

        if text_correction_mode:
            workspace_context["textCorrectionMode"] = True
            workspace_context["textCorrectionSubtype"] = text_correction_subtype
            if "text_correction" not in pipeline_stages:
                pipeline_stages.append("text_correction")

        memory_prompt = ChatConversationMemoryService.format_prompt_block(
            working_memory_snapshot
        )
        base_conversation_context = (
            ChatIntelligencePipelineService.build_conversation_context(history_source)
            if history_source
            else ""
        )
        conversation_context = ChatWorkingMemoryService.merge_conversation_context(
            memory_prompt,
            base_conversation_context,
        )

        if peer_context and peer_context.conversation_text:
            conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                conversation_context,
                peer_context.conversation_text,
            )
            pipeline_stages.append("project_shared_context")

        try:
            from app.application.services.chat_user_memory_service import (
                ChatUserMemoryService,
            )

            user_memory_block = ChatUserMemoryService().format_prompt_block_for(
                user_id=str(user_id) if user_id else None,
                project_id=str((workspace_context.get("project") or {}).get("id") or "")
                or None,
            )

            if user_memory_block:
                conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                    conversation_context,
                    user_memory_block,
                )
                pipeline_stages.append("user_memory")
        except Exception:
            pass

        from app.application.services.chat_attachment_multi_compare_service import (
            ChatAttachmentMultiCompareService,
        )

        attachment_compare_hint = ChatAttachmentMultiCompareService.build_context_hint(
            message=message,
            attachments=attachments,
        )

        if attachment_compare_hint:
            conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                conversation_context,
                attachment_compare_hint,
            )
            pipeline_stages.append("attachment_compare")

        missing_product_code_answer = None
        ambiguous_period_answer = None
        interpretation_without_data_answer = None

        if not canvas_action and not pre_capability_answer and not analysis_mode and not text_task_pure:
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
            from app.domain.services.chat_sql_query_refinement_service import (
                ChatSqlQueryRefinementService,
            )

            if ChatAnalysisIntentService.is_data_reference_without_tool_data(
                message,
                history_source,
            ) and not ChatSqlQueryRefinementService.is_sql_follow_up(
                message,
                previous_messages=history_source,
            ):
                interpretation_without_data_answer = (
                    "Ainda não há dados nesta conversa para interpretar. "
                    "Faça primeiro uma consulta operacional (ex.: estoque, roteiro, estrutura ou inspeção de um produto) "
                    "e depois peça para explicar, resumir ou traduzir o resultado."
                )

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

        if skip_tools_for_attachment_document:
            operational_optimize = False
            analysis_mode = False

        if (
            canvas_action
            or pre_capability_answer
            or missing_product_code_answer
            or ambiguous_period_answer
            or routing_disambiguation_answer
            or interpretation_without_data_answer
            or skip_tools_for_user_identity
            or skip_tools_for_data_interpretation
            or skip_tools_for_attachment_document
            or small_talk_direct
            or utility_direct
            or web_save_sources_direct
            or web_post_search_direct
            or attachment_welcome_direct
            or unclear_direct
            or text_task_pure
        ) and not canvas_operational_update:
            if skip_tools_for_user_identity:
                pipeline_stages.append("identity_shortcut")
            elif skip_tools_for_data_interpretation:
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
            elif skip_tools_for_attachment_document:
                pipeline_stages.append("attachment_document")
            elif unclear_direct:
                pipeline_stages.append("unclear_request")
            elif text_task_pure:
                pipeline_stages.append("text_task")
            tool_context = {
                "context": "",
                "toolCalls": [],
                "nativeToolCalling": {},
            }
            if skip_tools_for_attachment_document:
                from app.application.services.chat_document_vision_service import (
                    ChatDocumentVisionService,
                )

                vision_meta = ChatDocumentVisionService.build_attachment_vision_metadata(
                    user_id=str(getattr(request, "user_id", "") or ""),
                    session_id=str(getattr(request, "session_id", "") or ""),
                    attachment_ids=[str(item) for item in request_attachment_ids],
                    skills=workspace_context.get("skills"),
                )

                if vision_meta:
                    tool_context["documentVision"] = vision_meta

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

        resolved_skills = workspace_context.get("skills") or {}
        assistant_identity_question = ChatAssistantIdentityService.is_assistant_identity_question(
            message
        )
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        technical_description_normas = (
            ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message)
        )
        assistant_identity_direct = None
        if (
            assistant_identity_question
            and Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED
        ):
            assistant_identity_direct = ChatAssistantIdentityService.build_direct_answer(
                message=message,
                workspace_context=workspace_context,
            )

        skip_rag = (
            (
                fast_path
                and not ChatAgentSkillsService.preserves_rag_on_fast_path(resolved_skills)
            )
            or bool(small_talk_direct)
            or bool(utility_direct)
            or bool(web_save_sources_direct)
            or bool(web_post_search_direct)
            or bool(attachment_welcome_direct)
            or bool(text_task_pure)
            or operational_optimize
            or analysis_mode
            or ChatExternalActionDirectResponseService.should_skip_rag(tool_context)
            or bool(assistant_identity_direct)
        )

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        if canvas_action:
            direct_answer = canvas_action.answer
        elif pre_capability_answer:
            direct_answer = pre_capability_answer
        elif small_talk_direct:
            direct_answer = small_talk_direct
        elif utility_direct:
            direct_answer = utility_direct
        elif web_post_search_direct:
            direct_answer = web_post_search_direct
        elif web_save_sources_direct:
            direct_answer = web_save_sources_direct
        elif (
            isinstance(tool_context, dict)
            and str(tool_context.get("directAnswer") or "").strip()
            and (
                ChatSqlQueryRefinementService.is_sql_follow_up(
                    message,
                    previous_messages=history_source,
                )
                or ChatSqlIntentService.is_sql_conversation_turn(message)
            )
        ):
            direct_answer = str(tool_context.get("directAnswer") or "").strip()
        elif session_memory_direct:
            direct_answer = session_memory_direct
        elif attachment_welcome_direct:
            direct_answer = attachment_welcome_direct
        elif interpretation_without_data_answer:
            direct_answer = interpretation_without_data_answer
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

        if canvas_action or pre_capability_answer or small_talk_direct or utility_direct or (
            web_post_search_direct
        ) or (
            web_save_sources_direct
        ) or (
            session_memory_direct
        ) or (
            attachment_welcome_direct
        ) or (
            analysis_mode and direct_answer
        ) or interpretation_without_data_answer:
            skip_rag = True

        # Casos de identidade/capacidades gerais ainda são resolvidos no use case,
        # pois dependem de token e/ou workspace_context completos.

        if not direct_answer:
            meta_direct = ChatMetaDirectAnswerService.build(
                message=message,
                workspace_context=workspace_context,
                resolve_user_identity_answer=resolve_user_identity_answer,
                resolve_capabilities_answer=resolve_capabilities_answer,
            )

            if meta_direct:
                direct_answer = meta_direct
                skip_rag = True
                pipeline_stages.append("meta_direct_answer")

        if not direct_answer:
            user_direct = resolve_user_identity_answer(message)
            if user_direct:
                direct_answer = user_direct
                skip_rag = True

        if not direct_answer:
            caps_direct = resolve_capabilities_answer(message)
            if caps_direct:
                direct_answer = caps_direct
                skip_rag = True

        if not direct_answer and assistant_identity_direct:
            direct_answer = assistant_identity_direct
            skip_rag = True

        if not direct_answer and missing_product_code_answer:
            direct_answer = missing_product_code_answer
            skip_rag = True

        if not direct_answer and ambiguous_period_answer:
            direct_answer = ambiguous_period_answer
            skip_rag = True

        if not direct_answer and routing_disambiguation_answer:
            direct_answer = routing_disambiguation_answer
            skip_rag = True

        if not direct_answer and interpretation_without_data_answer:
            direct_answer = interpretation_without_data_answer
            skip_rag = True

        if not direct_answer and unclear_direct:
            direct_answer = unclear_direct
            skip_rag = True

            if "unclear_request" not in pipeline_stages:
                pipeline_stages.append("unclear_request")

        if not direct_answer and skip_tools_for_data_interpretation:
            from app.application.services.chat_data_interpretation_answer_service import (
                ChatDataInterpretationAnswerService,
            )

            interpreted = ChatDataInterpretationAnswerService.build_answer(
                message,
                history_source,
            )

            if interpreted:
                direct_answer = interpreted
                skip_rag = True

                from app.application.services.chat_text_task_composer_service import (
                    ChatTextTaskComposerService,
                )

                draft_meta = ChatTextTaskComposerService.build_operational_email_with_metadata(
                    message=message,
                    previous_messages=history_source,
                )

                if draft_meta:
                    tool_context["operationalEmailDraft"] = draft_meta

                    if "email_operational" not in pipeline_stages:
                        pipeline_stages.append("email_operational")

        if tool_calls:
            from app.application.services.chat_tool_context_service import (
                ChatToolContextService,
            )

            if not (
                isinstance(tool_context, dict) and tool_context.get("sqlRequiresLlm")
            ):
                presentation_answer = ChatToolContextService.prefer_presentation_direct_answer(
                    direct_answer,
                    tool_calls,
                    message=message,
                )

                if presentation_answer:
                    direct_answer = presentation_answer
                    skip_rag = True

            from app.domain.services.chat_product_overview_intent_service import (
                ChatProductOverviewIntentService,
            )

            if ChatProductOverviewIntentService.should_force_llm_synthesis(
                message,
                tool_calls,
            ):
                direct_answer = None
                skip_rag = False

        if ChatTextTaskIntentService.is_mixed_text_and_operational(message):
            from app.application.services.chat_text_task_composer_service import (
                ChatTextTaskComposerService,
            )

            mixed_draft = ChatTextTaskComposerService.build_operational_email_with_metadata(
                message=message,
                tool_calls=tool_calls,
            )

            if mixed_draft:
                from app.application.services.chat_email_answer_guard_service import (
                    ChatEmailAnswerGuardService,
                )

                mixed_text, _guard = ChatEmailAnswerGuardService.apply(
                    str(mixed_draft.get("text") or ""),
                    message=message,
                    workspace_context={"emailWritingMode": True},
                )
                tool_context["operationalEmailDraft"] = mixed_draft

                if mixed_text:
                    if direct_answer:
                        direct_answer = f"{direct_answer.strip()}\n\n---\n\n{mixed_text}"
                    else:
                        direct_answer = mixed_text

                skip_rag = True

                if "text_task_mixed" not in pipeline_stages:
                    pipeline_stages.append("text_task_mixed")

                if "email_operational" not in pipeline_stages:
                    pipeline_stages.append("email_operational")

        if direct_answer:
            skip_rag = True
            if "direct_answer" not in pipeline_stages:
                pipeline_stages.append("direct_answer")

        if text_task_pure and not direct_answer:
            skip_rag = True

        if on_stream_activity and not skip_rag:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Buscando",
                    target="base de conhecimento",
                    phase="rag",
                    state="active",
                    message="Procurando nas informações de apoio...",
                    detail="Consultando a base de conhecimento autorizada.",
                    entry_id="rag-search",
                )
            )

        if skip_rag:
            rag = {"context": "", "sources": []}
            pipeline_stages.append("skip_rag")
        else:
            pipeline_stages.append("rag")
            rag_query = message
            rag_min_score = None
            if assistant_identity_question:
                rag_query = ChatAssistantIdentityService.build_rag_query(message)
                rag_min_score = Settings.RAG_IDENTITY_QUESTION_MIN_SCORE
            elif technical_description_normas:
                rag_query = ChatTechnicalDescriptionIntentService.build_rag_query(message)
            elif self.semantic_memory_service.should_use_enriched_query(workspace_context):
                rag_query = self.semantic_memory_service.resolve_rag_query(
                    message,
                    workspace_context=workspace_context,
                    default_query=rag_query,
                )

                if "semantic_memory" not in pipeline_stages:
                    pipeline_stages.append("semantic_memory")

            rag = self.rag_context_service.build_context(
                rag_query,
                filters=self.knowledge_scope_service.build_filters(
                    user_id=user_id,
                    session=session,
                    workspace_context=workspace_context,
                    attachment_ids=attachment_ids,
                ),
                min_score=rag_min_score,
                chunk_filter=(
                    ChatAssistantIdentityService.identity_chunk_filter()
                    if assistant_identity_question
                    else None
                ),
            )

        sources = rag["sources"]
        web_sources = tool_context.get("webSources") if isinstance(tool_context, dict) else None

        if isinstance(web_sources, list) and web_sources:
            sources = [*web_sources, *sources]

        if not skip_rag and self.semantic_memory_service.should_use_enriched_query(
            workspace_context
        ):
            workspace_context = self.semantic_memory_service.attach_rag_to_workspace(
                workspace_context,
                message=message,
                rag_result=rag,
            )

            from app.domain.services.chat_semantic_memory_retriever_service import (
                ChatSemanticMemoryRetrieverService,
            )

            semantic_block = ChatSemanticMemoryRetrieverService.format_prompt_block(
                workspace_context.get("workingMemory"),
            )

            if semantic_block:
                conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                    conversation_context,
                    semantic_block,
                )

        try:
            from app.application.services.chat_glossary_retrieval_service import (
                ChatGlossaryRetrievalService,
            )

            glossary_block = ChatGlossaryRetrievalService().build_context_block_for(
                message=message,
                project_id=str((workspace_context.get("project") or {}).get("id") or "")
                or None,
            )

            if glossary_block:
                existing_rag_context = rag.get("context") or ""
                rag = {
                    **rag,
                    "context": (
                        f"{existing_rag_context}\n\n{glossary_block}"
                        if existing_rag_context
                        else glossary_block
                    ),
                }
                if "glossary" not in pipeline_stages:
                    pipeline_stages.append("glossary")
        except Exception:
            pass

        rag_context_chars = len(rag.get("context") or "")
        pipeline_timings.mark("rag_done")

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            if skip_rag:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Ignorado",
                        target="base de conhecimento",
                        phase="rag",
                        state="done",
                        message="Não precisei de documentos extras desta vez.",
                        detail="Base de conhecimento não necessária neste turno.",
                        entry_id="rag-search",
                    )
                )
            elif sources:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Encontrado",
                        target=f"{len(sources)} trecho(s) relevante(s)",
                        phase="rag",
                        level="success",
                        state="done",
                        message=(
                            f"Encontrei {len(sources)} trecho(s) útil(eis) "
                            "para te responder."
                        ),
                        detail=f"Base de conhecimento: {len(sources)} trecho(s) relevante(s).",
                        entry_id="rag-search",
                    )
                )
            elif rag_context_chars > 0:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Encontrado",
                        target="contexto documental",
                        phase="rag",
                        level="success",
                        state="done",
                        message="Encontrei material de apoio relevante.",
                        detail=(
                            "Base de conhecimento: contexto aplicado "
                            f"({rag_context_chars} caracteres)."
                        ),
                        entry_id="rag-search",
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Sem trechos",
                        target="nenhum trecho adicional",
                        phase="rag",
                        level="warning",
                        state="done",
                        message="Vou responder com o que já sei sobre isso.",
                        detail=(
                            "Base de conhecimento consultada; "
                            "nenhum trecho adicional aplicável."
                        ),
                        entry_id="rag-search",
                    )
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
        )

