"""Agente operacional padrão para sessões sem agente explícito (chat «comum»)."""

from __future__ import annotations

from uuid import UUID

from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.infrastructure.config.settings import Settings


class ChatPlatformDefaultAgentService:
    @classmethod
    def resolve_agent_id(
        cls,
        agent_repository: ChatAgentRepositoryPort | None,
        user_id: UUID,
    ) -> UUID | None:
        if not agent_repository or not Settings.CHAT_PLATFORM_DEFAULT_AGENT_ENABLED:
            return None

        configured_id = Settings.CHAT_PLATFORM_DEFAULT_AGENT_ID

        if configured_id:
            try:
                parsed = UUID(configured_id)
            except ValueError:
                return None

            if agent_repository.get_enabled_by_id(parsed, user_id=user_id):
                return parsed

            return None

        agent_name = Settings.CHAT_PLATFORM_DEFAULT_AGENT_NAME

        if not agent_name:
            return None

        agent = agent_repository.get_enabled_system_by_name(agent_name, user_id=user_id)

        return agent.id if agent else None
