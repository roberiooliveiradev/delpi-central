from app.application.use_cases.update_chat_message_use_case import UpdateChatMessageUseCase
from app.application.use_cases.delete_chat_session_use_case import DeleteChatSessionUseCase
from app.infrastructure.persistence.postgres_external_action_repository import PostgresExternalActionRepository
from app.application.services.external_actions.external_action_selection_service import ExternalActionSelectionService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.rag_context_service import RagContextService
from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.application.use_cases.rename_chat_session_use_case import RenameChatSessionUseCase
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.composition.tool_composer import make_execute_tool_use_case
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.composition.llm_composer import make_llm_gateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_create_chat_session_use_case() -> CreateChatSessionUseCase:
    return CreateChatSessionUseCase(PostgresChatSessionRepository())


def make_list_chat_sessions_use_case() -> ListChatSessionsUseCase:
    return ListChatSessionsUseCase(PostgresChatSessionRepository())


def make_get_chat_history_use_case() -> GetChatHistoryUseCase:
    return GetChatHistoryUseCase(PostgresChatSessionRepository())


def make_rag_context_service() -> RagContextService:
    return RagContextService(
        SearchKnowledgeUseCase(
            knowledge_repository=PostgresKnowledgeRepository(),
            embedding_gateway=LocalEmbeddingGateway(),
        )
    )


def make_chat_tool_context_service() -> ChatToolContextService:
    return ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=make_execute_tool_use_case(),
        external_action_selection_service=ExternalActionSelectionService(
            PostgresExternalActionRepository()
        ),
    )


def make_send_chat_message_use_case() -> SendChatMessageUseCase:
    return SendChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=make_llm_gateway(),
        prompt_policy_service=PromptPolicyService(),
        rag_context_service=make_rag_context_service(),
        chat_tool_context_service=make_chat_tool_context_service(),
    )


def make_stream_chat_message_use_case() -> StreamChatMessageUseCase:
    return StreamChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=make_llm_gateway(),
        prompt_policy_service=PromptPolicyService(),
        rag_context_service=make_rag_context_service(),
        chat_tool_context_service=make_chat_tool_context_service(),
    )

def make_rename_chat_session_use_case() -> RenameChatSessionUseCase:
    return RenameChatSessionUseCase(PostgresChatSessionRepository())

def make_delete_chat_session_use_case() -> DeleteChatSessionUseCase:
    return DeleteChatSessionUseCase(PostgresChatSessionRepository())


def make_update_chat_message_use_case() -> UpdateChatMessageUseCase:
    return UpdateChatMessageUseCase(PostgresChatSessionRepository())

