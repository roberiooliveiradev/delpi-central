from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)


def make_create_chat_session_use_case() -> CreateChatSessionUseCase:
    return CreateChatSessionUseCase(PostgresChatSessionRepository())


def make_list_chat_sessions_use_case() -> ListChatSessionsUseCase:
    return ListChatSessionsUseCase(PostgresChatSessionRepository())


def make_get_chat_history_use_case() -> GetChatHistoryUseCase:
    return GetChatHistoryUseCase(PostgresChatSessionRepository())


def make_send_chat_message_use_case() -> SendChatMessageUseCase:
    return SendChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=OllamaLlmGateway(),
        prompt_policy_service=PromptPolicyService(),
    )
