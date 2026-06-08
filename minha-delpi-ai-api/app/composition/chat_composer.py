from app.composition.content_composer import (
    configure_domain_infrastructure_ports_with_persistence,
)
from app.application.use_cases.update_chat_message_use_case import UpdateChatMessageUseCase
from app.application.use_cases.delete_chat_session_use_case import DeleteChatSessionUseCase
from app.composition.external_action_composer import make_postgres_external_action_repository
from app.application.services.external_actions.external_action_semantic_ranker_service import (
    ExternalActionSemanticRankerService,
)
from app.application.services.external_actions.external_action_selection_service import ExternalActionSelectionService
from app.application.services.admin_guideline_prompt_service import AdminGuidelinePromptService
from app.application.services.chat_attachment_context_service import ChatAttachmentContextService
from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor
from app.application.services.chat_history_summary_service import ChatHistorySummaryService
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.services.chat_native_tool_calling_service import (
    ChatNativeToolCallingService,
)
from app.application.services.chat_tool_router_service import ChatToolRouterService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.rag_context_service import RagContextService
from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.chat_agents_use_cases import (
    CreateChatAgentUseCase,
    DeleteChatAgentActionProviderUseCase,
    DeleteChatAgentActionUseCase,
    DeleteChatAgentUseCase,
    ListChatAgentActionProvidersUseCase,
    ListChatAgentActionsUseCase,
    ListChatAgentsUseCase,
    UpsertChatAgentActionProviderUseCase,
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
from app.application.use_cases.index_chat_attachment_use_case import IndexChatAttachmentUseCase
from app.application.use_cases.ingest_knowledge_document_use_case import IngestKnowledgeDocumentUseCase
from app.composition.knowledge_pipeline_composer import (
    make_knowledge_ingestion_pipeline_service,
)
from app.application.use_cases.chat_sources_use_cases import (
    CreateAgentSourceUseCase,
    CreateProjectSourceUseCase,
    DeleteChatSourceUseCase,
    ListAgentSourcesUseCase,
    ListProjectSourcesUseCase,
)
from app.application.use_cases.chat_attachments_use_cases import (
    CreateChatAttachmentUseCase,
    DeleteChatAttachmentUseCase,
    ListChatAttachmentsUseCase,
)
from app.application.use_cases.download_chat_file_use_cases import (
    DownloadChatAttachmentUseCase,
    DownloadChatSourceUseCase,
)
from app.application.use_cases.chat_artifacts_use_cases import (
    CreateChatArtifactUseCase,
    DeleteChatArtifactUseCase,
    ListChatArtifactsUseCase,
    UpdateChatArtifactUseCase,
)
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.application.use_cases.switch_chat_branch_use_case import SwitchChatBranchUseCase
from app.application.use_cases.rename_chat_session_use_case import RenameChatSessionUseCase
from app.application.use_cases.set_chat_session_state_use_case import (
    SetChatSessionArchivedUseCase,
    SetChatSessionPinnedUseCase,
)
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.application.services.chat_session_memory_service import ChatSessionMemoryService
from app.application.use_cases.clear_chat_session_memory_use_case import (
    ClearChatSessionMemoryUseCase,
)
from app.application.use_cases.chat_session_memory_pins_use_case import (
    ChatSessionMemoryPinsUseCase,
)
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.infrastructure.persistence.postgres_chat_session_memory_repository import (
    PostgresChatSessionMemoryRepository,
)
from app.composition.tool_composer import make_execute_tool_use_case
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.domain.services.tool_selection_service import ToolSelectionService
from app.application.services.chat_agentic_tool_loop_service import ChatAgenticToolLoopService
from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.composition.external_action_composer import make_embedding_gateway
from app.composition.llm_composer import make_llm_gateway
from app.infrastructure.persistence.postgres_admin_guideline_repository import PostgresAdminGuidelineRepository
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


def make_switch_chat_branch_use_case() -> SwitchChatBranchUseCase:
    repository = PostgresChatSessionRepository()
    return SwitchChatBranchUseCase(
        repository=repository,
        history_use_case=GetChatHistoryUseCase(repository),
    )


def make_upsert_chat_message_feedback_use_case():
    from app.application.use_cases.upsert_chat_message_feedback_use_case import (
        UpsertChatMessageFeedbackUseCase,
    )

    return UpsertChatMessageFeedbackUseCase(PostgresChatSessionRepository())


def make_chat_intelligence_settings_service() -> ChatIntelligenceSettingsService:
    return ChatIntelligenceSettingsService()


def make_rag_context_service() -> RagContextService:
    return RagContextService(
        SearchKnowledgeUseCase(
            knowledge_repository=PostgresKnowledgeRepository(),
            embedding_gateway=make_embedding_gateway(),
        ),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
    )




def make_chat_workspace_context_service() -> ChatWorkspaceContextService:
    return ChatWorkspaceContextService(
        project_repository=PostgresChatProjectRepository(),
        agent_repository=PostgresChatAgentRepository(),
    )


def make_chat_attachment_context_service() -> ChatAttachmentContextService:
    return ChatAttachmentContextService(
        attachment_repository=PostgresChatAttachmentRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
        text_extractor=ChatAttachmentTextExtractor(),
    )


def make_chat_history_summary_service() -> ChatHistorySummaryService:
    return ChatHistorySummaryService(
        llm_gateway=make_llm_gateway(),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
    )


def make_chat_tool_router_service() -> ChatToolRouterService:
    return ChatToolRouterService(
        llm_gateway=make_llm_gateway(),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
    )


def make_external_action_semantic_ranker_service() -> ExternalActionSemanticRankerService:
    return ExternalActionSemanticRankerService(
        embedding_gateway=make_embedding_gateway(),
        external_action_repository=make_postgres_external_action_repository(),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
    )


def make_chat_agentic_tool_loop_service() -> ChatAgenticToolLoopService:
    return ChatAgenticToolLoopService(
        llm_gateway=make_llm_gateway(),
        execute_tool_use_case=make_execute_tool_use_case(),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
        external_action_repository=make_postgres_external_action_repository(),
    )


def make_chat_native_tool_calling_service() -> ChatNativeToolCallingService:
    return ChatNativeToolCallingService(
        llm_gateway=make_llm_gateway(),
        intelligence_settings_service=make_chat_intelligence_settings_service(),
    )


def make_chat_tool_context_service() -> ChatToolContextService:
    return ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=make_execute_tool_use_case(),
        external_action_selection_service=ExternalActionSelectionService(
            make_postgres_external_action_repository(),
            semantic_ranker=make_external_action_semantic_ranker_service(),
        ),
        tool_router_service=make_chat_tool_router_service(),
        external_action_repository=make_postgres_external_action_repository(),
        native_tool_calling_service=make_chat_native_tool_calling_service(),
    )


