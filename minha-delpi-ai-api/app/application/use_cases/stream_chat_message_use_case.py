import time
from collections.abc import Iterator
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
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
from app.application.services.chat_turn.chat_stream_session_title_service import (
    ChatStreamSessionTitleService,
)
from app.application.services.chat_turn.chat_stream_turn_prepare_service import (
    ChatStreamTurnPrepareService,
)
from app.application.services.chat_turn.chat_stream_user_message_service import (
    ChatStreamUserMessageService,
)
from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.exceptions.chat_exceptions import (
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
from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)
from app.infrastructure.llm.llm_request_context import llm_generation_scope


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
        self.llm_gateway = llm_gateway
        self.message_security_service = message_security_service or ChatMessageSecurityService(
            audit_repository=audit_repository,
        )
        self.prompt_builder_service = ChatPromptBuilderService(prompt_policy_service)
        self.turn_preparation_service = ChatTurnPreparationService(
            rag_context_service=rag_context_service,
            session_memory_service=session_memory_service,
        )
        self.turn_completion_service = turn_completion_service or ChatTurnCompletionService(
            chat_repository=chat_repository,
            audit_repository=audit_repository,
            session_memory_service=session_memory_service,
        )
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
        self.session_title_service = ChatStreamSessionTitleService()
        self.stream_prepare = ChatStreamTurnPrepareService(
            chat_repository=chat_repository,
            turn_preparation_service=self.turn_preparation_service,
            turn_support=self.turn_support,
            session_title_service=self.session_title_service,
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

        ChatWorkspaceAgentActivationService.prepare_session_for_turn(
            session=session,
            request_agent_id=request.agent_id,
            chat_mode=request.chat_mode,
            update_session_agent_id=self.chat_repository.update_session_agent_id,
        )

        resend_from_message_id = request.resend_from_message_id
        workspace_context = self.turn_support.build_workspace_context(
            session,
            user_id,
            request_agent_id=request.agent_id,
        )
        attachments = self.turn_support.get_message_attachments(request, user_id, session_id)
        previous_messages = self.chat_repository.list_all_messages_by_session(session_id)

        user_persist = ChatStreamUserMessageService.persist(
            chat_repository=self.chat_repository,
            turn_support=self.turn_support,
            request=request,
            message=message,
            session=session,
            user_id=user_id,
            session_id=session_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            resend_from_message_id=resend_from_message_id,
        )

        for event in user_persist.events:
            yield event

        user_message = user_persist.user_message

        ChatTurnSideEffectsService.capture_all_from_turn(
            message=message,
            session=session,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        yield {
            "type": "status",
            "message": ChatAssistantContentService.get(
                "stream",
                "statusUnderstandingQuestion",
            )
            or ChatAssistantContentService.get("stream", "statusConnected"),
        }

        from flask import current_app, has_app_context

        flask_app = current_app._get_current_object() if has_app_context() else None

        prepare_state = self.stream_prepare.start_worker(
            request=request,
            message=message,
            session=session,
            user_id=user_id,
            session_id=session_id,
            resend_from_message_id=resend_from_message_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            user_message=user_message,
            turn_generation_config=turn_generation_config,
            flask_app=flask_app,
        )

        yield from ChatStreamTurnPrepareService.iter_activity_events(prepare_state)
        ChatStreamTurnPrepareService.raise_if_failed(prepare_state)

        prepared = ChatStreamTurnPrepareService.prepared_value(prepare_state)
        context_box = prepare_state.context_box
        workspace_context = context_box["workspace_context"]
        attachments = context_box["attachments"]
        previous_messages = context_box["previous_messages"]
        user_message = context_box.get("user_message")
        existing_user_message = context_box.get("existing_user_message")
        should_generate_session_title = bool(
            context_box.get("should_generate_session_title")
        )

        if should_generate_session_title:
            self.session_title_service.apply_fallback_rename(
                self.chat_repository,
                session_id=session_id,
                user_id=user_id,
                message=message,
            )

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
        sources = prepared.sources
        tool_calls = prepared.tool_calls
        tool_context = prepared.tool_context
        pipeline_timings = prepared.pipeline_timings
        canvas_open_payload = prepared.canvas_open_payload

        answer_parts: list[str] = []
        started_at = time.perf_counter()
        persist_before_playback = Settings.CHAT_PERSIST_BEFORE_PLAYBACK
        assistant_placeholder = None

        yield {"type": "sources", "sources": sources}

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
                "message": ChatAssistantContentService.get(
                    "stream",
                    "statusAssemblingDirectAnswer",
                ),
            }
            answer_parts.append(direct_answer)

            if not persist_before_playback:
                for chunk in ChatExternalActionDirectResponseService.iter_stream_chunks(
                    direct_answer
                ):
                    yield {"type": "token", "content": chunk}
        else:
            yield {
                "type": "status",
                "message": ChatAssistantContentService.get(
                    "stream",
                    "statusGeneratingAnswer",
                ),
            }

            for token in self.llm_gateway.stream(llm_messages):
                answer_parts.append(token)

                if not persist_before_playback:
                    yield {"type": "token", "content": token}

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
                mode=(
                    "stream_update"
                    if persist_before_playback and assistant_placeholder
                    else "stream_create"
                ),
                is_stream=True,
                persist_before_playback=persist_before_playback,
                assistant_placeholder=assistant_placeholder,
            ),
        )

        answer = completion.answer
        assistant_message = completion.assistant_message
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

        if should_generate_session_title:
            self.session_title_service.schedule_llm_refine(
                chat_repository=self.chat_repository,
                llm_gateway=self.llm_gateway,
                session_id=session_id,
                user_id=user_id,
                message=message,
            )
