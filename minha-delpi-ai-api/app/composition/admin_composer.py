from app.application.use_cases.archive_admin_guideline_use_case import ArchiveAdminGuidelineUseCase
from app.application.use_cases.compare_admin_guideline_versions_use_case import CompareAdminGuidelineVersionsUseCase
from app.application.use_cases.list_admin_guidelines_use_case import ListAdminGuidelinesUseCase
from app.application.use_cases.list_admin_guideline_versions_use_case import ListAdminGuidelineVersionsUseCase
from app.application.use_cases.publish_admin_guideline_use_case import PublishAdminGuidelineUseCase
from app.application.use_cases.save_admin_guideline_use_case import SaveAdminGuidelineUseCase
from app.infrastructure.persistence.postgres_admin_guideline_repository import PostgresAdminGuidelineRepository
from app.domain.services.external_actions.external_provider_url_policy import ExternalProviderUrlPolicy
from app.application.use_cases.list_external_actions_use_case import ListExternalActionsUseCase
from app.application.use_cases.list_external_action_providers_use_case import ListExternalActionProvidersUseCase
from app.application.use_cases.import_external_actions_schema_use_case import ImportExternalActionsSchemaUseCase
from app.application.use_cases.ingest_knowledge_document_use_case import IngestKnowledgeDocumentUseCase
from app.application.use_cases.create_external_action_provider_use_case import CreateExternalActionProviderUseCase
from app.application.use_cases.deactivate_knowledge_document_use_case import (
    DeactivateKnowledgeDocumentUseCase,
)
from app.application.use_cases.delete_knowledge_document_use_case import (
    DeleteKnowledgeDocumentUseCase,
)
from app.application.use_cases.get_admin_drawing_analysis_summary_use_case import (
    GetAdminDrawingAnalysisSummaryUseCase,
)
from app.application.use_cases.get_admin_intent_routing_summary_use_case import (
    GetAdminIntentRoutingSummaryUseCase,
)
from app.application.use_cases.get_admin_error_handling_summary_use_case import (
    GetAdminErrorHandlingSummaryUseCase,
)
from app.application.use_cases.get_admin_web_search_summary_use_case import (
    GetAdminWebSearchSummaryUseCase,
)
from app.application.use_cases.get_admin_interactivity_summary_use_case import (
    GetAdminInteractivitySummaryUseCase,
)
from app.application.use_cases.get_admin_presentation_summary_use_case import (
    GetAdminPresentationSummaryUseCase,
)
from app.application.use_cases.get_admin_session_memory_summary_use_case import (
    GetAdminSessionMemorySummaryUseCase,
)
from app.application.use_cases.get_admin_text_task_summary_use_case import (
    GetAdminTextTaskSummaryUseCase,
)
from app.application.use_cases.get_admin_document_vision_summary_use_case import (
    GetAdminDocumentVisionSummaryUseCase,
)
from app.application.use_cases.get_admin_sql_advanced_summary_use_case import (
    GetAdminSqlAdvancedSummaryUseCase,
)
from app.application.use_cases.get_admin_metrics_summary_use_case import GetAdminMetricsSummaryUseCase
from app.application.use_cases.get_admin_tools_health_use_case import GetAdminToolsHealthUseCase
from app.application.use_cases.admin_llm_cost_table_use_cases import (
    GetAdminLlmCostTableUseCase,
    SaveAdminLlmCostTableUseCase,
)
from app.application.services.knowledge_semantic_deduplicator_service import (
    KnowledgeSemanticDeduplicatorService,
)
from app.application.services.response_evaluation_llm_suggestion_service import (
    ResponseEvaluationLlmSuggestionService,
)
from app.application.use_cases.get_admin_rbac_summary_use_case import GetAdminRbacSummaryUseCase
from app.application.use_cases.get_admin_rbac_profiles_use_case import GetAdminRbacProfilesUseCase
from app.application.use_cases.get_admin_system_check_use_case import GetAdminSystemCheckUseCase
from app.application.use_cases.get_llm_provider_status_use_case import (
    GetLlmProviderStatusUseCase,
)
from app.application.use_cases.list_admin_audit_logs_use_case import (
    ListAdminAuditLogsUseCase,
)
from app.application.use_cases.list_admin_knowledge_documents_use_case import (
    ListAdminKnowledgeDocumentsUseCase,
)
from app.application.use_cases.update_admin_knowledge_document_metadata_use_case import (
    UpdateAdminKnowledgeDocumentMetadataUseCase,
)
from app.application.use_cases.reactivate_knowledge_document_use_case import (
    ReactivateKnowledgeDocumentUseCase,
)
from app.application.use_cases.restore_admin_guideline_version_use_case import RestoreAdminGuidelineVersionUseCase
from app.application.use_cases.reindex_knowledge_document_use_case import (
    ReindexKnowledgeDocumentUseCase,
)
from app.application.use_cases.admin_agent_simulate_use_case import AdminAgentSimulateUseCase
from app.application.use_cases.admin_rag_test_use_case import AdminRagTestUseCase
from app.application.use_cases.admin_agent_specialization_use_cases import (
    GetAdminAgentSpecializationUseCase,
    ListAdminAgentSpecializationPresetsUseCase,
    ListAdminSpecializedAgentsUseCase,
    SaveAdminAgentSpecializationUseCase,
)
from app.application.use_cases.admin_security_use_cases import (
    GetAdminSecurityConfigUseCase,
    GetAdminSecuritySummaryUseCase,
    ListAdminSecurityEventsUseCase,
    ScanAdminSecurityInputUseCase,
)
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.use_cases.admin_response_evaluation_use_cases import (
    GetAdminResponseEvaluationContextUseCase,
    GetAdminResponseEvaluationSummaryUseCase,
    ListAdminResponseCandidatesUseCase,
    ListAdminResponseEvaluationsUseCase,
    SaveAdminResponseEvaluationUseCase,
)
from app.application.use_cases.admin_chat_intelligence_use_cases import (
    GetAdminChatIntelligenceSettingsUseCase,
    ReindexExternalActionEmbeddingsUseCase,
    SaveAdminChatIntelligenceSettingsUseCase,
)
from app.composition.chat_composer import (
    make_admin_guideline_prompt_service,
    make_chat_tool_context_service,
    make_rag_context_service,
)
from app.composition.external_action_composer import make_postgres_external_action_repository
from app.composition.llm_composer import make_llm_gateway
from app.domain.services.tool_selection_service import ToolSelectionService
from app.application.use_cases.preview_knowledge_ingestion_use_case import (
    PreviewKnowledgeIngestionUseCase,
)
from app.composition.knowledge_pipeline_composer import (
    make_knowledge_ingestion_pipeline_service,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_admin_metrics_repository import PostgresAdminMetricsRepository
from app.infrastructure.persistence.postgres_admin_system_check_repository import PostgresAdminSystemCheckRepository
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_response_evaluation_repository import (
    PostgresResponseEvaluationRepository,
)
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_get_llm_provider_status_use_case() -> GetLlmProviderStatusUseCase:
    return GetLlmProviderStatusUseCase()


def make_list_admin_knowledge_documents_use_case() -> ListAdminKnowledgeDocumentsUseCase:
    return ListAdminKnowledgeDocumentsUseCase(PostgresKnowledgeRepository())


def make_update_admin_knowledge_document_metadata_use_case() -> (
    UpdateAdminKnowledgeDocumentMetadataUseCase
):
    return UpdateAdminKnowledgeDocumentMetadataUseCase(PostgresKnowledgeRepository())


def make_deactivate_knowledge_document_use_case() -> DeactivateKnowledgeDocumentUseCase:
    return DeactivateKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_reactivate_knowledge_document_use_case() -> ReactivateKnowledgeDocumentUseCase:
    return ReactivateKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_reindex_knowledge_document_use_case() -> ReindexKnowledgeDocumentUseCase:
    return ReindexKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        pipeline=make_knowledge_ingestion_pipeline_service(),
        audit_repository=PostgresAuditRepository(),
    )