def make_admin_guideline_prompt_service() -> AdminGuidelinePromptService:
    return AdminGuidelinePromptService(PostgresAdminGuidelineRepository())


def make_chat_web_search_synthesis_service() -> ChatWebSearchSynthesisService:
    return ChatWebSearchSynthesisService(llm_gateway=make_llm_gateway())


def make_chat_session_memory_service() -> ChatSessionMemoryService:
    return ChatSessionMemoryService(PostgresChatSessionMemoryRepository())


def make_clear_chat_session_memory_use_case() -> ClearChatSessionMemoryUseCase:
    return ClearChatSessionMemoryUseCase(
        PostgresChatSessionRepository(),
        PostgresChatSessionMemoryRepository(),
    )


def make_chat_session_memory_pins_use_case() -> ChatSessionMemoryPinsUseCase:
    return ChatSessionMemoryPinsUseCase(
        PostgresChatSessionRepository(),
        PostgresChatSessionMemoryRepository(),
    )


def make_chat_turn_completion_service():
    from app.application.services.chat_turn.chat_turn_completion_service import (
        ChatTurnCompletionService,
    )

    return ChatTurnCompletionService(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        session_memory_service=make_chat_session_memory_service(),
    )


def make_send_chat_message_use_case() -> SendChatMessageUseCase:
    configure_domain_infrastructure_ports_with_persistence()

    return SendChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=make_llm_gateway(),
        prompt_policy_service=PromptPolicyService(),
        rag_context_service=make_rag_context_service(),
        chat_tool_context_service=make_chat_tool_context_service(),
        agent_repository=PostgresChatAgentRepository(),
        attachment_repository=PostgresChatAttachmentRepository(),
        chat_attachment_context_service=make_chat_attachment_context_service(),
        chat_history_summary_service=make_chat_history_summary_service(),
        chat_agentic_tool_loop_service=make_chat_agentic_tool_loop_service(),
        workspace_context_service=make_chat_workspace_context_service(),
        admin_guideline_prompt_service=make_admin_guideline_prompt_service(),
        web_search_synthesis_service=make_chat_web_search_synthesis_service(),
        session_memory_service=make_chat_session_memory_service(),
        turn_completion_service=make_chat_turn_completion_service(),
    )


