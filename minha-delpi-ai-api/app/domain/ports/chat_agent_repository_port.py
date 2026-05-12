from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_agent import ChatAgent


class ChatAgentRepositoryPort(ABC):
    @abstractmethod
    def list_accessible(self, user_id: UUID) -> list[tuple[ChatAgent, str]]:
        raise NotImplementedError

    @abstractmethod
    def get_accessible_by_id(self, agent_id: UUID, user_id: UUID) -> tuple[ChatAgent, str] | None:
        raise NotImplementedError

    @abstractmethod
    def get_enabled_by_key(self, key: str, user_id: UUID | None = None) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        owner_user_id: UUID,
        key: str,
        name: str,
        description: str | None,
        system_prompt: str | None,
        visibility: str,
        category: str | None,
        icon: str | None,
        response_style: str | None,
        metadata: dict | None,
    ) -> ChatAgent:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        agent_id: UUID,
        user_id: UUID,
        **fields,
    ) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, agent_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def share(self, agent_id: UUID, user_id: UUID, target_user_id: UUID, role: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def upsert_action(
        self,
        agent_id: UUID,
        user_id: UUID,
        provider_key: str,
        action_id: str,
        sensitivity: str,
        requires_confirmation: bool,
        enabled: bool,
    ) -> bool:
        raise NotImplementedError