def make_ingest_admin_knowledge_document_use_case() -> IngestKnowledgeDocumentUseCase:
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        pipeline=make_knowledge_ingestion_pipeline_service(),
        audit_repository=PostgresAuditRepository(),
    )


def make_preview_knowledge_ingestion_use_case() -> PreviewKnowledgeIngestionUseCase:
    return PreviewKnowledgeIngestionUseCase(
        pipeline=make_knowledge_ingestion_pipeline_service(),
        semantic_deduplicator=KnowledgeSemanticDeduplicatorService(
            embedding_gateway=LocalEmbeddingGateway(),
            knowledge_repository=PostgresKnowledgeRepository(),
        ),
    )


def make_delete_knowledge_document_use_case() -> DeleteKnowledgeDocumentUseCase:
    return DeleteKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_list_admin_audit_logs_use_case() -> ListAdminAuditLogsUseCase:
    return ListAdminAuditLogsUseCase(PostgresAuditRepository())

def make_get_admin_metrics_summary_use_case() -> GetAdminMetricsSummaryUseCase:
    return GetAdminMetricsSummaryUseCase(PostgresAdminMetricsRepository())


def make_get_admin_drawing_analysis_summary_use_case() -> GetAdminDrawingAnalysisSummaryUseCase:
    return GetAdminDrawingAnalysisSummaryUseCase(PostgresAuditRepository())


