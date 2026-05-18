from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_project import ChatProject


class ChatProjectRepositoryPort(ABC):
    @abstractmethod
    def list_accessible(self, user_id: UUID, archived: bool = False) -> list[tuple[ChatProject, str]]:
        raise NotImplementedError

    @abstractmethod
    def get_accessible_by_id(self, project_id: UUID, user_id: UUID) -> tuple[ChatProject, str] | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
        instructions: str | None = None,
        default_agent_key: str | None = None,
        visibility: str = "private",
        icon: str | None = None,
        color: str | None = None,
        metadata: dict | None = None,
    ) -> ChatProject:
        raise NotImplementedError

    @abstractmethod
    def update(self, project_id: UUID, user_id: UUID, **fields) -> ChatProject | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def share(self, project_id: UUID, user_id: UUID, target_user_id: UUID, role: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_shares(self, project_id: UUID, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def revoke_share(self, project_id: UUID, user_id: UUID, target_user_id: UUID) -> bool:
        raise NotImplementedError
