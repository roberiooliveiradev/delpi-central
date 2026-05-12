from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_project import ChatProject


class ChatProjectRepositoryPort(ABC):
    @abstractmethod
    def list_by_user(self, user_id: UUID) -> list[ChatProject]:
        raise NotImplementedError

    @abstractmethod
    def create(self, user_id: UUID, name: str, description: str | None = None) -> ChatProject:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, project_id: UUID, user_id: UUID) -> ChatProject | None:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> ChatProject | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError
