"""Orquestração do turno send — extraído de ``SendChatMessageUseCase``."""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import partial
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.dto.send_chat_message_response import SendChatMessageResponse
from app.application.services.chat_intelligence_runtime_access import (
    resolve_chat_intelligence_runtime,
)
from app.application.services.chat_llm_gateway_resolver_service import (
    ChatLlmGatewayResolverService,
)
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_turn.chat_turn_completion_service import (
    ChatTurnCompletionInput,
    ChatTurnCompletionService,
    ChatTurnPersistenceOptions,
)
from app.application.services.chat_turn.chat_turn_llm_assembly_service import (
    ChatTurnLlmAssemblyService,
)
from app.application.services.chat_turn.chat_turn_llm_provider_guard_service import (
    ChatTurnLlmProviderGuardService,
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
from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)
from app.domain.services.chat_host_surface_context_service import (
    ChatHostSurfaceContextService,
)
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService
from app.domain.services.chat_response_mode_context_budget_service import (
    ChatResponseModeContextBudgetService,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.llm.llm_request_context import llm_provider_scope


@dataclass(frozen=True)
class ChatSendTurnExecutionDeps:
    chat_repository: ChatSessionRepositoryPort
    message_security_service: ChatMessageSecurityService
    turn_support: ChatTurnUseCaseSupportService
    turn_preparation_service: ChatTurnPreparationService
    prompt_builder_service: ChatPromptBuilderService
    llm_gateway: LlmGatewayPort
    web_search_synthesis_service: ChatWebSearchSynthesisService
    turn_completion_service: ChatTurnCompletionService


class ChatSendTurnExecutionService:
    @classmethod
    def execute_turn(
        cls,
        request: SendChatMessageRequest,
        deps: ChatSendTurnExecutionDeps,
    ) -> SendChatMessageResponse:
        ChatTurnSideEffectsService.warm_learned_normalization()
        user_id = UUID(request.user_id)
        message = deps.message_security_service.secure_message(
            request.message,
            user_id=user_id,
            context=request.context,
            source="chat",
        )
        session_id = UUID(request.session_id)

        session = deps.chat_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        ChatWorkspaceAgentActivationService.prepare_session_for_turn(
            session=session,
            request_agent_id=request.agent_id,
            chat_mode=request.chat_mode,
            request_project_id=request.project_id,
            sync_project_binding=request.sync_project_binding,
            update_session_agent_id=deps.chat_repository.update_session_agent_id,
            update_session_project_id=deps.chat_repository.update_session_project_id,
        )

        supplemental_agent_ids = (
            request.agent_ids[1:]
            if request.agent_ids and len(request.agent_ids) > 1
            else None
        )
        supplemental_project_ids = (
            request.project_ids[1:]
            if request.project_ids and len(request.project_ids) > 1
            else None
        )

        workspace_context = deps.turn_support.build_workspace_context(
            session,
            user_id,
            request_agent_id=request.agent_id,
            supplemental_agent_ids=supplemental_agent_ids,
            supplemental_project_ids=supplemental_project_ids,
        )
        workspace_context = ChatHostSurfaceContextService.enrich_workspace(
            workspace_context,
            message=message,
            host_context=request.host_context,
        )
        effective_provider = ChatLlmGatewayResolverService.resolve_effective_provider(
            workspace_context.get("agent"),
        )

        with llm_provider_scope(effective_provider):
            ChatTurnLlmProviderGuardService.enforce_turn_rate_limit(
                user_id=user_id,
                provider=effective_provider,
            )
            return cls._execute_with_context(
                request=request,
                deps=deps,
                user_id=user_id,
                session_id=session_id,
                session=session,
                message=message,
                workspace_context=workspace_context,
            )

    @classmethod
    def _execute_with_context(
        cls,
        *,
        request: SendChatMessageRequest,
        deps: ChatSendTurnExecutionDeps,
        user_id: UUID,
        session_id: UUID,
        session,
        message: str,
        workspace_context: dict,
    ) -> SendChatMessageResponse:
        attachments = deps.turn_support.get_message_attachments(
            request, user_id, session_id
        )
        attachment_snapshots = deps.turn_support.enrich_attachments_for_message_metadata(
            attachments,
        )
        previous_messages = deps.chat_repository.list_all_messages_by_session(session_id)
        agent_meta = workspace_context.get("agent")
        agent_max = agent_meta.get("maxToolCalls") if isinstance(agent_meta, dict) else None
        max_tool_calls = ChatAdvancedSqlSpecialistService.resolve_max_tool_calls(
            message,
            agent_max,
        )

        user_message = deps.chat_repository.create_message(
            session_id=session_id,
            role="user",
            content=message,
            parent_message_id=session.active_leaf_message_id,
            metadata={
                "context": request.context,
                "agentId": workspace_context.get("agentId"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "attachments": attachment_snapshots,
                **ChatLlmMetadataService.user_message_response_mode(request),
                **ChatLlmMetadataService.user_message_typing_correction(request),
                "delivery": {"status": "submitted"},
            },
        )

        deps.turn_support.attach_files_to_message(
            request=request,
            user_id=user_id,
            session_id=session_id,
            message_id=user_message.id,
        )

        ChatTurnSideEffectsService.capture_all_from_turn(
            message=message,
            session=session,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        prepared = deps.turn_preparation_service.prepare(
            message=message,
            request=request,
            session=session,
            user_id=user_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            history_source=previous_messages,
            build_tool_context=partial(
                deps.turn_support.build_tool_context,
                agent_context=workspace_context.get("agent"),
            ),
            maybe_extend_tool_context=partial(
                deps.turn_support.maybe_extend_tool_context,
                request=request,
            ),
            prepare_history=deps.turn_support.prepare_history,
            history_keep=ChatResponseModeContextBudgetService.history_keep(
                request.response_mode
            ),
            fast_path_enabled=resolve_chat_intelligence_runtime().fast_path_enabled,
            fast_path_max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
            resolve_user_identity_answer=deps.turn_support.bind_user_identity_answer_resolver(
                request.access_token
            ),
            resolve_capabilities_answer=deps.turn_support.bind_capabilities_answer_resolver(
                workspace_context
            ),
            max_external_action_calls=max_tool_calls,
            run_post_rag_web_fallback=lambda: deps.turn_support.run_post_rag_web_fallback(
                request,
                previous_messages=previous_messages,
            ),
        )

        if isinstance(getattr(prepared, "workspace_context", None), dict):
            workspace_context = prepared.workspace_context

        assembly = ChatTurnLlmAssemblyService.assemble(
            request=request,
            message=message,
            user_id=user_id,
            workspace_context=workspace_context,
            attachments=attachments,
            previous_messages=previous_messages,
            prepared=prepared,
            user_message=user_message,
            chat_repository=deps.chat_repository,
            prompt_builder_service=deps.prompt_builder_service,
            web_search_synthesis_service=deps.web_search_synthesis_service,
            build_attachment_context=deps.turn_support.build_attachment_context,
            resolve_llm_user_context=deps.turn_support.resolve_llm_user_context,
            build_admin_guidelines_prompt=deps.turn_support.build_admin_guidelines_prompt,
            embedding_cache_stats=ChatTurnUseCaseSupportService.embedding_cache_stats,
            channel="send",
        )

        started_at = time.perf_counter()
        answer = assembly.direct_answer or deps.llm_gateway.generate(assembly.llm_messages)

        attachments = deps.turn_support.resolve_turn_attachments(
            attachments,
            user_id=user_id,
            session_id=session_id,
            tool_context=prepared.tool_context,
            session=session,
        )

        completion = deps.turn_completion_service.complete_turn(
            ChatTurnCompletionInput(
                request=request,
                message=message,
                user_id=user_id,
                session_id=session_id,
                workspace_context=workspace_context,
                attachments=attachments,
                previous_messages=previous_messages,
                history_source=previous_messages,
                prepared=prepared,
                answer=answer,
                sources=prepared.sources,
                tool_context=prepared.tool_context,
                tool_calls=prepared.tool_calls,
                direct_answer=assembly.direct_answer,
                pipeline_timings=prepared.pipeline_timings,
                pipeline_stages=assembly.pipeline_stages,
                fast_path=prepared.fast_path,
                operational_optimize=prepared.operational_optimize,
                skip_rag=prepared.skip_rag,
                analysis_mode=prepared.analysis_mode,
                llm_messages=assembly.llm_messages,
                admin_debug_payload=assembly.admin_debug_payload,
                active_guidelines=assembly.active_guidelines,
                started_at=started_at,
                user_message=user_message,
                canvas_open_payload=prepared.canvas_open_payload,
            ),
            persistence=ChatTurnPersistenceOptions(mode="send"),
        )

        client_metadata = ChatMessageDeliveryService.client_metadata_for_response(
            completion.assistant_metadata,
        )

        return SendChatMessageResponse(
            messageId=str(completion.assistant_message.id),
            answer=completion.answer,
            sources=completion.sources,
            toolCalls=completion.tool_calls,
            canvasOpen=(
                {
                    "title": completion.canvas_open_payload.title,
                    "markdown": completion.canvas_open_payload.markdown,
                    "sourceMessageId": completion.canvas_open_payload.source_message_id,
                }
                if completion.canvas_open_payload
                else None
            ),
            adminDebug=completion.client_admin_debug,
            metadata=client_metadata or None,
        )
