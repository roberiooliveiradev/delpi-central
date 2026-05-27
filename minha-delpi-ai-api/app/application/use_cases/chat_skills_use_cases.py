from uuid import UUID

from app.application.dto.upsert_chat_agent_skill_request import UpsertChatAgentSkillRequest
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from app.infrastructure.config.settings import Settings


class ListChatSkillCatalogUseCase:
    def execute(self) -> list[dict]:
        return ChatSkillRegistry.list_catalog()


class ListChatAgentSkillsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str) -> list[dict] | None:
        record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not record:
            return None

        agent, _access_role = record
        allowed_action_ids = self.repository.list_enabled_action_ids(
            UUID(agent_id),
            UUID(user_id),
        )

        return ChatSkillRegistry.list_agent_bindings(
            agent_metadata=agent.metadata,
            allowed_action_ids=allowed_action_ids,
            has_agent=True,
            default_sql_authoring=Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL,
            default_company_knowledge=Settings.CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL,
        )


class UpsertChatAgentSkillUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: UpsertChatAgentSkillRequest) -> bool:
        skill_key = (request.skill_key or "").strip().lower()

        if not skill_key:
            raise InvalidChatSessionInputError("skillKey is required")

        if not ChatSkillRegistry.get(skill_key):
            raise InvalidChatSessionInputError("Unknown skill key")

        return self.repository.upsert_skill(
            agent_id=UUID(request.agent_id),
            user_id=UUID(request.user_id),
            skill_key=skill_key,
            enabled=bool(request.enabled),
            can_manage_official_agents=request.can_manage_official_agents,
        )
