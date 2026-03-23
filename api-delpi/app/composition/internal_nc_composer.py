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