def make_get_admin_intent_routing_summary_use_case() -> GetAdminIntentRoutingSummaryUseCase:
    return GetAdminIntentRoutingSummaryUseCase(PostgresAuditRepository())


def make_get_admin_interactivity_summary_use_case() -> GetAdminInteractivitySummaryUseCase:
    return GetAdminInteractivitySummaryUseCase(PostgresAuditRepository())


def make_get_admin_presentation_summary_use_case() -> GetAdminPresentationSummaryUseCase:
    return GetAdminPresentationSummaryUseCase(PostgresAuditRepository())


def make_get_admin_error_handling_summary_use_case() -> GetAdminErrorHandlingSummaryUseCase:
    return GetAdminErrorHandlingSummaryUseCase(PostgresAuditRepository())


def make_get_admin_web_search_summary_use_case() -> GetAdminWebSearchSummaryUseCase:
    return GetAdminWebSearchSummaryUseCase(PostgresAuditRepository())


def make_get_admin_feedback_summary_use_case():
    from app.application.use_cases.get_admin_feedback_summary_use_case import (
        GetAdminFeedbackSummaryUseCase,
    )
    from app.composition.repository_composer import make_chat_message_feedback_repository

    return GetAdminFeedbackSummaryUseCase(
        feedback_repository=make_chat_message_feedback_repository(),
    )


def make_get_admin_quality_unified_summary_use_case():
    from app.application.use_cases.get_admin_quality_unified_summary_use_case import (
        GetAdminQualityUnifiedSummaryUseCase,
    )

    return GetAdminQualityUnifiedSummaryUseCase()


def make_generate_weekly_quality_report_use_case():
    from app.application.use_cases.generate_weekly_quality_report_use_case import (
        GenerateWeeklyQualityReportUseCase,
    )
    from app.composition.repository_composer import make_chat_quality_report_repository

    return GenerateWeeklyQualityReportUseCase(
        report_repository=make_chat_quality_report_repository(),
    )


def make_list_admin_quality_issues_use_case():
    from app.application.use_cases.chat_quality_issues_use_cases import (
        ListAdminQualityIssuesUseCase,
    )
    from app.composition.repository_composer import make_chat_quality_issue_repository

    return ListAdminQualityIssuesUseCase(
        issue_repository=make_chat_quality_issue_repository(),
    )


def make_update_admin_quality_issue_status_use_case():
    from app.application.use_cases.chat_quality_issues_use_cases import (
        UpdateAdminQualityIssueStatusUseCase,
    )
    from app.composition.repository_composer import make_chat_quality_issue_repository

    return UpdateAdminQualityIssueStatusUseCase(
        issue_repository=make_chat_quality_issue_repository(),
    )


def make_list_learning_candidates_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ListLearningCandidatesUseCase,
    )

    return ListLearningCandidatesUseCase()


def make_review_learning_candidate_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ReviewLearningCandidateUseCase,
    )

    return ReviewLearningCandidateUseCase()


def make_list_vocabulary_terms_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ListVocabularyTermsUseCase,
    )

    return ListVocabularyTermsUseCase()


def make_upsert_vocabulary_term_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        UpsertVocabularyTermUseCase,
    )

    return UpsertVocabularyTermUseCase()