def make_stream_chat_message_use_case() -> StreamChatMessageUseCase:
    configure_domain_infrastructure_ports_with_persistence()

    return StreamChatMessageUseCase(
        chat_repository=PostgresChatSessionRepository(),
        audit_repository=PostgresAuditRepository(),
        llm_gateway=make_llm_gateway(),
        prompt_policy_service=PromptPolicyService(),
        rag_context_service=make_rag_context_service(),
        chat_tool_context_service=make_chat_tool_context_service(),
        agent_repository=PostgresChatAgentRepository(),
        attachment_repository=PostgresChatAttachmentRepository(),
        chat_attachment_context_service=make_chat_attachment_context_service(),
        chat_history_summary_service=make_chat_history_summary_service(),
        chat_agentic_tool_loop_service=make_chat_agentic_tool_loop_service(),
        workspace_context_service=make_chat_workspace_context_service(),
        admin_guideline_prompt_service=make_admin_guideline_prompt_service(),
        web_search_synthesis_service=make_chat_web_search_synthesis_service(),
        session_memory_service=make_chat_session_memory_service(),
        turn_completion_service=make_chat_turn_completion_service(),
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


def make_get_chat_agent_use_case():
    from app.application.use_cases.chat_agents_use_cases import GetChatAgentUseCase

    return GetChatAgentUseCase(PostgresChatAgentRepository())


def make_list_chat_agent_shares_use_case():
    from app.application.services.chat_share_profile_service import ChatShareProfileService
    from app.application.use_cases.chat_agents_use_cases import ListChatAgentSharesUseCase
    from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

    return ListChatAgentSharesUseCase(
        PostgresChatAgentRepository(),
        ChatShareProfileService(CoreApiHttpGateway()),
    )


def make_revoke_chat_agent_share_use_case():
    from app.application.use_cases.chat_agents_use_cases import RevokeChatAgentShareUseCase

    return RevokeChatAgentShareUseCase(PostgresChatAgentRepository())


def make_preview_chat_agent_use_case():
    from app.application.use_cases.chat_agents_use_cases import PreviewChatAgentUseCase
    from app.composition.admin_composer import make_admin_agent_simulate_use_case

    return PreviewChatAgentUseCase(
        PostgresChatAgentRepository(),
        make_admin_agent_simulate_use_case(with_llm=True),
    )


def make_publish_chat_agent_use_case():
    from app.application.use_cases.chat_agents_use_cases import PublishChatAgentUseCase

    return PublishChatAgentUseCase(PostgresChatAgentRepository())


def make_list_chat_agent_versions_use_case():
    from app.application.use_cases.chat_agents_use_cases import ListChatAgentVersionsUseCase

    return ListChatAgentVersionsUseCase(PostgresChatAgentRepository())


def make_create_chat_agent_use_case() -> CreateChatAgentUseCase:
    return CreateChatAgentUseCase(PostgresChatAgentRepository())


def make_update_chat_agent_use_case() -> UpdateChatAgentUseCase:
    return UpdateChatAgentUseCase(PostgresChatAgentRepository())


def make_delete_chat_agent_use_case() -> DeleteChatAgentUseCase:
    return DeleteChatAgentUseCase(PostgresChatAgentRepository())


def make_duplicate_chat_agent_use_case():
    from app.application.services.agent_source_copy_service import AgentSourceCopyService
    from app.application.use_cases.chat_agents_use_cases import DuplicateChatAgentUseCase
    from app.infrastructure.persistence.postgres_knowledge_repository import (
        PostgresKnowledgeRepository,
    )

    return DuplicateChatAgentUseCase(
        PostgresChatAgentRepository(),
        AgentSourceCopyService(
            PostgresKnowledgeRepository(),
            make_ingest_knowledge_document_use_case(),
        ),
    )


def make_transfer_chat_agent_ownership_use_case():
    from app.application.use_cases.chat_agents_use_cases import (
        TransferChatAgentOwnershipUseCase,
    )

    return TransferChatAgentOwnershipUseCase(PostgresChatAgentRepository())


def make_export_chat_agent_use_case():
    from app.application.use_cases.chat_agents_use_cases import ExportChatAgentUseCase

    return ExportChatAgentUseCase(PostgresChatAgentRepository())


def make_import_chat_agent_use_case():
    from app.application.use_cases.chat_agents_use_cases import ImportChatAgentUseCase

    return ImportChatAgentUseCase(PostgresChatAgentRepository())


def make_get_chat_agent_stats_use_case():
    from app.application.use_cases.chat_agents_use_cases import GetChatAgentStatsUseCase

    return GetChatAgentStatsUseCase(PostgresChatAgentRepository())


def make_search_chat_directory_users_use_case():
    from app.application.use_cases.search_chat_directory_users_use_case import (
        SearchChatDirectoryUsersUseCase,
    )
    from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

    return SearchChatDirectoryUsersUseCase(CoreApiHttpGateway())


def make_share_chat_agent_use_case() -> ShareChatAgentUseCase:
    return ShareChatAgentUseCase(PostgresChatAgentRepository())






def make_list_chat_agent_action_providers_use_case() -> ListChatAgentActionProvidersUseCase:
    return ListChatAgentActionProvidersUseCase(PostgresChatAgentRepository())


def make_upsert_chat_agent_action_provider_use_case() -> UpsertChatAgentActionProviderUseCase:
    return UpsertChatAgentActionProviderUseCase(PostgresChatAgentRepository())


def make_list_chat_agent_actions_use_case() -> ListChatAgentActionsUseCase:
    return ListChatAgentActionsUseCase(PostgresChatAgentRepository())


def make_upsert_chat_agent_action_use_case() -> UpsertChatAgentActionUseCase:
    return UpsertChatAgentActionUseCase(PostgresChatAgentRepository())


def make_delete_chat_agent_action_provider_use_case() -> DeleteChatAgentActionProviderUseCase:
    return DeleteChatAgentActionProviderUseCase(PostgresChatAgentRepository())


def make_delete_chat_agent_action_use_case() -> DeleteChatAgentActionUseCase:
    return DeleteChatAgentActionUseCase(PostgresChatAgentRepository())


def make_list_chat_skill_catalog_use_case():
    from app.application.use_cases.chat_skills_use_cases import ListChatSkillCatalogUseCase

    return ListChatSkillCatalogUseCase()


def make_list_chat_agent_skills_use_case():
    from app.application.use_cases.chat_skills_use_cases import ListChatAgentSkillsUseCase

    return ListChatAgentSkillsUseCase(PostgresChatAgentRepository())


def make_upsert_chat_agent_skill_use_case():
    from app.application.use_cases.chat_skills_use_cases import UpsertChatAgentSkillUseCase

    return UpsertChatAgentSkillUseCase(PostgresChatAgentRepository())


def make_share_chat_project_use_case() -> ShareChatProjectUseCase:
    return ShareChatProjectUseCase(PostgresChatProjectRepository())


def make_list_chat_project_shares_use_case():
    from app.application.services.chat_share_profile_service import ChatShareProfileService
    from app.application.use_cases.chat_projects_use_cases import ListChatProjectSharesUseCase
    from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

    return ListChatProjectSharesUseCase(
        PostgresChatProjectRepository(),
        ChatShareProfileService(CoreApiHttpGateway()),
    )


def make_revoke_chat_project_share_use_case():
    from app.application.use_cases.chat_projects_use_cases import RevokeChatProjectShareUseCase

    return RevokeChatProjectShareUseCase(PostgresChatProjectRepository())




def make_ingest_knowledge_document_use_case() -> IngestKnowledgeDocumentUseCase:
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=make_embedding_gateway(),
        pipeline=make_knowledge_ingestion_pipeline_service(),
        audit_repository=PostgresAuditRepository(),
    )


