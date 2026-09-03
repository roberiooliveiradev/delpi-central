from __future__ import annotations

from requests_app.application.use_cases.file_use_cases import FileUseCases
from requests_app.application.use_cases.request_use_cases import (
    CreateRequestUseCase,
    GetRequestTypeUseCase,
    GetRequestUseCase,
    ListMyRequestsUseCase,
    ListRequestTypesUseCase,
    ListWorkQueueRequestsUseCase,
    TransitionRequestUseCase,
    UpdateRequestPayloadUseCase,
)
from requests_app.application.services.attachment_storage import (
    ArtifactStorage,
    AttachmentStorage,
)
from requests_app.domain.services.workflow_engine import WorkflowEngine
from requests_app.infrastructure.persistence.repositories.postgres_file_repository import (
    PostgresFileRepository,
)
from requests_app.infrastructure.persistence.repositories.postgres_repositories import (
    PostgresIdempotencyRepository,
    PostgresRequestRepository,
    PostgresRequestTypeRepository,
)


def _engine() -> WorkflowEngine:
    return WorkflowEngine()


def build_file_use_cases() -> FileUseCases:
    return FileUseCases(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        PostgresFileRepository(),
        AttachmentStorage(),
        ArtifactStorage(),
        _engine(),
    )


def build_list_request_types_use_case() -> ListRequestTypesUseCase:
    return ListRequestTypesUseCase(PostgresRequestTypeRepository())


def build_get_request_type_use_case() -> GetRequestTypeUseCase:
    return GetRequestTypeUseCase(PostgresRequestTypeRepository())


def build_create_request_use_case() -> CreateRequestUseCase:
    return CreateRequestUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        PostgresIdempotencyRepository(),
        _engine(),
        PostgresFileRepository(),
    )


def build_list_my_requests_use_case() -> ListMyRequestsUseCase:
    return ListMyRequestsUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        _engine(),
    )


def build_list_work_queue_use_case() -> ListWorkQueueRequestsUseCase:
    return ListWorkQueueRequestsUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        _engine(),
    )


def build_get_request_use_case() -> GetRequestUseCase:
    return GetRequestUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        _engine(),
    )


def build_update_request_payload_use_case() -> UpdateRequestPayloadUseCase:
    return UpdateRequestPayloadUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        PostgresIdempotencyRepository(),
        _engine(),
    )


def build_transition_request_use_case() -> TransitionRequestUseCase:
    return TransitionRequestUseCase(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        PostgresIdempotencyRepository(),
        _engine(),
        PostgresFileRepository(),
    )


def build_timeline_use_cases():
    from requests_app.application.use_cases.timeline_use_cases import TimelineUseCases

    return TimelineUseCases(
        PostgresRequestTypeRepository(),
        PostgresRequestRepository(),
        PostgresFileRepository(),
    )
