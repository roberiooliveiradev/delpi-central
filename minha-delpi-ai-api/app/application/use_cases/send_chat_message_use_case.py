import hashlib
import time
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.dto.send_chat_message_response import SendChatMessageResponse
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)
from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService
from app.application.services.rag_context_service import RagContextService
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
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.infrastructure.config.settings import Settings


class SendChatMessageUseCase:
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
        self.agent_repository = agent_repository
        self.attachment_repository = attachment_repository
        self.chat_attachment_context_service = chat_attachment_context_service
        self.chat_history_summary_service = chat_history_summary_service
        self.chat_agentic_tool_loop_service = chat_agentic_tool_loop_service
        self.workspace_context_service = workspace_context_service
        self.admin_guideline_prompt_service = admin_guideline_prompt_service

    def execute(self, request: SendChatMessageRequest) -> SendChatMessageResponse:
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

        workspace_context = self._build_workspace_context(session, user_id)
        attachments = self._get_message_attachments(request, user_id, session_id)

        previous_messages = self.chat_repository.list_messages_by_session(session_id)
        attachment_ids = getattr(request, "attachment_ids", None)
        allowed_action_ids = workspace_context.get("allowedActionIds") or []
        operational_optimize = ChatOperationalPipelineService.should_optimize(
            message,
            allowed_action_ids,
            attachment_ids=attachment_ids,
        )

        if operational_optimize:
            keep = max(1, Settings.CHAT_HISTORY_MAX_MESSAGES)
            history_summary, history = "", list(previous_messages[-keep:])
        else:
            history_summary, history = self._prepare_history(previous_messages)

        pipeline_timings = ChatPipelineTimings()

        fast_path = ChatFastPathService.should_use(
            message,
            enabled=Settings.CHAT_FAST_PATH_ENABLED,
            max_chars=Settings.CHAT_FAST_PATH_MAX_CHARS,
            attachment_ids=attachment_ids,
        )

        conversation_context = self._build_conversation_context(previous_messages)

        tool_context = self._build_tool_context(
            request,
            allowed_action_ids=workspace_context.get("allowedActionIds"),
            capabilities=workspace_context.get("capabilities") or {},
            specialization=workspace_context.get("specialization"),
            fast_path=fast_path,
            conversation_context=conversation_context,
        )
        tool_context = self._maybe_extend_tool_context(
            request=request,
            workspace_context=workspace_context,
            tool_context=tool_context,
        )
        tool_calls = tool_context["toolCalls"]
        pipeline_timings.mark("tools_done")

        skip_rag = (
            fast_path
            or operational_optimize
            or ChatExternalActionDirectResponseService.should_skip_rag(tool_context)
        )
        direct_answer = ChatExternalActionDirectResponseService.resolve_answer(tool_context)

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
            ),
        )

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

        if operational_optimize or direct_answer or fast_path:
            admin_guidelines_prompt, active_guidelines = "", []
        else:
            admin_guidelines_prompt, active_guidelines = self._build_admin_guidelines_prompt(
                workspace_context,
            )

        if direct_answer:
            llm_messages = []
        elif fast_path and Settings.CHAT_FAST_PATH_SLIM_PROMPT:
            llm_messages = self.prompt_builder_service.build_fast_path_messages(
                current_message=message,
                history=history[-2:] if history else [],
            )
        else:
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
            )

        started_at = time.perf_counter()

        if direct_answer:
            answer = direct_answer
        else:
            answer = self.llm_gateway.generate(llm_messages)

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

        assistant_message = self.chat_repository.create_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            metadata={
                "provider": Settings.LLM_PROVIDER,
                "model": Settings.OLLAMA_MODEL,
                "agentKey": workspace_context.get("agentKey"),
                "agent": workspace_context.get("agent"),
                "project": workspace_context.get("project"),
                "attachments": attachments,
                "sources": sources,
                "toolCalls": tool_calls,
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
            },
        )

        self.audit_repository.log(
            user_id=user_id,
            action="chat.message.sent",
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
                "latency_ms": latency_ms,
                "prompt_tokens_estimated": prompt_tokens_estimated,
                "completion_tokens_estimated": completion_tokens_estimated,
                "total_tokens_estimated": total_tokens_estimated,
                "estimated_cost": estimated_cost,
            },
        )

        return SendChatMessageResponse(
            messageId=str(assistant_message.id),
            answer=answer,
            sources=sources,
            toolCalls=tool_calls,
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

    def _build_conversation_context(self, previous_messages, limit: int = 8) -> str:
        parts: list[str] = []

        for item in previous_messages[-limit:]:
            role = str(getattr(item, "role", "") or "user").strip()
            content = str(getattr(item, "content", "") or "").strip()

            if content:
                parts.append(f"{role}: {content}")

        return "\n".join(parts)

    def _build_tool_context(
        self,
        request: SendChatMessageRequest,
        allowed_action_ids: list[str] | None = None,
        capabilities: dict | None = None,
        specialization: dict | None = None,
        fast_path: bool = False,
        conversation_context: str | None = None,
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
            conversation_context=conversation_context,
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

    def _prepare_history(self, previous_messages) -> tuple[str, list]:
        if self.chat_history_summary_service:
            return self.chat_history_summary_service.prepare_history(previous_messages)

        keep = Settings.CHAT_HISTORY_MAX_MESSAGES

        return "", list(previous_messages[-keep:])

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
