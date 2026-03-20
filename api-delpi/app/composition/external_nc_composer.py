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

    return TransitionExternalNonconformityStatusUseCase(
        repository=repository,
        audit_event_repository=audit_event_repository,
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