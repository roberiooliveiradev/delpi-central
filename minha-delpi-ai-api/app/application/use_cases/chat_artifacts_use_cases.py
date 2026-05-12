from uuid import UUID

from app.application.dto.chat_artifact_response import ChatArtifactResponse
from app.application.dto.create_chat_artifact_request import CreateChatArtifactRequest
from app.application.dto.update_chat_artifact_request import UpdateChatArtifactRequest
from app.domain.entities.chat_artifact import ChatArtifact
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
    InvalidChatSessionInputError,
)
from app.domain.ports.chat_artifact_repository_port import ChatArtifactRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


ALLOWED_ARTIFACT_TYPES = {"markdown", "table", "json", "report"}


def _to_response(artifact: ChatArtifact) -> ChatArtifactResponse:
    return ChatArtifactResponse(
        id=str(artifact.id),
        session_id=str(artifact.session_id),
        message_id=str(artifact.message_id) if artifact.message_id else None,
        user_id=str(artifact.user_id),
        type=artifact.type,
        title=artifact.title,
        content=artifact.content,
        metadata=artifact.metadata,
        created_at=artifact.created_at.isoformat(),
        updated_at=artifact.updated_at.isoformat(),
    )


def _validate_artifact_type(value: str) -> str:
    normalized = (value or "").strip().lower()

    if normalized not in ALLOWED_ARTIFACT_TYPES:
        raise InvalidChatSessionInputError("Invalid artifact type")

    return normalized


def _validate_title(value: str | None) -> str:
    normalized = (value or "").strip()

    if not normalized:
        raise InvalidChatSessionInputError("Artifact title is required")

    if len(normalized) > 180:
        raise InvalidChatSessionInputError("Artifact title exceeds maximum length")

    return normalized


def _validate_content(value: str | None) -> str:
    normalized = value if isinstance(value, str) else ""

    if not normalized.strip():
        raise InvalidChatSessionInputError("Artifact content is required")

    if len(normalized) > 200_000:
        raise InvalidChatSessionInputError("Artifact content exceeds maximum length")

    return normalized


class ListChatArtifactsUseCase:
    def __init__(
        self,
        artifact_repository: ChatArtifactRepositoryPort,
        session_repository: ChatSessionRepositoryPort,
    ):
        self.artifact_repository = artifact_repository
        self.session_repository = session_repository

    def execute(self, user_id: str, session_id: str) -> list[ChatArtifactResponse]:
        user_uuid = UUID(user_id)
        session_uuid = UUID(session_id)

        session = self.session_repository.get_session_by_id(session_uuid)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_uuid:
            raise ChatSessionAccessDeniedError()

        artifacts = self.artifact_repository.list_by_session(
            session_id=session_uuid,
            user_id=user_uuid,
        )

        return [_to_response(artifact) for artifact in artifacts]


class CreateChatArtifactUseCase:
    def __init__(
        self,
        artifact_repository: ChatArtifactRepositoryPort,
        session_repository: ChatSessionRepositoryPort,
    ):
        self.artifact_repository = artifact_repository
        self.session_repository = session_repository

    def execute(self, request: CreateChatArtifactRequest) -> ChatArtifactResponse:
        user_uuid = UUID(request.user_id)
        session_uuid = UUID(request.session_id)

        session = self.session_repository.get_session_by_id(session_uuid)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_uuid:
            raise ChatSessionAccessDeniedError()

        artifact = self.artifact_repository.create(
            session_id=session_uuid,
            user_id=user_uuid,
            message_id=UUID(request.message_id) if request.message_id else None,
            type=_validate_artifact_type(request.type),
            title=_validate_title(request.title),
            content=_validate_content(request.content),
            metadata=request.metadata,
        )

        return _to_response(artifact)


class UpdateChatArtifactUseCase:
    def __init__(self, artifact_repository: ChatArtifactRepositoryPort):
        self.artifact_repository = artifact_repository

    def execute(self, request: UpdateChatArtifactRequest) -> ChatArtifactResponse | None:
        artifact = self.artifact_repository.update(
            artifact_id=UUID(request.artifact_id),
            user_id=UUID(request.user_id),
            title=_validate_title(request.title) if request.title is not None else None,
            content=_validate_content(request.content)
            if request.content is not None
            else None,
            metadata=request.metadata,
        )

        if not artifact:
            return None

        return _to_response(artifact)


class DeleteChatArtifactUseCase:
    def __init__(self, artifact_repository: ChatArtifactRepositoryPort):
        self.artifact_repository = artifact_repository

    def execute(self, user_id: str, artifact_id: str) -> bool:
        return self.artifact_repository.delete(
            artifact_id=UUID(artifact_id),
            user_id=UUID(user_id),
        )
