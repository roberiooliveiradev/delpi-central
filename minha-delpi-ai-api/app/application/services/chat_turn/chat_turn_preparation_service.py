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
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_turn.chat_turn_preparation_direct_answer_service import (
    ChatTurnPreparationDirectAnswerService,
)
from app.application.services.chat_turn.chat_turn_preparation_memory_context_service import (
    ChatTurnPreparationMemoryContextService,
)
from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)
from app.application.services.chat_turn.chat_turn_preparation_post_tool_resolution_service import (
    ChatTurnPreparationPostToolResolutionService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
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

        direct_answer_bundle = ChatTurnPreparationDirectAnswerService.build_early_bundle(
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
        )

        fast_path = direct_answer_bundle.fast_path
        pre_capability_answer = direct_answer_bundle.pre_capability_answer
        small_talk_direct = direct_answer_bundle.small_talk_direct
        utility_direct = direct_answer_bundle.utility_direct
        unclear_direct = direct_answer_bundle.unclear_direct
        web_save_sources_direct = direct_answer_bundle.web_save_sources_direct
        web_post_search_direct = direct_answer_bundle.web_post_search_direct
        attachment_welcome_direct = direct_answer_bundle.attachment_welcome_direct
        routing_disambiguation = direct_answer_bundle.routing_disambiguation
        routing_disambiguation_answer = direct_answer_bundle.routing_disambiguation_answer
        routing_disambiguation_suggestions = (
            direct_answer_bundle.routing_disambiguation_suggestions
        )
        session_memory_direct = direct_answer_bundle.session_memory_direct
        email_writing_mode = direct_answer_bundle.email_writing_mode
        email_subtype = direct_answer_bundle.email_subtype
        text_correction_mode = direct_answer_bundle.text_correction_mode
        text_correction_subtype = direct_answer_bundle.text_correction_subtype

        for stage in direct_answer_bundle.pipeline_stage_additions:
            if stage not in pipeline_stages:
                pipeline_stages.append(stage)

        workspace_context.update(direct_answer_bundle.workspace_context_patches)

        memory_context = ChatTurnPreparationMemoryContextService.build(
            message=message,
            workspace_context=workspace_context,
            history_source=history_source,
            attachments=attachments,
            session=session,
            user_id=user_id,
            session_memory_service=self.session_memory_service,
        )

        workspace_context = memory_context.workspace_context
        working_memory_snapshot = memory_context.working_memory_snapshot
        conversation_context = memory_context.conversation_context

        for stage in memory_context.pipeline_stage_additions:
            if stage not in pipeline_stages:
                pipeline_stages.append(stage)

        interpretation_without_data_answer = (
            ChatTurnPreparationDirectAnswerService.resolve_interpretation_without_data(
                message=message,
                history_source=history_source,
                canvas_action=canvas_action,
                pre_capability_answer=pre_capability_answer,
                analysis_mode=analysis_mode,
                text_task_pure=text_task_pure,
            )
        )

        operational_guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
            message=message,
            history_source=history_source,
            conversation_context=conversation_context,
            working_memory_snapshot=working_memory_snapshot,
            canvas_action=canvas_action,
            pre_capability_answer=pre_capability_answer,
            analysis_mode=analysis_mode,
            text_task_pure=text_task_pure,
        )
        missing_product_code_answer = operational_guards.missing_product_code_answer
        ambiguous_period_answer = operational_guards.ambiguous_period_answer

        skip_tool_flags = ChatTurnPreparationToolRoutingService.resolve_skip_tool_flags(
            message=message,
            request=request,
            history_source=history_source,
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
            routing_disambiguation_answer=routing_disambiguation_answer,
            skip_tools_for_data_interpretation=skip_tools_for_data_interpretation,
            resolve_user_identity_answer=resolve_user_identity_answer,
            resolve_capabilities_answer=resolve_capabilities_answer,
        )
        direct_answer = post_tool.direct_answer
        skip_rag = post_tool.skip_rag
        tool_context = post_tool.tool_context

        assistant_identity_question = ChatAssistantIdentityService.is_assistant_identity_question(
            message
        )
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        technical_description_normas = (
            ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message)
        )

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
            attachment_ids=skip_tool_flags.request_attachment_ids or None,
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

