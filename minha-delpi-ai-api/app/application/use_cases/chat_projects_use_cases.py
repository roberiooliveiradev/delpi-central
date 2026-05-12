from uuid import UUID

from app.application.dto.chat_project_response import ChatProjectResponse
from app.application.dto.create_chat_project_request import CreateChatProjectRequest
from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.domain.entities.chat_project import ChatProject
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort


def _to_response(project: ChatProject) -> ChatProjectResponse:
    return ChatProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


def _validate_name(value: str | None) -> str:
    normalized = (value or "").strip()

    if not normalized:
        raise InvalidChatSessionInputError("Project name is required")

    if len(normalized) > 120:
        raise InvalidChatSessionInputError("Project name exceeds maximum length")

    return normalized


def _validate_description(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if len(normalized) > 500:
        raise InvalidChatSessionInputError("Project description exceeds maximum length")

    return normalized or None


class ListChatProjectsUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str) -> list[ChatProjectResponse]:
        projects = self.repository.list_by_user(UUID(user_id))
        return [_to_response(project) for project in projects]


class CreateChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: CreateChatProjectRequest) -> ChatProjectResponse:
        project = self.repository.create(
            user_id=UUID(request.user_id),
            name=_validate_name(request.name),
            description=_validate_description(request.description),
        )

        return _to_response(project)


class UpdateChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: UpdateChatProjectRequest) -> ChatProjectResponse | None:
        project = self.repository.update(
            project_id=UUID(request.project_id),
            user_id=UUID(request.user_id),
            name=_validate_name(request.name) if request.name is not None else None,
            description=_validate_description(request.description),
        )

        if not project:
            return None

        return _to_response(project)


class DeleteChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, project_id: str) -> bool:
        return self.repository.delete(
            project_id=UUID(project_id),
            user_id=UUID(user_id),
        )