def make_reindex_glossary_knowledge_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ReindexGlossaryKnowledgeUseCase,
    )

    return ReindexGlossaryKnowledgeUseCase()


def make_reindex_user_memory_knowledge_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ReindexUserMemoryKnowledgeUseCase,
    )

    return ReindexUserMemoryKnowledgeUseCase()


def make_get_admin_learning_summary_use_case():
    from app.application.use_cases.get_admin_learning_summary_use_case import (
        GetAdminLearningSummaryUseCase,
    )

    return GetAdminLearningSummaryUseCase()


def make_list_evaluation_cases_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ListEvaluationCasesUseCase,
    )

    return ListEvaluationCasesUseCase()


def make_create_evaluation_case_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        CreateEvaluationCaseUseCase,
    )

    return CreateEvaluationCaseUseCase()


def make_run_evaluation_case_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        RunEvaluationCaseUseCase,
    )

    return RunEvaluationCaseUseCase()


def make_review_evaluation_case_use_case():
    from app.application.use_cases.chat_learning_use_cases import (
        ReviewEvaluationCaseUseCase,
    )

    return ReviewEvaluationCaseUseCase()


def make_list_fine_tuning_samples_use_case():
    from app.application.use_cases.chat_learning_use_cases import ListFineTuningSamplesUseCase

    return ListFineTuningSamplesUseCase()


def make_create_fine_tuning_sample_use_case():
    from app.application.use_cases.chat_learning_use_cases import CreateFineTuningSampleUseCase

    return CreateFineTuningSampleUseCase()


def make_review_fine_tuning_sample_use_case():
    from app.application.use_cases.chat_learning_use_cases import ReviewFineTuningSampleUseCase

    return ReviewFineTuningSampleUseCase()


def make_list_fine_tuning_datasets_use_case():
    from app.application.use_cases.chat_learning_use_cases import ListFineTuningDatasetsUseCase

    return ListFineTuningDatasetsUseCase()


def make_create_fine_tuning_dataset_use_case():
    from app.application.use_cases.chat_learning_use_cases import CreateFineTuningDatasetUseCase

    return CreateFineTuningDatasetUseCase()


def make_approve_fine_tuning_dataset_use_case():
    from app.application.use_cases.chat_learning_use_cases import ApproveFineTuningDatasetUseCase

    return ApproveFineTuningDatasetUseCase()


def make_export_fine_tuning_dataset_use_case():
    from app.application.use_cases.chat_learning_use_cases import ExportFineTuningDatasetUseCase

    return ExportFineTuningDatasetUseCase()


def make_fine_tuning_run_use_case():
    from app.application.use_cases.chat_learning_use_cases import FineTuningRunUseCase

    return FineTuningRunUseCase()


def make_list_user_memory_items_use_case():
    from app.application.use_cases.chat_user_memory_use_cases import (
        ListUserMemoryItemsUseCase,
    )

    return ListUserMemoryItemsUseCase()


def make_review_user_memory_item_use_case():
    from app.application.use_cases.chat_user_memory_use_cases import (
        ReviewUserMemoryItemUseCase,
    )

    return ReviewUserMemoryItemUseCase()


def make_get_admin_text_task_summary_use_case() -> GetAdminTextTaskSummaryUseCase:
    from app.composition.repository_composer import (
        make_audit_repository,
        make_chat_message_feedback_repository,
    )

    return GetAdminTextTaskSummaryUseCase(
        make_audit_repository(),
        feedback_repository=make_chat_message_feedback_repository(),
    )


def make_get_admin_session_memory_summary_use_case() -> GetAdminSessionMemorySummaryUseCase:
    from app.composition.repository_composer import (
        make_audit_repository,
        make_chat_message_feedback_repository,
    )

    return GetAdminSessionMemorySummaryUseCase(
        make_audit_repository(),
        feedback_repository=make_chat_message_feedback_repository(),
    )


def make_get_admin_document_vision_summary_use_case() -> GetAdminDocumentVisionSummaryUseCase:
    return GetAdminDocumentVisionSummaryUseCase(PostgresAuditRepository())


def make_get_admin_sql_advanced_summary_use_case() -> GetAdminSqlAdvancedSummaryUseCase:
    return GetAdminSqlAdvancedSummaryUseCase(PostgresAuditRepository())


