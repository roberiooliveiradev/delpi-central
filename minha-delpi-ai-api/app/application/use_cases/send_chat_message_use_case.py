import hashlib
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.dto.send_chat_message_response import SendChatMessageResponse
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.rag_context_service import RagContextService
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
    InvalidChatSessionInputError,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
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
    ):
        self.chat_repository = chat_repository
        self.audit_repository = audit_repository
        self.llm_gateway = llm_gateway
        self.prompt_policy_service = prompt_policy_service
        self.rag_context_service = rag_context_service
        self.chat_tool_context_service = chat_tool_context_service

    def execute(self, request: SendChatMessageRequest) -> SendChatMessageResponse:
        message = self._validate_message(request.message)

        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)

        session = self.chat_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        previous_messages = self.chat_repository.list_messages_by_session(session_id)
        history = previous_messages[-Settings.CHAT_HISTORY_MAX_MESSAGES:]

        rag = self.rag_context_service.build_context(message)
        sources = rag["sources"]

        tool_context = self._build_tool_context(request)
        tool_calls = tool_context["toolCalls"]

        self.chat_repository.create_message(
            session_id=session_id,
            role="user",
            content=message,
            metadata={
                "context": request.context,
                "rag": {
                    "sources": sources,
                },
                "toolCalls": tool_calls,
            },
        )

        llm_messages = self._build_llm_messages(
            history=history,
            current_message=message,
            rag_context=rag["context"],
            tool_context=tool_context["context"],
        )

        answer = self.llm_gateway.generate(llm_messages)

        assistant_message = self.chat_repository.create_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            metadata={
                "provider": Settings.LLM_PROVIDER,
                "model": Settings.OLLAMA_MODEL,
                "sources": sources,
                "toolCalls": tool_calls,
                "rag": {
                    "enabled": True,
                    "sourceCount": len(sources),
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
                "sources": sources,
                "rag_enabled": True,
                "tool_count": len(tool_calls),
            },
        )

        return SendChatMessageResponse(
            messageId=str(assistant_message.id),
            answer=answer,
            sources=sources,
            toolCalls=tool_calls,
        )

    def _build_tool_context(self, request: SendChatMessageRequest) -> dict:
        if not request.access_token:
            return {
                "context": "",
                "toolCalls": [],
            }

        return self.chat_tool_context_service.build_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
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

    def _build_llm_messages(
        self,
        history,
        current_message: str,
        rag_context: str,
        tool_context: str,
    ) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": self.prompt_policy_service.build_contextual_prompt(
                    rag_context=rag_context,
                    tool_context=tool_context,
                ),
            }
        ]

        for item in history:
            if item.role not in {"user", "assistant", "system"}:
                continue

            messages.append(
                {
                    "role": item.role,
                    "content": item.content,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": current_message,
            }
        )

        return messages

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
