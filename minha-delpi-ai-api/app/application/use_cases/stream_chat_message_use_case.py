import hashlib
from collections.abc import Iterator
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
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


class StreamChatMessageUseCase:
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

    def stream(self, request: SendChatMessageRequest) -> Iterator[dict]:
        message = self._validate_message(request.message)

        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)

        session = self.chat_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        previous_messages = self.chat_repository.list_messages_by_session(session_id)

        if self._should_generate_session_title(session, previous_messages):
            self._generate_and_apply_session_title(
                session_id=session_id,
                user_id=user_id,
                message=message,
            )

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
                "stream": True,
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

        answer_parts: list[str] = []

        yield {
            "type": "sources",
            "sources": sources,
        }

        yield {
            "type": "tool_calls",
            "toolCalls": tool_calls,
        }

        for token in self.llm_gateway.stream(llm_messages):
            answer_parts.append(token)
            yield {
                "type": "token",
                "content": token,
            }

        answer = "".join(answer_parts).strip()

        assistant_message = self.chat_repository.create_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            metadata={
                "provider": Settings.LLM_PROVIDER,
                "model": Settings.OLLAMA_MODEL,
                "sources": sources,
                "toolCalls": tool_calls,
                "stream": True,
                "rag": {
                    "enabled": True,
                    "sourceCount": len(sources),
                },
            },
        )

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
                "sources": sources,
                "rag_enabled": True,
                "tool_count": len(tool_calls),
            },
        )

        yield {
            "type": "done",
            "messageId": str(assistant_message.id),
            "answer": answer,
            "sources": sources,
            "toolCalls": tool_calls,
        }

    def _should_generate_session_title(self, session, previous_messages) -> bool:
        if previous_messages:
            return False

        title = (session.title or "").strip().lower()

        return title in {"", "nova conversa", "novo chat", "conversa sem título"}

    def _generate_and_apply_session_title(
        self,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        fallback_title = self._fallback_title_from_message(message)

        try:
            generated_title = self.llm_gateway.generate(
                [
                    {
                        "role": "system",
                        "content": (
                            "Você cria títulos curtos para conversas corporativas. "
                            "Responda apenas com o título, em português, sem aspas, "
                            "sem ponto final, com no máximo 6 palavras."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Crie um título curto para esta conversa:\n\n"
                            f"{message}"
                        ),
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
            return "Nova conversa"

        if len(normalized) <= 48:
            return normalized

        return normalized[:48].rstrip() + "..."

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