def make_get_admin_system_check_use_case() -> GetAdminSystemCheckUseCase:
    return GetAdminSystemCheckUseCase(PostgresAdminSystemCheckRepository())


def make_get_admin_tools_health_use_case() -> GetAdminToolsHealthUseCase:
    return GetAdminToolsHealthUseCase(
        system_check_repository=PostgresAdminSystemCheckRepository(),
        external_action_repository=make_postgres_external_action_repository(),
    )


def make_get_admin_chat_intelligence_settings_use_case() -> GetAdminChatIntelligenceSettingsUseCase:
    return GetAdminChatIntelligenceSettingsUseCase()


def make_save_admin_chat_intelligence_settings_use_case() -> SaveAdminChatIntelligenceSettingsUseCase:
    return SaveAdminChatIntelligenceSettingsUseCase()


def make_reindex_external_action_embeddings_use_case() -> ReindexExternalActionEmbeddingsUseCase:
    return ReindexExternalActionEmbeddingsUseCase()


def make_get_admin_llm_cost_table_use_case() -> GetAdminLlmCostTableUseCase:
    return GetAdminLlmCostTableUseCase()


def make_save_admin_llm_cost_table_use_case() -> SaveAdminLlmCostTableUseCase:
    return SaveAdminLlmCostTableUseCase()

def make_create_external_action_provider_use_case() -> CreateExternalActionProviderUseCase:
    return CreateExternalActionProviderUseCase(
        repository=make_postgres_external_action_repository(),
        url_policy=ExternalProviderUrlPolicy(),
    )


def make_list_external_action_providers_use_case() -> ListExternalActionProvidersUseCase:
    return ListExternalActionProvidersUseCase(make_postgres_external_action_repository())


def make_import_external_actions_schema_use_case() -> ImportExternalActionsSchemaUseCase:
    return ImportExternalActionsSchemaUseCase(make_postgres_external_action_repository())


def make_list_external_actions_use_case() -> ListExternalActionsUseCase:
    return ListExternalActionsUseCase(make_postgres_external_action_repository())



def make_test_admin_rag_use_case() -> AdminRagTestUseCase:
    return AdminRagTestUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        guideline_repository=PostgresAdminGuidelineRepository(),
    )


def make_admin_agent_simulate_use_case(*, with_llm: bool = False) -> AdminAgentSimulateUseCase:
    return AdminAgentSimulateUseCase(
        rag_context_service=make_rag_context_service(),
        guideline_prompt_service=make_admin_guideline_prompt_service(),
        tool_selection_service=ToolSelectionService(),
        chat_tool_context_service=make_chat_tool_context_service(),
        llm_gateway=make_llm_gateway() if with_llm else None,
    )


def make_list_admin_guidelines_use_case() -> ListAdminGuidelinesUseCase:
    return ListAdminGuidelinesUseCase(PostgresAdminGuidelineRepository())


