from uuid import UUID

from app.application.dto.chat_project_response import ChatProjectResponse
from app.application.dto.create_chat_project_request import CreateChatProjectRequest
from app.application.dto.share_chat_project_request import ShareChatProjectRequest
from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.domain.entities.chat_project import ChatProject
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.domain.services.chat_project_settings_service import ChatProjectSettingsService


ALLOWED_VISIBILITY = {"private", "public"}
ALLOWED_SHARE_ROLES = {"viewer", "editor"}


def _parse_optional_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return UUID(normalized)


def _to_response(project: ChatProject, access_role: str = "viewer") -> ChatProjectResponse:
    return ChatProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        instructions=project.instructions,
        default_agent_id=str(project.default_agent_id) if project.default_agent_id else None,
        visibility=project.visibility,
        icon=project.icon,
        color=project.color,
        archived_at=project.archived_at.isoformat() if project.archived_at else None,
        metadata=project.metadata,
        share_conversation_context=ChatProjectSettingsService.share_conversation_context_enabled(
            project.metadata
        ),
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

        metadata = ChatProjectSettingsService.merge_metadata(
            None,
            patch=request.metadata,
            share_conversation_context=request.share_conversation_context,
        )

        project = self.repository.create(
            user_id=UUID(request.user_id),
            name=_validate_text(request.name, 120, required=True),
            description=_validate_text(request.description, 500),
            instructions=_validate_text(request.instructions, 12000),
            default_agent_id=_parse_optional_uuid(request.default_agent_id),
            visibility=visibility,
            icon=_validate_text(request.icon, 60),
            color=_validate_text(request.color, 40),
            metadata=metadata,
        )

        return _to_response(project, "owner")


class UpdateChatProjectUseCase:
    def __init__(self, repository: ChatProjectRepositoryPort):
        self.repository = repository

    def execute(self, request: UpdateChatProjectRequest) -> ChatProjectResponse | None:
        if request.visibility is not None and request.visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid project visibility")

        project_metadata = None

        if request.metadata is not None or request.share_conversation_context is not None:
            current = self.repository.get_accessible_by_id(
                project_id=UUID(request.project_id),
                user_id=UUID(request.user_id),
            )

            existing_meta = current[0].metadata if current else {}

            project_metadata = ChatProjectSettingsService.merge_metadata(
                existing_meta,
                patch=request.metadata,
                share_conversation_context=request.share_conversation_context,
            )

        update_fields: dict = {
            "name": _validate_text(request.name, 120) if request.name is not None else None,
            "description": _validate_text(request.description, 500)
            if request.description is not None
            else None,
            "instructions": _validate_text(request.instructions, 12000)
            if request.instructions is not None
            else None,
            "visibility": request.visibility,
            "icon": _validate_text(request.icon, 60) if request.icon is not None else None,
            "color": _validate_text(request.color, 40) if request.color is not None else None,
            "project_metadata": project_metadata,
            "archived": request.archived,
        }

        apply_null: set[str] = set()

        if request.explicit_default_agent_id:
            if request.default_agent_id:
                update_fields["default_agent_id"] = _parse_optional_uuid(request.default_agent_id)
            else:
                update_fields["default_agent_id"] = None
                apply_null.add("default_agent_id")

        project = self.repository.update(
            project_id=UUID(request.project_id),
            user_id=UUID(request.user_id),
            apply_null=frozenset(apply_null),
            **update_fields,
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
