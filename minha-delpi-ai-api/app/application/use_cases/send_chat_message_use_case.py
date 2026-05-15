import hashlib
import time
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.dto.send_chat_message_response import SendChatMessageResponse
from app.application.services.chat_knowledge_scope_service import ChatKnowledgeScopeService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.rag_context_service import RagContextService
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
    InvalidChatSessionInputError,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
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
        workspace_context_service: ChatWorkspaceContextService | None = None,
        admin_guideline_prompt_service=None,
    ):
        self.chat_repository = chat_repository
        self.audit_repository = audit_repository
        self.llm_gateway = llm_gateway
        self.prompt_policy_service = prompt_policy_service
        self.prompt_builder_service = ChatPromptBuilderService(prompt_policy_service)
        self.knowledge_scope_service = ChatKnowledgeScopeService()
        self.rag_context_service = rag_context_service
        self.chat_tool_context_service = chat_tool_context_service
        self.agent_repository = agent_repository
        self.attachment_repository = attachment_repository
        self.workspace_context_service = workspace_context_service
        self.admin_guideline_prompt_service = admin_guideline_prompt_service

    def execute(self, request: SendChatMessageRequest) -> SendChatMessageResponse:
        message = self._validate_message(request.message)

        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)

        session = self.chat_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        workspace_context = self._build_workspace_context(session, user_id)
        attachments = self._get_message_attachments(request, user_id, session_id)

        previous_messages = self.chat_repository.list_messages_by_session(session_id)
        history = previous_messages[-Settings.CHAT_HISTORY_MAX_MESSAGES:]

        rag = self.rag_context_service.build_context(
            message,
            filters=self.knowledge_scope_service.build_filters(
                user_id=user_id,
                session=session,
                workspace_context=workspace_context,
                attachment_ids=getattr(request, "attachment_ids", None),
            ),
        )
        sources = rag["sources"]

        tool_context = self._build_tool_context(
            request,
            allowed_action_ids=workspace_context.get("allowedActionIds"),
            capabilities=workspace_context.get("capabilities") or {},
        )
        tool_calls = tool_context["toolCalls"]

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
            },
        )

        self._attach_files_to_message(
            request=request,
            user_id=user_id,
            session_id=session_id,
            message_id=user_message.id,
        )

        admin_guidelines_prompt, active_guidelines = self._build_admin_guidelines_prompt()

        llm_messages = self.prompt_builder_service.build_messages(
            history=history,
            current_message=message,
            rag_context=rag["context"],
            tool_context=tool_context["context"],
            project_prompt=workspace_context.get("projectPrompt"),
            agent_prompt=workspace_context.get("agentPrompt"),
            admin_guidelines_prompt=admin_guidelines_prompt,
            attachments=attachments,
        )

        started_at = time.perf_counter()
        answer = self.llm_gateway.generate(llm_messages)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        prompt_tokens_estimated = self._estimate_tokens_from_messages(llm_messages)
        completion_tokens_estimated = self._estimate_tokens(answer)
        total_tokens_estimated = prompt_tokens_estimated + completion_tokens_estimated

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
                "adminGuidelines": self._guideline_metadata(active_guidelines),
                "metrics": {
                    "latencyMs": latency_ms,
                    "promptTokensEstimated": prompt_tokens_estimated,
                    "completionTokensEstimated": completion_tokens_estimated,
                    "totalTokensEstimated": total_tokens_estimated,
                    "estimatedCost": None,
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
                "estimated_cost": None,
            },
        )

        return SendChatMessageResponse(
            messageId=str(assistant_message.id),
            answer=answer,
            sources=sources,
            toolCalls=tool_calls,
        )

    def _build_admin_guidelines_prompt(self) -> tuple[str, list[dict]]:
        if not self.admin_guideline_prompt_service:
            return "", []

        return self.admin_guideline_prompt_service.build_active_guidelines_prompt()

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

    def _build_tool_context(
        self,
        request: SendChatMessageRequest,
        allowed_action_ids: list[str] | None = None,
        capabilities: dict | None = None,
    ) -> dict:
        if not request.access_token:
            return {
                "context": "",
                "toolCalls": [],
            }

        actions_enabled = True
        if capabilities and capabilities.get("actions") is False:
            actions_enabled = False

        return self.chat_tool_context_service.build_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            allowed_action_ids=allowed_action_ids,
            actions_enabled=actions_enabled,
        )

    def _validate_message(self, value: str) -> str:
        if not isinstance(value, str):
            raise InvalidChatSessionInputError("Message must be a string")

        normalized = value.strip()

        if not normalized:
            raise InvalidChatSessionInputError("Message is required")

        if len(normalized) > 8000:
            raise InvalidChatSessionInputError("Message exceeds maximum length")

        return normalized

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