def make_index_chat_attachment_use_case() -> IndexChatAttachmentUseCase:
    return IndexChatAttachmentUseCase(
        attachment_repository=PostgresChatAttachmentRepository(),
        ingest_knowledge_document_use_case=make_ingest_knowledge_document_use_case(),
        text_extractor=ChatAttachmentTextExtractor(),
    )


def make_create_chat_attachment_use_case() -> CreateChatAttachmentUseCase:
    return CreateChatAttachmentUseCase(
        attachment_repository=PostgresChatAttachmentRepository(),
        session_repository=PostgresChatSessionRepository(),
        index_attachment_use_case=make_index_chat_attachment_use_case(),
    )


def make_list_chat_attachments_use_case() -> ListChatAttachmentsUseCase:
    return ListChatAttachmentsUseCase(
        attachment_repository=PostgresChatAttachmentRepository(),
        session_repository=PostgresChatSessionRepository(),
    )


def make_delete_chat_attachment_use_case() -> DeleteChatAttachmentUseCase:
    return DeleteChatAttachmentUseCase(PostgresChatAttachmentRepository())


def make_create_project_source_use_case() -> CreateProjectSourceUseCase:
    return CreateProjectSourceUseCase(
        project_repository=PostgresChatProjectRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
        ingest_use_case=make_ingest_knowledge_document_use_case(),
        text_extractor=ChatAttachmentTextExtractor(),
    )


