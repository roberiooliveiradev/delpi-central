from app.application.use_cases.update_chat_message_use_case import UpdateChatMessageUseCase
from app.application.use_cases.delete_chat_session_use_case import DeleteChatSessionUseCase
from app.infrastructure.persistence.postgres_external_action_repository import PostgresExternalActionRepository
from app.application.services.external_actions.external_action_selection_service import ExternalActionSelectionService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.rag_context_service import RagContextService
from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.chat_agents_use_cases import (
    CreateChatAgentUseCase,
    DeleteChatAgentUseCase,
    ListChatAgentsUseCase,
    ShareChatAgentUseCase,
    UpdateChatAgentUseCase,
    UpsertChatAgentActionUseCase,
)
from app.application.use_cases.chat_projects_use_cases import (
    CreateChatProjectUseCase,
    DeleteChatProjectUseCase,
    ListChatProjectsUseCase,
    ShareChatProjectUseCase,
    UpdateChatProjectUseCase,
)
from app.application.use_cases.chat_attachments_use_cases import (
    CreateChatAttachmentUseCase,
    DeleteChatAttachmentUseCase,
    ListChatAttachmentsUseCase,
)
from app.application.use_cases.chat_artifacts_use_cases import (
    CreateChatArtifactUseCase,
    DeleteChatArtifactUseCase,
    ListChatArtifactsUseCase,
    UpdateChatArtifactUseCase,
)
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.application.use_cases.rename_chat_session_use_case import RenameChatSessionUseCase
from app.application.use_cases.set_chat_session_state_use_case import (
    SetChatSessionArchivedUseCase,
    SetChatSessionPinnedUseCase,
)
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.composition.tool_composer import make_execute_tool_use_case
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.composition.llm_composer import make_llm_gateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_agent_repository import PostgresChatAgentRepository
from app.infrastructure.persistence.postgres_chat_project_repository import PostgresChatProjectRepository
from app.infrastructure.persistence.postgres_chat_artifact_repository import (
    PostgresChatArtifactRepository,
)
from app.infrastructure.persistence.postgres_chat_attachment_repository import (
    PostgresChatAttachmentRepository,
)
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_create_chat_session_use_case() -> CreateChatSessionUseCase:
    return CreateChatSessionUseCase(
        repository=PostgresChatSessionRepository(),
        project_repository=PostgresChatProjectRepository(),
        agent_repository=PostgresChatAgentRepository(),
    )


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




def make_chat_workspace_context_service() -> ChatWorkspaceContextService:
    return ChatWorkspaceContextService(
        project_repository=PostgresChatProjectRepository(),
        agent_repository=PostgresChatAgentRepository(),
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
        agent_repository=PostgresChatAgentRepository(),
        attachment_repository=PostgresChatAttachmentRepository(),
        workspace_context_service=make_chat_workspace_context_service(),
    )


def make_stream_chat_message_use_case() -> StreamChatMessageUseCase:
    return StreamChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=make_llm_gateway(),
        prompt_policy_service=PromptPolicyService(),
        rag_context_service=make_rag_context_service(),
        chat_tool_context_service=make_chat_tool_context_service(),
        agent_repository=PostgresChatAgentRepository(),
        attachment_repository=PostgresChatAttachmentRepository(),
        workspace_context_service=make_chat_workspace_context_service(),
    )

def make_rename_chat_session_use_case() -> RenameChatSessionUseCase:
    return RenameChatSessionUseCase(PostgresChatSessionRepository())

def make_delete_chat_session_use_case() -> DeleteChatSessionUseCase:
    return DeleteChatSessionUseCase(PostgresChatSessionRepository())


def make_update_chat_message_use_case() -> UpdateChatMessageUseCase:
    return UpdateChatMessageUseCase(PostgresChatSessionRepository())



def make_set_chat_session_pinned_use_case() -> SetChatSessionPinnedUseCase:
    return SetChatSessionPinnedUseCase(PostgresChatSessionRepository())


def make_set_chat_session_archived_use_case() -> SetChatSessionArchivedUseCase:
    return SetChatSessionArchivedUseCase(PostgresChatSessionRepository())


def make_list_chat_artifacts_use_case() -> ListChatArtifactsUseCase:
    return ListChatArtifactsUseCase(
        artifact_repository=PostgresChatArtifactRepository(),
        session_repository=PostgresChatSessionRepository(),
    )


def make_create_chat_artifact_use_case() -> CreateChatArtifactUseCase:
    return CreateChatArtifactUseCase(
        artifact_repository=PostgresChatArtifactRepository(),
        session_repository=PostgresChatSessionRepository(),
    )


def make_update_chat_artifact_use_case() -> UpdateChatArtifactUseCase:
    return UpdateChatArtifactUseCase(PostgresChatArtifactRepository())


def make_delete_chat_artifact_use_case() -> DeleteChatArtifactUseCase:
    return DeleteChatArtifactUseCase(PostgresChatArtifactRepository())


def make_list_chat_projects_use_case() -> ListChatProjectsUseCase:
    return ListChatProjectsUseCase(PostgresChatProjectRepository())


def make_create_chat_project_use_case() -> CreateChatProjectUseCase:
    return CreateChatProjectUseCase(PostgresChatProjectRepository())


def make_update_chat_project_use_case() -> UpdateChatProjectUseCase:
    return UpdateChatProjectUseCase(PostgresChatProjectRepository())


def make_delete_chat_project_use_case() -> DeleteChatProjectUseCase:
    return DeleteChatProjectUseCase(PostgresChatProjectRepository())


def make_list_chat_agents_use_case() -> ListChatAgentsUseCase:
    return ListChatAgentsUseCase(PostgresChatAgentRepository())


def make_create_chat_agent_use_case() -> CreateChatAgentUseCase:
    return CreateChatAgentUseCase(PostgresChatAgentRepository())


def make_update_chat_agent_use_case() -> UpdateChatAgentUseCase:
    return UpdateChatAgentUseCase(PostgresChatAgentRepository())


def make_delete_chat_agent_use_case() -> DeleteChatAgentUseCase:
    return DeleteChatAgentUseCase(PostgresChatAgentRepository())


def make_share_chat_agent_use_case() -> ShareChatAgentUseCase:
    return ShareChatAgentUseCase(PostgresChatAgentRepository())


def make_upsert_chat_agent_action_use_case() -> UpsertChatAgentActionUseCase:
    return UpsertChatAgentActionUseCase(PostgresChatAgentRepository())


def make_share_chat_project_use_case() -> ShareChatProjectUseCase:
    return ShareChatProjectUseCase(PostgresChatProjectRepository())


def make_create_chat_attachment_use_case() -> CreateChatAttachmentUseCase:
    return CreateChatAttachmentUseCase(
        attachment_repository=PostgresChatAttachmentRepository(),
        workspace_context_service=make_chat_workspace_context_service(),
        session_repository=PostgresChatSessionRepository(),
    )


def make_list_chat_attachments_use_case() -> ListChatAttachmentsUseCase:
    return ListChatAttachmentsUseCase(
        attachment_repository=PostgresChatAttachmentRepository(),
        workspace_context_service=make_chat_workspace_context_service(),
        session_repository=PostgresChatSessionRepository(),
    )


def make_delete_chat_attachment_use_case() -> DeleteChatAttachmentUseCase:
    return DeleteChatAttachmentUseCase(PostgresChatAttachmentRepository())