def make_save_admin_guideline_use_case() -> SaveAdminGuidelineUseCase:
    return SaveAdminGuidelineUseCase(
        repository=PostgresAdminGuidelineRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_publish_admin_guideline_use_case() -> PublishAdminGuidelineUseCase:
    return PublishAdminGuidelineUseCase(
        repository=PostgresAdminGuidelineRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_archive_admin_guideline_use_case() -> ArchiveAdminGuidelineUseCase:
    return ArchiveAdminGuidelineUseCase(
        repository=PostgresAdminGuidelineRepository(),
        audit_repository=PostgresAuditRepository(),
    )



def make_list_admin_guideline_versions_use_case() -> ListAdminGuidelineVersionsUseCase:
    return ListAdminGuidelineVersionsUseCase(PostgresAdminGuidelineRepository())



def make_compare_admin_guideline_versions_use_case() -> CompareAdminGuidelineVersionsUseCase:
    return CompareAdminGuidelineVersionsUseCase(PostgresAdminGuidelineRepository())


def make_restore_admin_guideline_version_use_case() -> RestoreAdminGuidelineVersionUseCase:
    return RestoreAdminGuidelineVersionUseCase(
        repository=PostgresAdminGuidelineRepository(),
        audit_repository=PostgresAuditRepository(),
    )



def make_get_admin_rbac_summary_use_case() -> GetAdminRbacSummaryUseCase:
    return GetAdminRbacSummaryUseCase()


def make_get_admin_rbac_profiles_use_case() -> GetAdminRbacProfilesUseCase:
    return GetAdminRbacProfilesUseCase()


def _response_evaluation_repository() -> PostgresResponseEvaluationRepository:
    return PostgresResponseEvaluationRepository()


def make_list_admin_response_candidates_use_case() -> ListAdminResponseCandidatesUseCase:
    return ListAdminResponseCandidatesUseCase(_response_evaluation_repository())


def make_get_admin_response_evaluation_context_use_case() -> (
    GetAdminResponseEvaluationContextUseCase
):
    return GetAdminResponseEvaluationContextUseCase(
        _response_evaluation_repository(),
        llm_suggestion_service=ResponseEvaluationLlmSuggestionService(
            llm_gateway=make_llm_gateway(),
        ),
    )


def make_save_admin_response_evaluation_use_case() -> SaveAdminResponseEvaluationUseCase:
    return SaveAdminResponseEvaluationUseCase(
        _response_evaluation_repository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_list_admin_response_evaluations_use_case() -> ListAdminResponseEvaluationsUseCase:
    return ListAdminResponseEvaluationsUseCase(_response_evaluation_repository())


def make_get_admin_response_evaluation_summary_use_case() -> (
    GetAdminResponseEvaluationSummaryUseCase
):
    return GetAdminResponseEvaluationSummaryUseCase(_response_evaluation_repository())


def make_list_admin_agent_specialization_presets_use_case() -> (
    ListAdminAgentSpecializationPresetsUseCase
):
    return ListAdminAgentSpecializationPresetsUseCase()


def make_list_admin_specialized_agents_use_case() -> ListAdminSpecializedAgentsUseCase:
    return ListAdminSpecializedAgentsUseCase()


def make_get_admin_agent_specialization_use_case() -> GetAdminAgentSpecializationUseCase:
    return GetAdminAgentSpecializationUseCase()


def make_save_admin_agent_specialization_use_case() -> SaveAdminAgentSpecializationUseCase:
    return SaveAdminAgentSpecializationUseCase(audit_repository=PostgresAuditRepository())


def make_get_admin_security_config_use_case() -> GetAdminSecurityConfigUseCase:
    return GetAdminSecurityConfigUseCase()


def make_get_admin_security_summary_use_case() -> GetAdminSecuritySummaryUseCase:
    return GetAdminSecuritySummaryUseCase(audit_repository=PostgresAuditRepository())


def make_list_admin_security_events_use_case() -> ListAdminSecurityEventsUseCase:
    return ListAdminSecurityEventsUseCase(audit_repository=PostgresAuditRepository())


def make_scan_admin_security_input_use_case() -> ScanAdminSecurityInputUseCase:
    return ScanAdminSecurityInputUseCase(
        message_security_service=ChatMessageSecurityService(),
        audit_repository=PostgresAuditRepository(),
    )


def make_list_admin_chat_skills_use_case():
    from app.application.use_cases.admin_chat_skill_use_cases import ListAdminChatSkillsUseCase
    from app.composition.repository_composer import make_chat_skill_repository

    return ListAdminChatSkillsUseCase(repository=make_chat_skill_repository())


def make_create_admin_chat_skill_use_case():
    from app.application.use_cases.admin_chat_skill_use_cases import CreateAdminChatSkillUseCase
    from app.composition.repository_composer import make_chat_skill_repository

    return CreateAdminChatSkillUseCase(repository=make_chat_skill_repository())


def make_update_admin_chat_skill_use_case():
    from app.application.use_cases.admin_chat_skill_use_cases import UpdateAdminChatSkillUseCase
    from app.composition.repository_composer import make_chat_skill_repository

    return UpdateAdminChatSkillUseCase(repository=make_chat_skill_repository())


def make_deactivate_admin_chat_skill_use_case():
    from app.application.use_cases.admin_chat_skill_use_cases import DeactivateAdminChatSkillUseCase
    from app.composition.repository_composer import make_chat_skill_repository

    return DeactivateAdminChatSkillUseCase(repository=make_chat_skill_repository())
