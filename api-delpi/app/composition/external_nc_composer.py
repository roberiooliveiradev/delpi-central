from __future__ import annotations

from app.application.use_cases.external_nc.create_external_nonconformity_use_case import (
    CreateExternalNonconformityUseCase,
)
from app.application.use_cases.external_nc.get_external_nonconformity_details_use_case import (
    GetExternalNonconformityDetailsUseCase,
)
from app.application.use_cases.external_nc.list_external_nonconformities_use_case import (
    ListExternalNonconformitiesUseCase,
)
from app.application.use_cases.external_nc.update_external_nonconformity_use_case import (
    UpdateExternalNonconformityUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nonconformity_repository import (
    PostgresExternalNonconformityRepository,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_sequential_code_generator import (
    PostgresSequentialCodeGenerator,
)
from app.application.use_cases.external_nc.transition_external_nonconformity_status_use_case import (
    TransitionExternalNonconformityStatusUseCase,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_audit_event_repository import (
    PostgresAuditEventRepository,
)
from app.application.use_cases.external_nc.add_external_nc_comment_use_case import (
    AddExternalNcCommentUseCase,
)
from app.application.use_cases.external_nc.list_external_nc_comments_use_case import (
    ListExternalNcCommentsUseCase,
)
from app.application.use_cases.external_nc.upload_external_nc_attachment_use_case import (
    UploadExternalNcAttachmentUseCase,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_attachment_repository import (
    PostgresAttachmentRepository,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_comment_repository import (
    PostgresCommentRepository,
)
from app.application.use_cases.external_nc.add_external_nc_root_cause_use_case import (
    AddExternalNcRootCauseUseCase,
)
from app.application.use_cases.external_nc.list_external_nc_root_causes_use_case import (
    ListExternalNcRootCausesUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nonconformity_root_cause_repository import (
    PostgresExternalNonconformityRootCauseRepository,
)
from app.application.use_cases.external_nc.create_external_nc_action_use_case import (
    CreateExternalNcActionUseCase,
)
from app.application.use_cases.external_nc.update_external_nc_action_use_case import (
    UpdateExternalNcActionUseCase,
)
from app.application.use_cases.external_nc.complete_external_nc_action_use_case import (
    CompleteExternalNcActionUseCase,
)
from app.application.use_cases.external_nc.list_external_nc_actions_use_case import (
    ListExternalNcActionsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nonconformity_action_repository import (
    PostgresExternalNonconformityActionRepository,
)
from app.application.use_cases.external_nc.list_external_nc_effectiveness_checks_use_case import (
    ListExternalNcEffectivenessChecksUseCase,
)
from app.application.use_cases.external_nc.register_external_nc_effectiveness_check_use_case import (
    RegisterExternalNcEffectivenessCheckUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nonconformity_effectiveness_repository import (
    PostgresExternalNonconformityEffectivenessRepository,
)
from app.application.use_cases.external_nc.upload_external_nc_action_attachment_use_case import (
    UploadExternalNcActionAttachmentUseCase,
)
from app.application.use_cases.external_nc.add_external_nc_team_member_use_case import (
    AddExternalNcTeamMemberUseCase,
)
from app.application.use_cases.external_nc.list_external_nc_team_members_use_case import (
    ListExternalNcTeamMembersUseCase,
)
from app.application.use_cases.external_nc.remove_external_nc_team_member_use_case import (
    RemoveExternalNcTeamMemberUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nc_team_member_repository import (
    PostgresExternalNcTeamMemberRepository,
)
from app.application.use_cases.external_nc.update_external_supplier_status_use_case import (
    UpdateExternalSupplierStatusUseCase,
)
from app.application.use_cases.external_nc.get_external_nc_dashboard_by_cause_use_case import (
    GetExternalNcDashboardByCauseUseCase,
)
from app.application.use_cases.external_nc.get_external_nc_dashboard_by_supplier_use_case import (
    GetExternalNcDashboardBySupplierUseCase,
)
from app.application.use_cases.external_nc.get_external_nc_dashboard_overdue_actions_use_case import (
    GetExternalNcDashboardOverdueActionsUseCase,
)
from app.application.use_cases.external_nc.get_external_nc_dashboard_summary_use_case import (
    GetExternalNcDashboardSummaryUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nc_dashboard_repository import (
    PostgresExternalNcDashboardRepository,
)
from app.application.use_cases.external_nc.export_nonconformity_report_use_case import (
    ExportNonconformityReportUseCase,
)
from app.infrastructure.persistence.plugins.repositories.external_nc.postgres_external_nc_export_repository import (
    PostgresExternalNcExportRepository,
)

def build_create_external_nonconformity_use_case() -> CreateExternalNonconformityUseCase:
    repository = PostgresExternalNonconformityRepository()
    sequential_code_generator = PostgresSequentialCodeGenerator()

    return CreateExternalNonconformityUseCase(
        repository=repository,
        sequential_code_generator=sequential_code_generator,
    )


def build_get_external_nonconformity_details_use_case() -> GetExternalNonconformityDetailsUseCase:
    repository = PostgresExternalNonconformityRepository()
    return GetExternalNonconformityDetailsUseCase(repository=repository)


def build_list_external_nonconformities_use_case() -> ListExternalNonconformitiesUseCase:
    repository = PostgresExternalNonconformityRepository()
    return ListExternalNonconformitiesUseCase(repository=repository)


def build_update_external_nonconformity_use_case() -> UpdateExternalNonconformityUseCase:
    repository = PostgresExternalNonconformityRepository()
    return UpdateExternalNonconformityUseCase(repository=repository)


def build_transition_external_nonconformity_status_use_case() -> TransitionExternalNonconformityStatusUseCase:
    repository = PostgresExternalNonconformityRepository()
    audit_event_repository = PostgresAuditEventRepository()
    effectiveness_repository = PostgresExternalNonconformityEffectivenessRepository()
    root_cause_repository = PostgresExternalNonconformityRootCauseRepository()

    return TransitionExternalNonconformityStatusUseCase(
        repository=repository,
        audit_event_repository=audit_event_repository,
        effectiveness_repository=effectiveness_repository,
        root_cause_repository=root_cause_repository,
    )


def build_add_external_nc_comment_use_case() -> AddExternalNcCommentUseCase:
    repository = PostgresExternalNonconformityRepository()
    comment_repository = PostgresCommentRepository()
    audit_event_repository = PostgresAuditEventRepository()

    return AddExternalNcCommentUseCase(
        repository=repository,
        comment_repository=comment_repository,
        audit_event_repository=audit_event_repository,
    )


def build_list_external_nc_comments_use_case() -> ListExternalNcCommentsUseCase:
    repository = PostgresExternalNonconformityRepository()
    comment_repository = PostgresCommentRepository()

    return ListExternalNcCommentsUseCase(
        repository=repository,
        comment_repository=comment_repository,
    )


def build_upload_external_nc_attachment_use_case() -> UploadExternalNcAttachmentUseCase:
    repository = PostgresExternalNonconformityRepository()
    attachment_repository = PostgresAttachmentRepository()
    audit_event_repository = PostgresAuditEventRepository()

    return UploadExternalNcAttachmentUseCase(
        repository=repository,
        attachment_repository=attachment_repository,
        audit_event_repository=audit_event_repository,
    )


def build_add_external_nc_root_cause_use_case() -> AddExternalNcRootCauseUseCase:
    nonconformity_repository = PostgresExternalNonconformityRepository()
    root_cause_repository = PostgresExternalNonconformityRootCauseRepository()
    audit_event_repository = PostgresAuditEventRepository()

    return AddExternalNcRootCauseUseCase(
        nonconformity_repository=nonconformity_repository,
        root_cause_repository=root_cause_repository,
        audit_event_repository=audit_event_repository,
    )


def build_list_external_nc_root_causes_use_case() -> ListExternalNcRootCausesUseCase:
    nonconformity_repository = PostgresExternalNonconformityRepository()
    root_cause_repository = PostgresExternalNonconformityRootCauseRepository()

    return ListExternalNcRootCausesUseCase(
        nonconformity_repository=nonconformity_repository,
        root_cause_repository=root_cause_repository,
    )


def build_create_external_nc_action_use_case() -> CreateExternalNcActionUseCase:
    return CreateExternalNcActionUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        action_repository=PostgresExternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_update_external_nc_action_use_case() -> UpdateExternalNcActionUseCase:
    return UpdateExternalNcActionUseCase(
        action_repository=PostgresExternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_complete_external_nc_action_use_case() -> CompleteExternalNcActionUseCase:
    return CompleteExternalNcActionUseCase(
        action_repository=PostgresExternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_external_nc_actions_use_case() -> ListExternalNcActionsUseCase:
    return ListExternalNcActionsUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        action_repository=PostgresExternalNonconformityActionRepository(),
    )


def build_register_external_nc_effectiveness_check_use_case() -> RegisterExternalNcEffectivenessCheckUseCase:
    return RegisterExternalNcEffectivenessCheckUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        effectiveness_repository=PostgresExternalNonconformityEffectivenessRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
        action_repository=PostgresExternalNonconformityActionRepository(),
    )


def build_list_external_nc_effectiveness_checks_use_case() -> ListExternalNcEffectivenessChecksUseCase:
    return ListExternalNcEffectivenessChecksUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        effectiveness_repository=PostgresExternalNonconformityEffectivenessRepository(),
    )


def build_upload_external_nc_action_attachment_use_case() -> UploadExternalNcActionAttachmentUseCase:
    return UploadExternalNcActionAttachmentUseCase(
        action_repository=PostgresExternalNonconformityActionRepository(),
        attachment_repository=PostgresAttachmentRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_add_external_nc_team_member_use_case() -> AddExternalNcTeamMemberUseCase:
    return AddExternalNcTeamMemberUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        team_member_repository=PostgresExternalNcTeamMemberRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_external_nc_team_members_use_case() -> ListExternalNcTeamMembersUseCase:
    return ListExternalNcTeamMembersUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        team_member_repository=PostgresExternalNcTeamMemberRepository(),
    )


def build_remove_external_nc_team_member_use_case() -> RemoveExternalNcTeamMemberUseCase:
    return RemoveExternalNcTeamMemberUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        team_member_repository=PostgresExternalNcTeamMemberRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_update_external_supplier_status_use_case() -> UpdateExternalSupplierStatusUseCase:
    return UpdateExternalSupplierStatusUseCase(
        nonconformity_repository=PostgresExternalNonconformityRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_get_external_nc_dashboard_summary_use_case() -> GetExternalNcDashboardSummaryUseCase:
    return GetExternalNcDashboardSummaryUseCase(
        dashboard_repository=PostgresExternalNcDashboardRepository(),
    )


def build_get_external_nc_dashboard_by_supplier_use_case() -> GetExternalNcDashboardBySupplierUseCase:
    return GetExternalNcDashboardBySupplierUseCase(
        dashboard_repository=PostgresExternalNcDashboardRepository(),
    )


def build_get_external_nc_dashboard_by_cause_use_case() -> GetExternalNcDashboardByCauseUseCase:
    return GetExternalNcDashboardByCauseUseCase(
        dashboard_repository=PostgresExternalNcDashboardRepository(),
    )


def build_get_external_nc_dashboard_overdue_actions_use_case() -> GetExternalNcDashboardOverdueActionsUseCase:
    return GetExternalNcDashboardOverdueActionsUseCase(
        dashboard_repository=PostgresExternalNcDashboardRepository(),
    )


def build_export_nonconformity_report_use_case() -> ExportNonconformityReportUseCase:
    return ExportNonconformityReportUseCase(
        export_repository=PostgresExternalNcExportRepository(),
    )