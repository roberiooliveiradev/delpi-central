from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_agent import ChatAgent


class ChatAgentRepositoryPort(ABC):
    @abstractmethod
    def list_accessible(
        self,
        user_id: UUID,
        *,
        include_disabled: bool = False,
    ) -> list[tuple[ChatAgent, str]]:
        raise NotImplementedError

    @abstractmethod
    def list_shares(self, agent_id: UUID, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def revoke_share(self, agent_id: UUID, user_id: UUID, target_user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    def can_edit(
        self,
        agent_id: UUID,
        user_id: UUID,
        can_manage_official_agents: bool = False,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_accessible_by_id(self, agent_id: UUID, user_id: UUID) -> tuple[ChatAgent, str] | None:
        raise NotImplementedError

    @abstractmethod
    def get_enabled_by_key(self, key: str, user_id: UUID | None = None) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def get_for_preview(self, agent_id: UUID, user_id: UUID) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def publish(
        self,
        agent_id: UUID,
        user_id: UUID,
        *,
        can_manage_official_agents: bool = False,
    ) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def list_versions(self, agent_id: UUID, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        owner_user_id: UUID | None,
        key: str,
        name: str,
        description: str | None,
        system_prompt: str | None,
        visibility: str,
        category: str | None,
        icon: str | None,
        response_style: str | None,
        metadata: dict | None,
        *,
        max_tool_calls: int | None = None,
        requires_confirmation_for_write: bool | None = None,
        enabled: bool | None = None,
    ) -> ChatAgent:
        raise NotImplementedError

    @abstractmethod
    def duplicate(
        self,
        agent_id: UUID,
        user_id: UUID,
        *,
        can_manage_official_agents: bool = False,
        copy_actions: bool = False,
    ) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def apply_exported_action_configuration(
        self,
        agent_id: UUID,
        providers: list[dict],
        actions: list[dict],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def transfer_ownership(
        self,
        agent_id: UUID,
        user_id: UUID,
        new_owner_id: UUID,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_usage_summaries(
        self,
        agent_keys: list[str],
        *,
        hours: int = 168,
    ) -> dict[str, dict[str, int]]:
        raise NotImplementedError

    @abstractmethod
    def get_usage_stats(
        self,
        agent_id: UUID,
        user_id: UUID,
        *,
        hours: int = 168,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        agent_id: UUID,
        user_id: UUID,
        can_manage_official_agents: bool = False,
        **fields,
    ) -> ChatAgent | None:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        agent_id: UUID,
        user_id: UUID,
        can_manage_official_agents: bool = False,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def share(self, agent_id: UUID, user_id: UUID, target_user_id: UUID, role: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_action_providers(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def upsert_action_provider(
        self,
        agent_id: UUID,
        user_id: UUID,
        provider_key: str,
        enabled: bool,
        allow_read: bool,
        allow_write: bool,
        allow_admin: bool,
        requires_confirmation_for_write: bool,
        can_manage_official_agents: bool = False,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_enabled_provider_keys(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_actions(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_enabled_action_ids(
        self,
        agent_id: UUID,
        user_id: UUID,
    ) -> list[str]:
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
        can_manage_official_agents: bool = False,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def upsert_skill(
        self,
        agent_id: UUID,
        user_id: UUID,
        skill_key: str,
        enabled: bool,
        can_manage_official_agents: bool = False,
    ) -> bool:
        raise NotImplementedError
