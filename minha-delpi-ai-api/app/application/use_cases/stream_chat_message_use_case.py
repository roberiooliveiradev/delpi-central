import hashlib
import logging
import queue
import threading
import time
from collections.abc import Iterator
from functools import partial
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService
from app.application.services.rag_context_service import RagContextService
from app.application.services.chat_turn.chat_turn_completion_service import (
    ChatTurnCompletionInput,
    ChatTurnCompletionService,
    ChatTurnPersistenceOptions,
)
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.infrastructure.content.content_service import ContentService
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_external_action_direct_response_service import (
    ChatExternalActionDirectResponseService,
)
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.infrastructure.config.settings import Settings
from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.infrastructure.llm.llm_request_context import get_active_config, llm_generation_scope


logger = logging.getLogger("minha-delpi-ai-api.stream_chat")


class StreamChatMessageUseCase:
    def __init__(
        self,
        chat_repository: ChatSessionRepositoryPort,
        audit_repository: AuditRepositoryPort,
        llm_gateway: LlmGatewayPort,
        prompt_policy_service: PromptPolicyService,
        rag_context_service: RagContextService,
        chat_tool_context_service: ChatToolContextService,
        agent_repository: ChatAgentRepositoryPort | None = None,
        attachment_repository: ChatAttachmentRepositoryPort | None = None,
        chat_attachment_context_service=None,
        chat_history_summary_service=None,
        chat_agentic_tool_loop_service=None,
        workspace_context_service: ChatWorkspaceContextService | None = None,
        admin_guideline_prompt_service=None,
        message_security_service: ChatMessageSecurityService | None = None,
        web_search_synthesis_service: ChatWebSearchSynthesisService | None = None,
        session_memory_service=None,
        turn_completion_service: ChatTurnCompletionService | None = None,
    ):
        self.chat_repository = chat_repository
        self.audit_repository = audit_repository
        self.message_security_service = message_security_service or ChatMessageSecurityService(
            audit_repository=audit_repository,
        )
        self.llm_gateway = llm_gateway
        self.prompt_policy_service = prompt_policy_service
        self.prompt_builder_service = ChatPromptBuilderService(prompt_policy_service)
        self.knowledge_scope_service = ChatKnowledgeScopeService()
        self.rag_context_service = rag_context_service
        self.chat_tool_context_service = chat_tool_context_service
        self.session_memory_service = session_memory_service
        self.turn_preparation_service = ChatTurnPreparationService(
            rag_context_service=rag_context_service,
            session_memory_service=session_memory_service,
        )
        self.turn_completion_service = turn_completion_service or ChatTurnCompletionService(
            chat_repository=chat_repository,
            audit_repository=audit_repository,
            session_memory_service=session_memory_service,
        )
        self.agent_repository = agent_repository
        self.attachment_repository = attachment_repository
        self.chat_attachment_context_service = chat_attachment_context_service
        self.chat_history_summary_service = chat_history_summary_service
        self.chat_agentic_tool_loop_service = chat_agentic_tool_loop_service
        self.workspace_context_service = workspace_context_service
        self.admin_guideline_prompt_service = admin_guideline_prompt_service
        self.web_search_synthesis_service = (
            web_search_synthesis_service
            or ChatWebSearchSynthesisService(llm_gateway=llm_gateway)
        )

    def stream(self, request: SendChatMessageRequest) -> Iterator[dict]:
        generation_config = ChatLlmMetadataService.resolve_generation_config(request)

        with llm_generation_scope(generation_config):
            yield from self._stream_turn(request)

    @staticmethod
    def _warm_learned_normalization() -> None:
        """Aplica regras de vocabulário aprendidas (best-effort, cacheado por TTL)."""
        try:
            from app.application.services.chat_learned_normalization_service import (
                ChatLearnedNormalizationService,
            )

            ChatLearnedNormalizationService().ensure_loaded()
        except Exception:
            return

    @staticmethod
    def _capture_learning_from_turn(*, message: str, session, user_id: str) -> None:
        """Aprendizagem contínua (playbook §17): definição explícita dita no turno.

        Best-effort + savepoint no serviço: nunca quebra nem polui o turno.
        """
        try:
            from app.infrastructure.config.settings import Settings

            if not Settings.CHAT_LEARNING_ENABLED or not Settings.CHAT_LEARNING_CAPTURE_FROM_TURN:
                return

            from app.application.services.chat_learning_capture_service import (
                ChatLearningCaptureService,
            )

            project_id = getattr(session, "project_id", None)
            ChatLearningCaptureService().capture_explicit_definition_from_turn(
                message=message,
                project_id=str(project_id) if project_id else None,
                created_by=user_id,
            )
        except Exception:
            return

    @staticmethod
    def _capture_user_memory_from_turn(
        *, message: str, session, user_id: str, session_id: str
    ) -> None:
        """Memória persistente (playbook Fase 3): preferências/perfil duráveis.

        Best-effort + savepoint no serviço: nunca quebra nem polui o turno.
        """
        try:
            from app.infrastructure.config.settings import Settings

            if not Settings.CHAT_USER_MEMORY_ENABLED or not Settings.CHAT_USER_MEMORY_CAPTURE:
                return

            from app.application.services.chat_user_memory_service import (
                ChatUserMemoryService,
            )

            project_id = getattr(session, "project_id", None)
            ChatUserMemoryService().capture_from_turn(
                message=message,
                user_id=user_id,
                project_id=str(project_id) if project_id else None,
                session_id=session_id,
            )
        except Exception:
            return

    @staticmethod
    def _capture_glossary_from_turn(*, message: str, session, user_id: str) -> None:
        """Glossário vivo (playbook Fase 4): termo desconhecido perguntado vira candidato.

        Best-effort + savepoint no serviço: nunca quebra nem polui o turno.
        """
        try:
            from app.infrastructure.config.settings import Settings

            if not Settings.CHAT_LEARNING_ENABLED or not Settings.CHAT_LEARNING_GLOSSARY_CAPTURE:
                return

            from app.application.services.chat_meaning_discovery_service import (
                ChatMeaningDiscoveryService,
            )

            project_id = getattr(session, "project_id", None)
            ChatMeaningDiscoveryService().capture_unknown_term_from_turn(
                message=message,
                project_id=str(project_id) if project_id else None,
                created_by=user_id,
            )
        except Exception:
            return

    def _stream_turn(self, request: SendChatMessageRequest) -> Iterator[dict]:
        self._warm_learned_normalization()
        turn_generation_config = ChatLlmMetadataService.resolve_generation_config(request)
        user_id = UUID(request.user_id)
        message = self.message_security_service.secure_message(
            request.message,
            user_id=user_id,
            context=request.context,
            source="chat",
        )
        session_id = UUID(request.session_id)

        session = self.chat_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        if request.agent_id and not session.agent_id:
            parsed_agent_id = UUID(request.agent_id)
            self.chat_repository.update_session_agent_id(
                session_id=session_id,
                user_id=user_id,
                agent_id=parsed_agent_id,
            )
            object.__setattr__(session, "agent_id", parsed_agent_id)

        resend_from_message_id = request.resend_from_message_id
        workspace_context = self._build_workspace_context(
            session,
            user_id,
            request_agent_id=request.agent_id,
        )
        attachments = self._get_message_attachments(request, user_id, session_id)
        previous_messages = self.chat_repository.list_all_messages_by_session(session_id)
        user_message = None

        if resend_from_message_id:
            anchor = self.chat_repository.get_user_message_for_user(
                message_id=UUID(resend_from_message_id),
                user_id=user_id,
                session_id=session_id,
            )

            if not anchor:
                raise ChatMessageNotFoundError()

            if anchor.session_id != session_id:
                raise ChatSessionAccessDeniedError()

            siblings = ChatMessageBranchService.list_user_siblings(
                previous_messages,
                anchor,
            )

            user_message = self.chat_repository.create_message(
                session_id=session_id,
                role="user",
                content=message,
                parent_message_id=anchor.parent_message_id,
                metadata={
                    "context": request.context,
                    "agentId": workspace_context.get("agentId"),
                    "agent": workspace_context.get("agent"),
                    "project": workspace_context.get("project"),
                    "attachments": attachments,
                    "stream": True,
                    "branch": {
                        "forkedFromMessageId": str(anchor.id),
                        "variantIndex": len(siblings) + 1,
                    },
                    **ChatLlmMetadataService.user_message_response_mode(request),
                    "delivery": {"status": "submitted"},
                },
            )

            self._attach_files_to_message(
                request=request,
                user_id=user_id,
                session_id=session_id,
                message_id=user_message.id,
            )

            self.chat_repository.set_active_leaf_message_id(
                session_id=session_id,
                user_id=user_id,
                message_id=user_message.id,
            )

            yield {
                "type": "user_persisted",
                "messageId": str(user_message.id),
            }
        else:
            user_message = self.chat_repository.create_message(
                session_id=session_id,
                role="user",
                content=message,
                parent_message_id=session.active_leaf_message_id,
                metadata={
                    "context": request.context,
                    "agentId": workspace_context.get("agentId"),
                    "agent": workspace_context.get("agent"),
                    "project": workspace_context.get("project"),
                    "attachments": attachments,
                    "stream": True,
                    **ChatLlmMetadataService.user_message_response_mode(request),
                    "delivery": {"status": "submitted"},
                },
            )

            self._attach_files_to_message(
                request=request,
                user_id=user_id,
                session_id=session_id,
                message_id=user_message.id,
            )

            # Aponta o ramo ativo para a pergunta imediatamente, para que ela
            # apareça ao reabrir a conversa mesmo se o usuário sair antes da
            # resposta ficar pronta (o placeholder/resposta do assistente
            # avança a folha depois).
            self.chat_repository.set_active_leaf_message_id(
                session_id=session_id,
                user_id=user_id,
                message_id=user_message.id,
            )

            yield {
                "type": "user_persisted",
                "messageId": str(user_message.id),
            }

        self._capture_learning_from_turn(
            message=message,
            session=session,
            user_id=request.user_id,
        )
        self._capture_user_memory_from_turn(
            message=message,
            session=session,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        self._capture_glossary_from_turn(
            message=message, session=session, user_id=request.user_id
        )

        yield {
            "type": "status",
            "message": ContentService.stream().get(
                "statusUnderstandingQuestion",
                ContentService.stream().get(
                    "statusConnected",
                    "Conectado. Preparando resposta...",
                ),
            ),
        }

        activity_queue: queue.Queue = queue.Queue()
        prepared_box: dict = {}
        prepare_error_box: dict = {}
        context_box: dict = {
            "workspace_context": workspace_context,
            "attachments": attachments,
            "previous_messages": previous_messages,
            "user_message": user_message,
        }

        from flask import current_app, has_app_context

        flask_app = current_app._get_current_object() if has_app_context() else None

        # Gate de turno simples (Playbook, seções 4-8): para perguntas simples
        # (identidade, saudação, agradecimento, hora/data, capacidades, "não entendi"),
        # nenhuma etapa técnica é exibida. A resposta direta continua sendo montada
        # pelos serviços existentes. Mutável para ser lido dentro de _run_prepare.
        suppress_activity = {"value": False}

        def _on_stream_activity(entry: dict) -> None:
            if suppress_activity["value"]:
                return
            activity_queue.put(("activity", entry))

        def _run_prepare() -> None:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            workspace_context = context_box["workspace_context"]
            attachments = context_box["attachments"]
            previous_messages = context_box["previous_messages"]
            existing_user_message = None

            from app.domain.services.chat_simple_turn_gate_service import (
                ChatSimpleTurnGateService,
            )

            suppress_activity["value"] = ChatSimpleTurnGateService.is_simple_turn(
                message=message,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
                attachment_ids=getattr(request, "attachment_ids", None),
            )

            _on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Carregando",
                    target="contexto da sessão",
                    phase="prepare",
                    state="active",
                    message=ContentService.stream().get(
                        "statusPreparingContext",
                        "Preparando tudo para te responder...",
                    ),
                    entry_id="prepare-session-context",
                )
            )

            if resend_from_message_id:
                branch_user_message = context_box.get("user_message")

                if not branch_user_message:
                    raise ChatMessageNotFoundError()

                anchor = self.chat_repository.get_user_message_for_user(
                    message_id=UUID(resend_from_message_id),
                    user_id=user_id,
                    session_id=session_id,
                )

                if not anchor:
                    raise ChatMessageNotFoundError()

                if anchor.session_id != session_id:
                    raise ChatSessionAccessDeniedError()

                all_messages = self.chat_repository.list_all_messages_by_session(session_id)
                existing_user_message = branch_user_message
                history_messages = ChatMessageBranchService.build_path_to_message(
                    all_messages,
                    anchor.parent_message_id,
                )
                previous_messages = all_messages
            else:
                history_messages = None

            should_generate_session_title = (
                not resend_from_message_id
                and self._should_generate_session_title(session, previous_messages)
            )

            history_source = history_messages if resend_from_message_id else previous_messages
            agent_meta = workspace_context.get("agent")
            from app.domain.services.chat_advanced_sql_specialist_service import (
                ChatAdvancedSqlSpecialistService,
            )

            agent_max = agent_meta.get("maxToolCalls") if isinstance(agent_meta, dict) else None
            max_tool_calls = ChatAdvancedSqlSpecialistService.resolve_max_tool_calls(
                message,
                agent_max,
            )

            context_box["history_source"] = history_source
            context_box["existing_user_message"] = existing_user_message
            context_box["should_generate_session_title"] = should_generate_session_title
            context_box["user_message"] = existing_user_message or context_box.get("user_message")

            _on_stream_activity(
                ChatStreamActivityService.entry(
                    verb="Pronto",
                    target="contexto da sessão",
                    # mensagem amigável; detalhe técnico fica no painel expandido
                    phase="prepare",
                    state="done",
                    level="success",
                    message="Tudo pronto. Já começo a responder...",
                    entry_id="prepare-session-context",
                )
            )

            prepared_box["value"] = self.turn_preparation_service.prepare(
                message=message,
                request=request,
                session=session,
                user_id=user_id,
                workspace_context=workspace_context,
                attachments=attachments,
                previous_messages=previous_messages,
                history_source=history_source,
                build_tool_context=partial(
                    self._build_tool_context,
                    agent_context=workspace_context.get("agent"),
                ),
                maybe_extend_tool_context=self._maybe_extend_tool_context,
                prepare_history=self._prepare_history,
                history_keep=Settings.CHAT_HISTORY_MAX_MESSAGES,
                fast_path_enabled=Settings.CHAT_FAST_PATH_ENABLED,
                fast_path_max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
                resolve_user_identity_answer=lambda msg: (
                    self._resolve_user_identity_answer(request.access_token, msg)
                    if request.access_token
                    and ChatUserContextService.is_user_identity_question(msg)
                    else None
                ),
                resolve_capabilities_answer=lambda msg: (
                    self._resolve_capabilities_answer(workspace_context, msg)
                    if ChatCapabilitiesService.is_capability_inquiry(msg)
                    else None
                ),
                max_external_action_calls=max_tool_calls,
                on_stream_activity=_on_stream_activity,
            )

        def _prepare_worker() -> None:
            try:
                with llm_generation_scope(turn_generation_config):
                    if flask_app is not None:
                        with flask_app.app_context():
                            _run_prepare()
                    else:
                        _run_prepare()
            except Exception as exc:
                prepare_error_box["error"] = exc
                # Avisa no log que algo falhou no meio do caminho (sempre visível,
                # mesmo em turno simples), em vez de o stream parar sem explicação.
                try:
                    from app.application.services.chat_stream_activity_service import (
                        ChatStreamActivityService,
                    )

                    activity_queue.put(
                        (
                            "activity",
                            ChatStreamActivityService.entry(
                                verb="Falhou",
                                target="preparação da resposta",
                                phase="prepare",
                                level="error",
                                state="failed",
                                message="Tive um problema ao preparar a sua resposta.",
                                detail=str(exc)[:300],
                                entry_id="prepare-failed",
                            ),
                        )
                    )
                except Exception:
                    pass
            finally:
                activity_queue.put(("done", None))

        threading.Thread(target=_prepare_worker, daemon=True).start()

        while True:
            kind, payload = activity_queue.get()

            if kind == "activity":
                yield {
                    "type": "activity",
                    "entry": payload,
                }
                continue

            if kind == "done":
                break

        if prepare_error_box.get("error"):
            raise prepare_error_box["error"]

        prepared = prepared_box["value"]
        workspace_context = context_box["workspace_context"]
        attachments = context_box["attachments"]
        previous_messages = context_box["previous_messages"]
        user_message = context_box.get("user_message")
        existing_user_message = context_box.get("existing_user_message")
        should_generate_session_title = bool(
            context_box.get("should_generate_session_title")
        )
        if should_generate_session_title:
            self.chat_repository.rename_session(
                session_id=session_id,
                user_id=user_id,
                title=self._fallback_title_from_message(message),
            )

        operational_optimize = prepared.operational_optimize
        analysis_mode = prepared.analysis_mode
        fast_path = prepared.fast_path
        skip_rag = prepared.skip_rag
        history_summary = prepared.history_summary
        history = prepared.history
        tool_context = prepared.tool_context
        tool_calls = prepared.tool_calls
        direct_answer = prepared.direct_answer
        rag = prepared.rag
        sources = prepared.sources
        pipeline_timings = prepared.pipeline_timings
        pipeline_stages = prepared.pipeline_stages
        canvas_open_payload = prepared.canvas_open_payload

        direct_answer, pipeline_stages = self.web_search_synthesis_service.enhance_prepared_turn(
            message=message,
            tool_context=tool_context,
            direct_answer=direct_answer,
            pipeline_stages=pipeline_stages,
        )

        intelligence_metadata = ChatIntelligenceMetadataService.build(
            sources=sources,
            tool_context=tool_context,
            embedding_cache_stats=self._embedding_cache_stats(),
            pipeline_timings=pipeline_timings.to_dict(),
            pipeline=ChatIntelligenceMetadataService.build_pipeline_flags(
                fast_path=fast_path,
                operational_optimize=operational_optimize,
                tool_context=tool_context,
                skip_rag=skip_rag,
                analysis_mode=analysis_mode,
                stages=pipeline_stages,
            ),
        )

        if resend_from_message_id:
            user_message = existing_user_message

        if user_message is not None:
            self.chat_repository.patch_message_metadata(
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

        if operational_optimize or direct_answer:
            admin_guidelines_prompt, active_guidelines = "", []
        else:
            admin_guidelines_prompt, active_guidelines = self._build_admin_guidelines_prompt(
                workspace_context,
            )

        if direct_answer:
            llm_messages = []
        else:
            user_context = self._resolve_llm_user_context(
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

            llm_messages = self.prompt_builder_service.build_messages(
                history=history,
                current_message=message,
                rag_context=rag["context"],
                tool_context=tool_context["context"],
                project_prompt=workspace_context.get("projectPrompt"),
                agent_prompt=workspace_context.get("agentPrompt"),
                admin_guidelines_prompt=admin_guidelines_prompt,
                attachments=attachments,
                attachment_context=self._build_attachment_context(
                    user_id=user_id,
                    session_id=session_id,
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
                text_task_attachment_context=self._build_attachment_context(
                    user_id=user_id,
                    session_id=session_id,
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

        answer_parts: list[str] = []
        started_at = time.perf_counter()
        persist_before_playback = Settings.CHAT_PERSIST_BEFORE_PLAYBACK
        assistant_placeholder = None

        yield {
            "type": "sources",
            "sources": sources,
        }

        yield {
            "type": "tool_calls",
            "toolCalls": tool_calls,
            "adminGuidelines": self._guideline_metadata(active_guidelines),
        }

        yield {
            "type": "admin_guidelines",
            "adminGuidelines": self._guideline_metadata(active_guidelines),
        }

        if persist_before_playback:
            assistant_placeholder = self.chat_repository.create_message(
                session_id=session_id,
                role="assistant",
                content="",
                parent_message_id=user_message.id if user_message else None,
                metadata=ChatMessageDeliveryService.generating_metadata(
                    {
                        "agentId": workspace_context.get("agentId"),
                        "stream": True,
                    }
                ),
            )
            self.chat_repository.set_active_leaf_message_id(
                session_id=session_id,
                user_id=user_id,
                message_id=assistant_placeholder.id,
            )
            yield {
                "type": "assistant_pending",
                "messageId": str(assistant_placeholder.id),
            }

        if direct_answer:
            yield {
                "type": "status",
                "message": ContentService.stream().get(
                    "statusAssemblingDirectAnswer",
                    "Montando resposta a partir dos dados consultados...",
                ),
            }
            answer_parts.append(direct_answer)
            if not persist_before_playback:
                for chunk in ChatExternalActionDirectResponseService.iter_stream_chunks(
                    direct_answer
                ):
                    yield {
                        "type": "token",
                        "content": chunk,
                    }
        else:
            yield {
                "type": "status",
                "message": ContentService.stream().get(
                    "statusGeneratingAnswer",
                    "Gerando resposta em linguagem natural...",
                ),
            }

            for token in self.llm_gateway.stream(llm_messages):
                answer_parts.append(token)
                if not persist_before_playback:
                    yield {
                        "type": "token",
                        "content": token,
                    }

        answer = "".join(answer_parts).strip()

        completion = self.turn_completion_service.complete_turn(
            ChatTurnCompletionInput(
                request=request,
                message=message,
                user_id=user_id,
                session_id=session_id,
                workspace_context=workspace_context,
                attachments=attachments,
                previous_messages=previous_messages,
                history_source=context_box.get("history_source") or previous_messages,
                prepared=prepared,
                answer=answer,
                sources=sources,
                tool_context=tool_context,
                tool_calls=tool_calls,
                direct_answer=direct_answer,
                pipeline_timings=pipeline_timings,
                pipeline_stages=pipeline_stages,
                fast_path=fast_path,
                operational_optimize=operational_optimize,
                skip_rag=skip_rag,
                analysis_mode=analysis_mode,
                llm_messages=llm_messages,
                admin_debug_payload=admin_debug_payload,
                active_guidelines=active_guidelines,
                started_at=started_at,
                user_message=user_message,
                canvas_open_payload=canvas_open_payload,
            ),
            persistence=ChatTurnPersistenceOptions(
                mode="stream_update" if persist_before_playback and assistant_placeholder else "stream_create",
                is_stream=True,
                persist_before_playback=persist_before_playback,
                assistant_placeholder=assistant_placeholder,
            ),
        )

        answer = completion.answer
        assistant_message = completion.assistant_message
        assistant_metadata = completion.assistant_metadata
        tool_calls = completion.tool_calls
        canvas_open_payload = completion.canvas_open_payload
        client_admin_debug = completion.client_admin_debug

        if canvas_open_payload:
            yield {
                "type": "canvas_open",
                "title": canvas_open_payload.title,
                "markdown": canvas_open_payload.markdown,
                "sourceMessageId": canvas_open_payload.source_message_id,
                "messageId": str(assistant_message.id),
            }

        if persist_before_playback:
            yield {
                "type": "playback",
                "messageId": str(assistant_message.id),
                "answer": answer,
                "sources": sources,
                "toolCalls": tool_calls,
                "adminDebug": client_admin_debug,
            }

        done_event = {
            "type": "done",
            "messageId": str(assistant_message.id),
            "answer": answer,
            "sources": sources,
            "toolCalls": tool_calls,
            "playback": persist_before_playback,
            "adminDebug": client_admin_debug,
        }

        if canvas_open_payload:
            done_event["canvasOpen"] = {
                "title": canvas_open_payload.title,
                "markdown": canvas_open_payload.markdown,
                "sourceMessageId": canvas_open_payload.source_message_id,
            }

        yield done_event

        if should_generate_session_title and Settings.CHAT_SESSION_TITLE_LLM_ENABLED:
            from flask import has_app_context

            if has_app_context():
                self._schedule_session_title_llm_refine(
                    session_id=session_id,
                    user_id=user_id,
                    message=message,
                )

    def _build_admin_guidelines_prompt(self, workspace_context: dict) -> tuple[str, list[dict]]:
        if not self.admin_guideline_prompt_service:
            return "", []

        specialization = workspace_context.get("specialization") or {}
        categories = specialization.get("guidelineCategories")

        return self.admin_guideline_prompt_service.build_active_guidelines_prompt(
            categories=categories,
        )

    def _guideline_metadata(self, guidelines: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
            }
            for item in guidelines
        ]

    def _build_workspace_context(
        self,
        session,
        user_id: UUID,
        request_agent_id: str | None = None,
    ) -> dict:
        if self.workspace_context_service:
            return self.workspace_context_service.build_context(
                session=session,
                user_id=user_id,
                request_agent_id=request_agent_id,
            )

        agent = self._get_session_agent(session, user_id)

        from app.application.services.chat_agent_skills_service import ChatAgentSkillsService

        return {
            "project": None,
            "agent": self._agent_metadata(agent),
            "projectPrompt": None,
            "agentPrompt": agent.system_prompt if agent else None,
            "agentId": str(agent.id) if agent else (str(session.agent_id) if session.agent_id else None),
            "allowedActionIds": [],
            "actionsEnabled": False,
            "userActivatedAgent": bool(session.agent_id or request_agent_id),
            "capabilities": {},
            "skills": ChatAgentSkillsService.resolve(
                agent_metadata=agent.metadata if agent else {},
                allowed_action_ids=[],
                has_agent=bool(agent),
            ),
        }

    def _get_session_agent(self, session, user_id: UUID):
        if not self.agent_repository or not session.agent_id:
            return None

        return self.agent_repository.get_enabled_by_id(
            session.agent_id,
            user_id=user_id,
        )

    def _get_message_attachments(
        self,
        request: SendChatMessageRequest,
        user_id: UUID,
        session_id: UUID,
    ) -> list[dict]:
        if not self.attachment_repository or not request.attachment_ids:
            return []

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        attachments = self.attachment_repository.list_attachments_by_ids(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        return [
            {
                "id": str(attachment.id),
                "filename": attachment.filename,
                "original_filename": attachment.original_filename,
                "content_type": attachment.content_type,
                "size_bytes": attachment.size_bytes,
                "status": attachment.status,
                "metadata": attachment.metadata,
            }
            for attachment in attachments
        ]

    def _attach_files_to_message(
        self,
        request: SendChatMessageRequest,
        user_id: UUID,
        session_id: UUID,
        message_id: UUID,
    ) -> None:
        if not self.attachment_repository or not request.attachment_ids:
            return

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        self.attachment_repository.attach_to_message(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            message_id=message_id,
        )

    def _prepare_history(self, previous_messages) -> tuple[str, list]:
        if self.chat_history_summary_service:
            return self.chat_history_summary_service.prepare_history(previous_messages)

        keep = Settings.CHAT_HISTORY_MAX_MESSAGES

        return "", list(previous_messages[-keep:])

    def _build_attachment_context(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        request: SendChatMessageRequest,
    ) -> str:
        if not self.chat_attachment_context_service or not request.attachment_ids:
            return ""

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        return self.chat_attachment_context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

    def _agent_metadata(self, agent) -> dict | None:
        if not agent:
            return None

        return {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "metadata": agent.metadata,
        }

    def _should_generate_session_title(self, session, previous_messages) -> bool:
        if previous_messages:
            return False

        title = (session.title or "").strip().lower()
        empty_titles = {
            "",
            *(
                str(item).strip().lower()
                for item in ContentService.stream().get("sessionTitleEmptyValues") or ()
            ),
        }

        return title in empty_titles

    def _schedule_session_title_llm_refine(
        self,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        from flask import current_app

        app = current_app._get_current_object()

        def worker() -> None:
            with app.app_context():
                try:
                    self._generate_and_apply_session_title(
                        session_id=session_id,
                        user_id=user_id,
                        message=message,
                    )
                    from app.extensions.db import db

                    db.session.commit()
                except Exception:
                    from app.extensions.db import db

                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    logger.exception("session_title_llm_refine_failed")

        threading.Thread(target=worker, daemon=True).start()

    def _generate_and_apply_session_title(
        self,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        fallback_title = self._fallback_title_from_message(message)

        stream_texts = ContentService.stream()
        title_system = str(
            stream_texts.get("titleGenerationSystem")
            or (
                "Você cria títulos curtos para conversas corporativas. "
                "Responda apenas com o título, em português, sem aspas, "
                "sem ponto final, com no máximo 6 palavras."
            )
        )
        title_user_template = str(
            stream_texts.get("titleGenerationUserTemplate")
            or "Crie um título curto para esta conversa:\n\n{message}"
        )

        try:
            generated_title = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": title_system,
                    },
                    {
                        "role": "user",
                        "content": title_user_template.format(message=message),
                    },
                ]
            ).strip()
        except Exception:
            generated_title = fallback_title

        title = self._normalize_generated_title(generated_title) or fallback_title

        self.chat_repository.rename_session(
            session_id=session_id,
            user_id=user_id,
            title=title,
        )

    def _normalize_generated_title(self, value: str) -> str:
        normalized = " ".join(value.replace("\n", " ").split())
        normalized = normalized.strip(" .\"'`")

        if not normalized:
            return ""

        if len(normalized) > 80:
            normalized = normalized[:80].rstrip()

        return normalized

    def _fallback_title_from_message(self, message: str) -> str:
        normalized = " ".join(message.split()).strip()

        if not normalized:
            return str(
                ContentService.stream().get("sessionTitleDefault") or "Nova conversa"
            )

        if len(normalized) <= 48:
            return normalized

        return normalized[:48].rstrip() + "..."

    def _maybe_extend_tool_context(
        self,
        *,
        request: SendChatMessageRequest,
        workspace_context: dict,
        tool_context: dict,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        on_stream_activity=None,
    ) -> dict:
        from app.application.services.chat_small_talk_service import ChatSmallTalkService

        if ChatSmallTalkService.is_small_talk(request.message):
            return tool_context

        from app.application.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )

        if ChatUtilityDirectAnswerService.is_utility_question(request.message):
            return tool_context

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(request.message):
            return tool_context

        if not self.chat_agentic_tool_loop_service or not request.access_token:
            return tool_context

        specialization = workspace_context.get("specialization") or {}
        allowed_tool_names = None

        if isinstance(specialization, dict):
            allowed_tool_names = specialization.get("allowedTools")

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target="passos adicionais (agentic)",
                    message="Verificando se preciso de mais alguma informação...",
                    detail="Verificando se ainda faltam ferramentas para responder.",
                )
            )

        return self.chat_agentic_tool_loop_service.extend_tool_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            tool_context=tool_context,
            allowed_tool_names=allowed_tool_names,
            allowed_action_ids=workspace_context.get("allowedActionIds"),
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

    def _embedding_cache_stats(self) -> dict | None:
        try:
            from app.composition.external_action_composer import get_embedding_cache_stats

            return get_embedding_cache_stats()
        except Exception:
            return None

    def _build_tool_context(
        self,
        request: SendChatMessageRequest,
        allowed_action_ids: list[str] | None = None,
        capabilities: dict | None = None,
        specialization: dict | None = None,
        fast_path: bool = False,
        previous_messages: list | None = None,
        max_external_action_calls: int | None = None,
        on_stream_activity=None,
        agent_context: dict | None = None,
        working_memory: dict | None = None,
    ) -> dict:
        if not request.access_token:
            return {
                "context": "",
                "toolCalls": [],
            }

        actions_enabled = True
        if capabilities and capabilities.get("actions") is False:
            actions_enabled = False

        allowed_tool_names = None

        if isinstance(specialization, dict):
            allowed_tool_names = specialization.get("allowedTools")

        return self.chat_tool_context_service.build_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            allowed_action_ids=allowed_action_ids,
            actions_enabled=actions_enabled,
            allowed_tool_names=allowed_tool_names,
            fast_path=fast_path,
            previous_messages=previous_messages,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
            agent_context=agent_context,
            working_memory=working_memory,
            attachment_context=self._build_attachment_context(
                user_id=UUID(request.user_id),
                session_id=UUID(request.session_id),
                request=request,
            ),
            attachment_ids=getattr(request, "attachment_ids", None),
            session_id=str(request.session_id) if getattr(request, "session_id", None) else None,
        )

    def _estimate_cost(self, *, prompt_tokens: int, completion_tokens: int) -> float | None:
        active = get_active_config()

        return LlmCostEstimatorService().estimate_cost(
            provider=Settings.LLM_PROVIDER,
            model=active.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _estimate_tokens_from_messages(self, messages: list[dict]) -> int:
        total = 0

        for item in messages:
            if isinstance(item, dict):
                total += self._estimate_tokens(str(item.get("content") or ""))

        return total

    def _estimate_tokens(self, value: str) -> int:
        normalized = str(value or "").strip()

        if not normalized:
            return 0

        return max(1, round(len(normalized) / 4))

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _resolve_llm_user_context(
        self,
        access_token: str | None,
        message: str,
        *,
        operational_optimize: bool,
        analysis_mode: bool = False,
    ) -> str | None:
        if analysis_mode and not ChatUserContextService.is_user_identity_question(message):
            return None

        if (
            operational_optimize
            and Settings.CHAT_OPERATIONAL_SLIM_USER_CONTEXT
            and not ChatUserContextService.is_user_identity_question(message)
        ):
            return None

        block = self._build_user_context(access_token)
        return block or None

    def _build_user_context(self, access_token: str | None) -> str:
        if not access_token:
            return ""

        from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

        service = ChatUserContextService(core_api_gateway=CoreApiHttpGateway())
        return service.build_user_context(access_token)

    def _resolve_user_identity_answer(self, access_token: str | None, message: str) -> str | None:
        if not access_token:
            return None

        from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

        service = ChatUserContextService(core_api_gateway=CoreApiHttpGateway())
        return service.build_direct_answer(access_token, message)

    def _resolve_capabilities_answer(
        self,
        workspace_context: dict,
        message: str,
    ) -> str | None:
        allowed = workspace_context.get("allowedActionIds") or []
        catalog = ChatCapabilitiesService.load_action_catalog_for_agent(allowed)
        return ChatCapabilitiesService.resolve_capability_answer(
            message=message,
            workspace_context=workspace_context,
            allowed_action_ids=allowed,
            action_catalog=catalog,
        )
