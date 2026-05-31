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
    intent_route: dict | None = None


class ChatTurnPreparationService:
    """Orquestra a preparação do turno até o ponto de chamar o LLM."""

    def __init__(
        self,
        *,
        rag_context_service,
        knowledge_scope_service: ChatKnowledgeScopeService | None = None,
        session_memory_service=None,
    ):
        self.rag_context_service = rag_context_service
        self.knowledge_scope_service = knowledge_scope_service or ChatKnowledgeScopeService()
        self.session_memory_service = session_memory_service

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
                    message="Pensando sobre a pergunta e o histórico...",
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
                        detail="Modo análise: síntese com base em consultas e histórico.",
                    )
                )
            elif operational_optimize:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="resposta operacional direta",
                        detail="Fast path operacional sem RAG completo.",
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.think(
                        target="intenção e rota OpenAPI",
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
                        message="Resumindo histórico longo, se necessário...",
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
                        message="Histórico pronto para o turno.",
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
                    message="Contexto da pergunta analisado.",
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

        from app.application.services.chat_web_search_save_sources_service import (
            ChatWebSearchSaveSourcesService,
        )

        web_save_sources_direct = ChatWebSearchSaveSourcesService.build_direct_answer(
            message=message,
            user_id=str(user_id),
            session=session,
            previous_messages=history_source,
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

        working_memory_snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
            message=message,
            previous_messages=history_source,
        )

        if self.session_memory_service and session is not None:
            working_memory_snapshot = self.session_memory_service.apply_to_pre_turn(
                session_id=getattr(session, "id", None),
                snapshot=working_memory_snapshot,
                message=message,
            )

        workspace_context = dict(workspace_context)
        workspace_context["workingMemory"] = working_memory_snapshot

        if text_task_pure:
            workspace_context["textTaskMode"] = True
            workspace_context["textTaskCategory"] = text_task_category

        memory_prompt = ChatWorkingMemoryService.format_prompt_block(working_memory_snapshot)
        base_conversation_context = (
            ChatIntelligencePipelineService.build_conversation_context(history_source)
            if history_source
            else ""
        )
        conversation_context = ChatWorkingMemoryService.merge_conversation_context(
            memory_prompt,
            base_conversation_context,
        )
        missing_product_code_answer = None
        ambiguous_period_answer = None
        interpretation_without_data_answer = None

        if not canvas_action and not pre_capability_answer and not analysis_mode and not text_task_pure:
            missing_product_code_answer = (
                ChatOperationalParameterService.resolve_missing_product_code_answer(
                    message,
                    conversation_context=conversation_context,
                    previous_messages=history_source,
                )
            )
            ambiguous_period_answer = (
                ChatOperationalParameterService.resolve_ambiguous_period_answer(
                    message,
                    previous_messages=history_source,
                )
            )
            if ChatAnalysisIntentService.is_data_reference_without_tool_data(
                message,
                history_source,
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

        if (
            canvas_action
            or pre_capability_answer
            or missing_product_code_answer
            or ambiguous_period_answer
            or interpretation_without_data_answer
            or skip_tools_for_user_identity
            or skip_tools_for_data_interpretation
            or small_talk_direct
            or utility_direct
            or web_save_sources_direct
            or attachment_welcome_direct
            or text_task_pure
        ) and not canvas_operational_update:
            if skip_tools_for_user_identity:
                pipeline_stages.append("identity_shortcut")
            elif skip_tools_for_data_interpretation:
                pipeline_stages.append("data_interpretation")
            elif canvas_action:
                pipeline_stages.append("canvas")
            elif pre_capability_answer:
                pipeline_stages.append("capabilities")
            elif missing_product_code_answer:
                pipeline_stages.append("operational_parameter")
            elif ambiguous_period_answer:
                pipeline_stages.append("operational_parameter")
            elif interpretation_without_data_answer:
                pipeline_stages.append("data_interpretation_empty")
            elif small_talk_direct:
                pipeline_stages.append("small_talk")
            elif utility_direct:
                pipeline_stages.append("utility_direct")
            elif web_save_sources_direct:
                pipeline_stages.append("web_save_sources")
            elif attachment_welcome_direct:
                pipeline_stages.append("attachment_welcome")
            elif text_task_pure:
                pipeline_stages.append("text_task")
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
            or bool(attachment_welcome_direct)
            or bool(text_task_pure)
            or operational_optimize
            or analysis_mode
            or ChatExternalActionDirectResponseService.should_skip_rag(tool_context)
            or bool(assistant_identity_direct)
        )

        if canvas_action:
            direct_answer = canvas_action.answer
        elif pre_capability_answer:
            direct_answer = pre_capability_answer
        elif small_talk_direct:
            direct_answer = small_talk_direct
        elif utility_direct:
            direct_answer = utility_direct
        elif web_save_sources_direct:
            direct_answer = web_save_sources_direct
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
            web_save_sources_direct
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

        if not direct_answer and interpretation_without_data_answer:
            direct_answer = interpretation_without_data_answer
            skip_rag = True

        if tool_calls:
            from app.application.services.chat_tool_context_service import (
                ChatToolContextService,
            )

            presentation_answer = ChatToolContextService.prefer_presentation_direct_answer(
                direct_answer,
                tool_calls,
            )

            if presentation_answer:
                direct_answer = presentation_answer
                skip_rag = True

        if ChatTextTaskIntentService.is_mixed_text_and_operational(message):
            from app.application.services.chat_text_task_composer_service import (
                ChatTextTaskComposerService,
            )

            mixed_supplement = ChatTextTaskComposerService.build_supplement_for_mixed_turn(
                message=message,
                tool_calls=tool_calls,
            )

            if mixed_supplement:
                if direct_answer:
                    direct_answer = f"{direct_answer.strip()}\n\n---\n\n{mixed_supplement}"
                else:
                    direct_answer = mixed_supplement

                skip_rag = True

                if "text_task_mixed" not in pipeline_stages:
                    pipeline_stages.append("text_task_mixed")

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
                    message="Consultando base de conhecimento autorizada...",
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
                        message="Base de conhecimento não necessária neste turno.",
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
                            f"Base de conhecimento: {len(sources)} trecho(s) "
                            "relevante(s) encontrado(s)."
                        ),
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
                        message=(
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
                        message=(
                            "Base de conhecimento consultada; "
                            "nenhum trecho adicional aplicável."
                        ),
                        entry_id="rag-search",
                    )
                )

        intent_route = ChatIntentRouterService.resolve_executed(
            message=message,
            pipeline_stages=pipeline_stages,
            analysis_mode=bool(analysis_mode),
            text_task_pure=bool(text_task_pure),
            text_task_category=text_task_category if text_task_pure else None,
            skip_rag=bool(skip_rag),
            direct_answer=direct_answer,
            tool_calls=tool_calls,
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
            intent_route=intent_route,
        )

