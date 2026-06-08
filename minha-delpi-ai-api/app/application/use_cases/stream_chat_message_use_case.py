import logging
import queue
import threading
import time
from collections.abc import Iterator
from functools import partial
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_user_context_service import ChatUserContextService
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.rag_context_service import RagContextService
from app.application.services.chat_turn.chat_turn_completion_service import (
    ChatTurnCompletionInput,
    ChatTurnCompletionService,
    ChatTurnPersistenceOptions,
)
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.application.services.chat_turn.chat_turn_side_effects_service import (
    ChatTurnSideEffectsService,
)
from app.application.services.chat_turn.chat_turn_use_case_support_service import (
    ChatTurnUseCaseSupportService,
)
from app.application.services.chat_turn.chat_turn_llm_assembly_service import (
    ChatTurnLlmAssemblyService,
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
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.infrastructure.config.settings import Settings
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.infrastructure.llm.llm_request_context import llm_generation_scope


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
        self.turn_support = ChatTurnUseCaseSupportService(
            agent_repository=agent_repository,
            attachment_repository=attachment_repository,
            chat_attachment_context_service=chat_attachment_context_service,
            chat_history_summary_service=chat_history_summary_service,
            chat_agentic_tool_loop_service=chat_agentic_tool_loop_service,
            workspace_context_service=workspace_context_service,
            admin_guideline_prompt_service=admin_guideline_prompt_service,
            chat_tool_context_service=chat_tool_context_service,
        )

    def stream(self, request: SendChatMessageRequest) -> Iterator[dict]:
        generation_config = ChatLlmMetadataService.resolve_generation_config(request)

        with llm_generation_scope(generation_config):
            yield from self._stream_turn(request)

    def _stream_turn(self, request: SendChatMessageRequest) -> Iterator[dict]:
        ChatTurnSideEffectsService.warm_learned_normalization()
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
        workspace_context = self.turn_support.build_workspace_context(
            session,
            user_id,
            request_agent_id=request.agent_id,
        )
        attachments = self.turn_support.get_message_attachments(request, user_id, session_id)
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

            self.turn_support.attach_files_to_message(
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

            self.turn_support.attach_files_to_message(
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

        ChatTurnSideEffectsService.capture_all_from_turn(
            message=message,
            session=session,
            user_id=request.user_id,
            session_id=request.session_id,
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
                    self.turn_support.build_tool_context,
                    request,
                    agent_context=workspace_context.get("agent"),
                ),
                maybe_extend_tool_context=partial(
                    self.turn_support.maybe_extend_tool_context,
                    request=request,
                ),
                prepare_history=self.turn_support.prepare_history,
                history_keep=Settings.CHAT_HISTORY_MAX_MESSAGES,
                fast_path_enabled=Settings.CHAT_FAST_PATH_ENABLED,
                fast_path_max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
                resolve_user_identity_answer=lambda msg: (
                    self.turn_support.resolve_user_identity_answer(request.access_token, msg)
                    if request.access_token
                    and ChatUserContextService.is_user_identity_question(msg)
                    else None
                ),
                resolve_capabilities_answer=lambda msg: (
                    self.turn_support.resolve_capabilities_answer(workspace_context, msg)
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

        sources = prepared.sources
        tool_calls = prepared.tool_calls
        tool_context = prepared.tool_context
        pipeline_timings = prepared.pipeline_timings
        canvas_open_payload = prepared.canvas_open_payload

        if resend_from_message_id:
            user_message = existing_user_message

        assembly = ChatTurnLlmAssemblyService.assemble(
            request=request,
            message=message,
            user_id=user_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            prepared=prepared,
            user_message=user_message,
            chat_repository=self.chat_repository,
            prompt_builder_service=self.prompt_builder_service,
            web_search_synthesis_service=self.web_search_synthesis_service,
            build_attachment_context=self.turn_support.build_attachment_context,
            resolve_llm_user_context=self.turn_support.resolve_llm_user_context,
            build_admin_guidelines_prompt=self.turn_support.build_admin_guidelines_prompt,
            embedding_cache_stats=ChatTurnUseCaseSupportService.embedding_cache_stats,
            channel="stream",
            patch_user_metadata=user_message is not None,
        )

        direct_answer = assembly.direct_answer
        pipeline_stages = assembly.pipeline_stages
        active_guidelines = assembly.active_guidelines
        llm_messages = assembly.llm_messages
        admin_debug_payload = assembly.admin_debug_payload

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
            "adminGuidelines": ChatTurnUseCaseSupportService.guideline_metadata(active_guidelines),
        }

        yield {
            "type": "admin_guidelines",
            "adminGuidelines": ChatTurnUseCaseSupportService.guideline_metadata(active_guidelines),
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
                fast_path=prepared.fast_path,
                operational_optimize=prepared.operational_optimize,
                skip_rag=prepared.skip_rag,
                analysis_mode=prepared.analysis_mode,
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