def make_list_project_sources_use_case() -> ListProjectSourcesUseCase:
    return ListProjectSourcesUseCase(
        project_repository=PostgresChatProjectRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
    )


def make_create_agent_source_use_case() -> CreateAgentSourceUseCase:
    return CreateAgentSourceUseCase(
        agent_repository=PostgresChatAgentRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
        ingest_use_case=make_ingest_knowledge_document_use_case(),
        text_extractor=ChatAttachmentTextExtractor(),
    )


def make_list_agent_sources_use_case() -> ListAgentSourcesUseCase:
    return ListAgentSourcesUseCase(
        agent_repository=PostgresChatAgentRepository(),
        knowledge_repository=PostgresKnowledgeRepository(),
    )


def make_delete_chat_source_use_case() -> DeleteChatSourceUseCase:
    return DeleteChatSourceUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        project_repository=PostgresChatProjectRepository(),
        agent_repository=PostgresChatAgentRepository(),
    )


def make_download_chat_attachment_use_case() -> DownloadChatAttachmentUseCase:
    return DownloadChatAttachmentUseCase(PostgresChatAttachmentRepository())


def make_download_chat_source_use_case() -> DownloadChatSourceUseCase:
    return DownloadChatSourceUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        access_checker=make_delete_chat_source_use_case(),
    )
