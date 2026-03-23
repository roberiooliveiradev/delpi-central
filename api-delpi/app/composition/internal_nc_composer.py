from __future__ import annotations

from app.application.use_cases.internal_nc.create_internal_nonconformity_use_case import (
    CreateInternalNonconformityUseCase,
)
from app.application.use_cases.internal_nc.get_internal_nonconformity_details_use_case import (
    GetInternalNonconformityDetailsUseCase,
)
from app.application.use_cases.internal_nc.list_internal_nonconformities_use_case import (
    ListInternalNonconformitiesUseCase,
)
from app.application.use_cases.internal_nc.update_internal_nonconformity_use_case import (
    UpdateInternalNonconformityUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nonconformity_repository import (
    PostgresInternalNonconformityRepository,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_sequential_code_generator import (
    PostgresSequentialCodeGenerator,
)
from app.application.use_cases.internal_nc.transition_internal_nonconformity_status_use_case import (
    TransitionInternalNonconformityStatusUseCase,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_audit_event_repository import (
    PostgresAuditEventRepository,
)
from app.application.use_cases.internal_nc.add_internal_nc_root_cause_use_case import (
    AddInternalNcRootCauseUseCase,
)
from app.application.use_cases.internal_nc.list_internal_nc_root_causes_use_case import (
    ListInternalNcRootCausesUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nonconformity_root_cause_repository import (
    PostgresInternalNonconformityRootCauseRepository,
)
from app.application.use_cases.internal_nc.create_internal_nc_action_use_case import (
    CreateInternalNcActionUseCase,
)
from app.application.use_cases.internal_nc.update_internal_nc_action_use_case import (
    UpdateInternalNcActionUseCase,
)
from app.application.use_cases.internal_nc.complete_internal_nc_action_use_case import (
    CompleteInternalNcActionUseCase,
)
from app.application.use_cases.internal_nc.list_internal_nc_actions_use_case import (
    ListInternalNcActionsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nonconformity_action_repository import (
    PostgresInternalNonconformityActionRepository,
)
from app.application.use_cases.internal_nc.list_internal_nc_effectiveness_checks_use_case import (
    ListInternalNcEffectivenessChecksUseCase,
)
from app.application.use_cases.internal_nc.register_internal_nc_effectiveness_check_use_case import (
    RegisterInternalNcEffectivenessCheckUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nonconformity_effectiveness_repository import (
    PostgresInternalNonconformityEffectivenessRepository,
)

from app.application.use_cases.internal_nc.add_internal_nc_team_member_use_case import (
    AddInternalNcTeamMemberUseCase,
)
from app.application.use_cases.internal_nc.list_internal_nc_team_members_use_case import (
    ListInternalNcTeamMembersUseCase,
)
from app.application.use_cases.internal_nc.remove_internal_nc_team_member_use_case import (
    RemoveInternalNcTeamMemberUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nc_team_member_repository import (
    PostgresInternalNcTeamMemberRepository,
)
from app.application.use_cases.internal_nc.add_internal_nc_comment_use_case import (
    AddInternalNcCommentUseCase,
)
from app.application.use_cases.internal_nc.list_internal_nc_comments_use_case import (
    ListInternalNcCommentsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nc_comment_repository import (
    PostgresInternalNcCommentRepository,
)
from app.application.use_cases.internal_nc.upload_internal_nc_attachment_use_case import (
    UploadInternalNcAttachmentUseCase,
)
from app.application.use_cases.internal_nc.upload_internal_nc_action_attachment_use_case import (
    UploadInternalNcActionAttachmentUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nc_attachment_repository import (
    PostgresInternalNcAttachmentRepository,
)
from app.application.use_cases.internal_nc.get_internal_nonconformity_full_details_use_case import (
    GetInternalNonconformityFullDetailsUseCase,
)
from app.infrastructure.persistence.plugins.repositories.internal_nc.postgres_internal_nc_details_repository import (
    PostgresInternalNcDetailsRepository,
)



def build_create_internal_nonconformity_use_case() -> CreateInternalNonconformityUseCase:
    return CreateInternalNonconformityUseCase(
        repository=PostgresInternalNonconformityRepository(),
        sequential_code_generator=PostgresSequentialCodeGenerator(),
    )


def build_list_internal_nonconformities_use_case() -> ListInternalNonconformitiesUseCase:
    return ListInternalNonconformitiesUseCase(
        repository=PostgresInternalNonconformityRepository(),
    )


def build_get_internal_nonconformity_details_use_case() -> GetInternalNonconformityDetailsUseCase:
    return GetInternalNonconformityDetailsUseCase(
        repository=PostgresInternalNonconformityRepository(),
    )


def build_update_internal_nonconformity_use_case() -> UpdateInternalNonconformityUseCase:
    return UpdateInternalNonconformityUseCase(
        repository=PostgresInternalNonconformityRepository(),
    )


def build_transition_internal_nonconformity_status_use_case() -> TransitionInternalNonconformityStatusUseCase:
    return TransitionInternalNonconformityStatusUseCase(
        repository=PostgresInternalNonconformityRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
        effectiveness_repository=PostgresInternalNonconformityEffectivenessRepository(),
    )


def build_add_internal_nc_root_cause_use_case() -> AddInternalNcRootCauseUseCase:
    return AddInternalNcRootCauseUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        root_cause_repository=PostgresInternalNonconformityRootCauseRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_internal_nc_root_causes_use_case() -> ListInternalNcRootCausesUseCase:
    return ListInternalNcRootCausesUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        root_cause_repository=PostgresInternalNonconformityRootCauseRepository(),
    )


def build_create_internal_nc_action_use_case() -> CreateInternalNcActionUseCase:
    return CreateInternalNcActionUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        action_repository=PostgresInternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_update_internal_nc_action_use_case() -> UpdateInternalNcActionUseCase:
    return UpdateInternalNcActionUseCase(
        action_repository=PostgresInternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_complete_internal_nc_action_use_case() -> CompleteInternalNcActionUseCase:
    return CompleteInternalNcActionUseCase(
        action_repository=PostgresInternalNonconformityActionRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_internal_nc_actions_use_case() -> ListInternalNcActionsUseCase:
    return ListInternalNcActionsUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        action_repository=PostgresInternalNonconformityActionRepository(),
    )


def build_register_internal_nc_effectiveness_check_use_case() -> RegisterInternalNcEffectivenessCheckUseCase:
    return RegisterInternalNcEffectivenessCheckUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        effectiveness_repository=PostgresInternalNonconformityEffectivenessRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
        action_repository=PostgresInternalNonconformityActionRepository(),
    )


def build_list_internal_nc_effectiveness_checks_use_case() -> ListInternalNcEffectivenessChecksUseCase:
    return ListInternalNcEffectivenessChecksUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        effectiveness_repository=PostgresInternalNonconformityEffectivenessRepository(),
    )


def build_add_internal_nc_team_member_use_case() -> AddInternalNcTeamMemberUseCase:
    return AddInternalNcTeamMemberUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        team_member_repository=PostgresInternalNcTeamMemberRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_internal_nc_team_members_use_case() -> ListInternalNcTeamMembersUseCase:
    return ListInternalNcTeamMembersUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        team_member_repository=PostgresInternalNcTeamMemberRepository(),
    )


def build_remove_internal_nc_team_member_use_case() -> RemoveInternalNcTeamMemberUseCase:
    return RemoveInternalNcTeamMemberUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        team_member_repository=PostgresInternalNcTeamMemberRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_add_internal_nc_comment_use_case() -> AddInternalNcCommentUseCase:
    return AddInternalNcCommentUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        comment_repository=PostgresInternalNcCommentRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_list_internal_nc_comments_use_case() -> ListInternalNcCommentsUseCase:
    return ListInternalNcCommentsUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        comment_repository=PostgresInternalNcCommentRepository(),
    )



def build_upload_internal_nc_attachment_use_case() -> UploadInternalNcAttachmentUseCase:
    return UploadInternalNcAttachmentUseCase(
        nonconformity_repository=PostgresInternalNonconformityRepository(),
        attachment_repository=PostgresInternalNcAttachmentRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_upload_internal_nc_action_attachment_use_case() -> UploadInternalNcActionAttachmentUseCase:
    return UploadInternalNcActionAttachmentUseCase(
        action_repository=PostgresInternalNonconformityActionRepository(),
        attachment_repository=PostgresInternalNcAttachmentRepository(),
        audit_event_repository=PostgresAuditEventRepository(),
    )


def build_get_internal_nonconformity_full_details_use_case() -> GetInternalNonconformityFullDetailsUseCase:
    return GetInternalNonconformityFullDetailsUseCase(
        details_repository=PostgresInternalNcDetailsRepository(),
    )