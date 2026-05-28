import hashlib
import logging
import threading
import time
from collections.abc import Iterator
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
from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_user_context_service import ChatUserContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService
from app.application.services.rag_context_service import RagContextService
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
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
        self.turn_preparation_service = ChatTurnPreparationService(
            rag_context_service=rag_context_service,
        )
        self.agent_repository = agent_repository
        self.attachment_repository = attachment_repository
        self.chat_attachment_context_service = chat_attachment_context_service
        self.chat_history_summary_service = chat_history_summary_service
        self.chat_agentic_tool_loop_service = chat_agentic_tool_loop_service
        self.workspace_context_service = workspace_context_service
        self.admin_guideline_prompt_service = admin_guideline_prompt_service

    def stream(self, request: SendChatMessageRequest) -> Iterator[dict]:
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

        if request.agent_key and not session.agent_key:
            self.chat_repository.update_session_agent_key(
                session_id=session_id,
                user_id=user_id,
                agent_key=request.agent_key,
            )
            object.__setattr__(session, "agent_key", request.agent_key)

        yield {
            "type": "status",
            "message": ContentService.stream().get(
                "statusConnected",
                "Conectado. Preparando resposta...",
            ),
        }

        workspace_context = self._build_workspace_context(session, user_id)
        attachments = self._get_message_attachments(request, user_id, session_id)

        resend_from_message_id = request.resend_from_message_id
        existing_user_message = None

        if resend_from_message_id:
            existing_user_message = self.chat_repository.update_user_message(
                message_id=UUID(resend_from_message_id),
                user_id=user_id,
                content=message,
                metadata_patch={"editMode": "resend"},
            )

            if not existing_user_message:
                raise ChatMessageNotFoundError()

            if existing_user_message.session_id != session_id:
                raise ChatSessionAccessDeniedError()

            self.chat_repository.delete_messages_after(
                session_id=session_id,
                message_id=existing_user_message.id,
                user_id=user_id,
            )

            all_messages = self.chat_repository.list_messages_by_session(session_id)
            history_messages = [
                item
                for item in all_messages
                if item.id != existing_user_message.id
            ]
            previous_messages = all_messages
        else:
            history_messages = None
            previous_messages = self.chat_repository.list_messages_by_session(session_id)

        should_generate_session_title = (
            not resend_from_message_id
            and self._should_generate_session_title(session, previous_messages)
        )
        if should_generate_session_title:
            self.chat_repository.rename_session(
                session_id=session_id,
                user_id=user_id,
                title=self._fallback_title_from_message(message),
            )

        history_source = history_messages if resend_from_message_id else previous_messages
        agent_meta = workspace_context.get("agent")
        max_tool_calls = agent_meta.get("maxToolCalls") if isinstance(agent_meta, dict) else None

        prepared = self.turn_preparation_service.prepare(
            message=message,
            request=request,
            session=session,
            user_id=user_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            history_source=history_source,
            build_tool_context=self._build_tool_context,
            maybe_extend_tool_context=self._maybe_extend_tool_context,
            prepare_history=self._prepare_history,
            history_keep=Settings.CHAT_HISTORY_MAX_MESSAGES,
            fast_path_enabled=Settings.CHAT_FAST_PATH_ENABLED,
            fast_path_max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
            resolve_user_identity_answer=lambda msg: (
                self._resolve_user_identity_answer(request.access_token, msg)
                if request.access_token and ChatUserContextService.is_user_identity_question(msg)
                else None
            ),
            resolve_assistant_identity_answer=lambda msg: (
                ChatAssistantIdentityService.build_direct_answer(
                    message=msg,
                    workspace_context=workspace_context,
                )
                if ChatAssistantIdentityService.is_assistant_identity_question(msg)
                else None
            ),
            resolve_capabilities_answer=lambda msg: (
                self._resolve_capabilities_answer(workspace_context, msg)
                if ChatCapabilitiesService.is_capability_inquiry(msg)
                else None
            ),
            max_external_action_calls=max_tool_calls,
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
        canvas_open_payload = prepared.canvas_open_payload
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
            ),
        )

        if resend_from_message_id:
            user_message = existing_user_message
        else:
            user_message = self.chat_repository.create_message(
                session_id=session_id,
                role="user",
                content=message,
                metadata={
                    "context": request.context,
                    "agentKey": workspace_context.get("agentKey"),
                    "agent": workspace_context.get("agent"),
                    "project": workspace_context.get("project"),
                    "attachments": attachments,
                    "stream": True,
                    "rag": {
                        "sources": sources,
                    },
                    "toolCalls": tool_calls,
                    "intelligence": intelligence_metadata,
                },
            )

            self._attach_files_to_message(
                request=request,
                user_id=user_id,
                session_id=session_id,
                message_id=user_message.id,
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
            user_context = self._build_user_context(request.access_token)
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
                user_context=user_context,
                skills=workspace_context.get("skills"),
            )

        answer_parts: list[str] = []
        started_at = time.perf_counter()
        # Respostas diretas não precisam de placeholder/playback; manter streaming de tokens
        # mesmo quando o modo persist-before-playback está habilitado.
        #
        # Exceção: quando há `canvas_open_payload`, o frontend espera playback para
        # persistir a mensagem e abrir a lousa com referência ao `messageId`.
        persist_before_playback = Settings.CHAT_PERSIST_BEFORE_PLAYBACK and not (
            bool(direct_answer) and not canvas_open_payload
        )
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
                metadata=ChatMessageDeliveryService.generating_metadata(
                    {
                        "agentKey": workspace_context.get("agentKey"),
                        "stream": True,
                    }
                ),
            )
            yield {
                "type": "assistant_pending",
                "messageId": str(assistant_placeholder.id),
            }

        if direct_answer:
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
            for token in self.llm_gateway.stream(llm_messages):
                answer_parts.append(token)
                if not persist_before_playback:
                    yield {
                        "type": "token",
                        "content": token,
                    }

        answer = "".join(answer_parts).strip()
        pipeline_timings.mark("llm_done")
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
            ),
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        prompt_tokens_estimated = self._estimate_tokens_from_messages(llm_messages)
        completion_tokens_estimated = self._estimate_tokens(answer)
        total_tokens_estimated = prompt_tokens_estimated + completion_tokens_estimated
        estimated_cost = self._estimate_cost(
            prompt_tokens=prompt_tokens_estimated,
            completion_tokens=completion_tokens_estimated,
        )

        assistant_metadata = {
            "provider": Settings.LLM_PROVIDER,
            "model": Settings.OLLAMA_MODEL,
            "agentKey": workspace_context.get("agentKey"),
            "agent": workspace_context.get("agent"),
            "project": workspace_context.get("project"),
            "attachments": attachments,
            "sources": sources,
            "toolCalls": tool_calls,
            "stream": True,
            "rag": {
                "enabled": True,
                "sourceCount": len(sources),
            },
            "intelligence": intelligence_metadata,
            "adminGuidelines": self._guideline_metadata(active_guidelines),
            "metrics": {
                "latencyMs": latency_ms,
                "promptTokensEstimated": prompt_tokens_estimated,
                "completionTokensEstimated": completion_tokens_estimated,
                "totalTokensEstimated": total_tokens_estimated,
                "estimatedCost": estimated_cost,
            },
            "directResponse": bool(direct_answer),
        }

        if canvas_open_payload:
            assistant_metadata["canvasOpen"] = {
                "title": canvas_open_payload.title,
                "markdown": canvas_open_payload.markdown,
                "sourceMessageId": canvas_open_payload.source_message_id,
            }

        if persist_before_playback:
            assistant_metadata = ChatMessageDeliveryService.ready_metadata(
                assistant_metadata,
                playback_pending=True,
            )

        if assistant_placeholder:
            assistant_message = self.chat_repository.update_assistant_message(
                assistant_placeholder.id,
                answer,
                assistant_metadata,
            )
        else:
            assistant_message = self.chat_repository.create_message(
                session_id=session_id,
                role="assistant",
                content=answer,
                metadata=assistant_metadata,
            )

        if not assistant_message:
            raise RuntimeError("Falha ao persistir mensagem do assistente.")

        self.audit_repository.log(
            user_id=user_id,
            action="chat.message.streamed",
            prompt_hash=self._hash_prompt(message),
            context=request.context,
            tool_calls=tool_calls,
            metadata={
                "session_id": str(session_id),
                "provider": Settings.LLM_PROVIDER,
                "model": Settings.OLLAMA_MODEL,
                "agentKey": workspace_context.get("agentKey"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "attachments": attachments,
                "sources": sources,
                "rag_enabled": True,
                "tool_count": len(tool_calls),
                "admin_guideline_count": len(active_guidelines),
                "admin_guidelines": self._guideline_metadata(active_guidelines),
                "agent_key": workspace_context.get("agentKey"),
                "agent": workspace_context.get("agent"),
                "latency_ms": latency_ms,
                "prompt_tokens_estimated": prompt_tokens_estimated,
                "completion_tokens_estimated": completion_tokens_estimated,
                "total_tokens_estimated": total_tokens_estimated,
                "estimated_cost": estimated_cost,
            },
        )

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
            }

        done_event = {
            "type": "done",
            "messageId": str(assistant_message.id),
            "answer": answer,
            "sources": sources,
            "toolCalls": tool_calls,
            "playback": persist_before_playback,
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

    def _build_workspace_context(self, session, user_id: UUID) -> dict:
        if self.workspace_context_service:
            return self.workspace_context_service.build_context(
                session=session,
                user_id=user_id,
            )

        agent = self._get_session_agent(session, user_id)

        from app.application.services.chat_agent_skills_service import ChatAgentSkillsService

        return {
            "project": None,
            "agent": self._agent_metadata(agent),
            "projectPrompt": None,
            "agentPrompt": agent.system_prompt if agent else None,
            "agentKey": agent.key if agent else session.agent_key,
            "allowedActionIds": [],
            "capabilities": {},
            "skills": ChatAgentSkillsService.resolve(
                agent_metadata=agent.metadata if agent else {},
                allowed_action_ids=[],
                has_agent=bool(agent),
            ),
        }

    def _get_session_agent(self, session, user_id: UUID):
        if not self.agent_repository or not session.agent_key:
            return None

        return self.agent_repository.get_enabled_by_key(
            session.agent_key,
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
            "key": agent.key,
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
    ) -> dict:
        if not self.chat_agentic_tool_loop_service or not request.access_token:
            return tool_context

        specialization = workspace_context.get("specialization") or {}
        allowed_tool_names = None

        if isinstance(specialization, dict):
            allowed_tool_names = specialization.get("allowedTools")

        return self.chat_agentic_tool_loop_service.extend_tool_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            tool_context=tool_context,
            allowed_tool_names=allowed_tool_names,
            allowed_action_ids=workspace_context.get("allowedActionIds"),
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
        )

    def _estimate_cost(self, *, prompt_tokens: int, completion_tokens: int) -> float | None:
        return LlmCostEstimatorService().estimate_cost(
            provider=Settings.LLM_PROVIDER,
            model=Settings.OLLAMA_MODEL if Settings.LLM_PROVIDER != "vllm" else Settings.VLLM_MODEL,
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
