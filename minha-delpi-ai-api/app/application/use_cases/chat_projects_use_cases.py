from uuid import UUID

from app.application.dto.chat_project_response import ChatProjectResponse
from app.application.dto.create_chat_project_request import CreateChatProjectRequest
from app.application.dto.share_chat_project_request import ShareChatProjectRequest
from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.domain.entities.chat_project import ChatProject
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort


ALLOWED_VISIBILITY = {"private", "public"}
ALLOWED_SHARE_ROLES = {"viewer", "editor"}


def _to_response(project: ChatProject, access_role: str = "viewer") -> ChatProjectResponse:
    return ChatProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        instructions=project.instructions,
        default_agent_key=project.default_agent_key,
        visibility=project.visibility,
        icon=project.icon,
        color=project.color,
        archived_at=project.archived_at.isoformat() if project.archived_at else None,
        metadata=project.metadata,
        access_role=access_role,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


def _validate_text(
    value: str | None,
    max_length: int,
    required: bool = False,
) -> str | None:
    normalized = (value or "").strip()

    if required and not normalized:
        raise InvalidChatSessionInputError("Required field is empty")

    if not normalized:
        return None

    if len(normalized) > max_length:
        raise InvalidChatSessionInputError(f"Field exceeds maximum length of {max_length}")

    return normalized


class ListChatProjectsUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, archived: bool = False) -> list[ChatProjectResponse]:
        projects = self.repository.list_accessible(UUID(user_id), archived=archived)
        return [_to_response(project, access_role) for project, access_role in projects]


class CreateChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: CreateChatProjectRequest) -> ChatProjectResponse:
        visibility = request.visibility or "private"

        if visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid project visibility")

        project = self.repository.create(
            user_id=UUID(request.user_id),
            name=_validate_text(request.name, 120, required=True),
            description=_validate_text(request.description, 500),
            instructions=_validate_text(request.instructions, 12000),
            default_agent_key=_validate_text(request.default_agent_key, 80),
            visibility=visibility,
            icon=_validate_text(request.icon, 60),
            color=_validate_text(request.color, 40),
            metadata=request.metadata,
        )

        return _to_response(project, "owner")


class UpdateChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: UpdateChatProjectRequest) -> ChatProjectResponse | None:
        if request.visibility is not None and request.visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid project visibility")

        project = self.repository.update(
            project_id=UUID(request.project_id),
            user_id=UUID(request.user_id),
            name=_validate_text(request.name, 120) if request.name is not None else None,
            description=_validate_text(request.description, 500) if request.description is not None else None,
            instructions=_validate_text(request.instructions, 12000) if request.instructions is not None else None,
            default_agent_key=_validate_text(request.default_agent_key, 80) if request.default_agent_key is not None else None,
            visibility=request.visibility,
            icon=_validate_text(request.icon, 60) if request.icon is not None else None,
            color=_validate_text(request.color, 40) if request.color is not None else None,
            project_metadata=request.metadata,
            archived=request.archived,
        )

        if not project:
            return None

        return _to_response(project, "editor")


class DeleteChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, project_id: str) -> bool:
        return self.repository.delete(
            project_id=UUID(project_id),
            user_id=UUID(user_id),
        )


class ShareChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: ShareChatProjectRequest) -> bool:
        role = request.role or "viewer"

        if role not in ALLOWED_SHARE_ROLES:
            raise InvalidChatSessionInputError("Invalid share role")

        return self.repository.share(
            project_id=UUID(request.project_id),
            user_id=UUID(request.user_id),
            target_user_id=UUID(request.target_user_id),
            role=role,
        )


class ListChatProjectSharesUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort, share_profile_service=None):
        self.repository = repository
        self.share_profile_service = share_profile_service

    def execute(
        self,
        *,
        user_id: str,
        project_id: str,
        access_token: str | None = None,
    ) -> list[dict]:
        shares = self.repository.list_shares(UUID(project_id), UUID(user_id))

        if self.share_profile_service:
            return self.share_profile_service.enrich_shares(
                shares,
                access_token=access_token,
            )

        return shares


class RevokeChatProjectShareUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, project_id: str, target_user_id: str) -> bool:
        return self.repository.revoke_share(
            UUID(project_id),
            UUID(user_id),
            UUID(target_user_id),
        )
