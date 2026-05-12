from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_artifact import ChatArtifact


class ChatArtifactRepositoryPort(ABC):
    @abstractmethod
    def list_by_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> list[ChatArtifact]:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        session_id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        content: str,
        message_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> ChatArtifact:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        artifact_id: UUID,
        user_id: UUID,
    ) -> ChatArtifact | None:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        artifact_id: UUID,
        user_id: UUID,
        title: str | None = None,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> ChatArtifact | None:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        artifact_id: UUID,
        user_id: UUID,
    ) -> bool:
        raise NotImplementedError
