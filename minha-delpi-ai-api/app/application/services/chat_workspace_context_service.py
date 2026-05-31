from uuid import UUID

from app.application.services.agent_specialization_service import (
    AgentSpecializationService,
)
from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.application.services.chat_platform_default_agent_service import (
    ChatPlatformDefaultAgentService,
)


class ChatWorkspaceContextService:
    def __init__(
        self,
        project_repository: ChatProjectRepositoryPort,
        agent_repository: ChatAgentRepositoryPort,
    ):
        self.project_repository = project_repository
        self.agent_repository = agent_repository
        self.specialization_service = AgentSpecializationService()

    def build_context(
        self,
        *,
        session,
        user_id: UUID,
        request_agent_id: UUID | str | None = None,
    ) -> dict:
        project = None
        agent = None
        parsed_request_agent_id = self._parse_agent_id(request_agent_id)

        if session.project_id:
            result = self.project_repository.get_accessible_by_id(
                project_id=session.project_id,
                user_id=user_id,
            )

            if result:
                project, _role = result

        user_activated_agent_id = session.agent_id or parsed_request_agent_id
        agent_id = user_activated_agent_id or (project.default_agent_id if project else None)

        if not agent_id:
            agent_id = ChatPlatformDefaultAgentService.resolve_agent_id(
                self.agent_repository,
                user_id,
            )

        if agent_id:
            agent = self.agent_repository.get_enabled_by_id(agent_id, user_id=user_id)

        allowed_action_ids = self._allowed_action_ids(agent, user_id)
        actions_enabled = bool(agent and allowed_action_ids)
        user_activated_agent = bool(user_activated_agent_id and actions_enabled)

        return {
            "project": self._project_metadata(project),
            "agent": self._agent_metadata(agent),
            "projectPrompt": self._project_prompt(project),
            "agentPrompt": agent.system_prompt if agent else None,
            "agentId": str(agent.id) if agent else None,
            "actionProviderKeys": self._action_provider_keys(agent, user_id),
            "allowedActionIds": allowed_action_ids,
            "actionsEnabled": actions_enabled,
            "userActivatedAgent": user_activated_agent,
            "capabilities": self._capabilities(agent),
            "skills": ChatAgentSkillsService.resolve(
                agent_metadata=agent.metadata if agent else {},
                allowed_action_ids=allowed_action_ids,
                has_agent=bool(agent),
            ),
            "specialization": self._specialization(agent),
        }

    def _project_metadata(self, project) -> dict | None:
        if not project:
            return None

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "instructions": project.instructions,
            "defaultAgentId": str(project.default_agent_id) if project.default_agent_id else None,
            "metadata": project.metadata,
        }

    def _agent_metadata(self, agent) -> dict | None:
        if not agent:
            return None

        return {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "category": agent.category,
            "metadata": agent.metadata,
            "responseStyle": agent.response_style,
            "maxToolCalls": agent.max_tool_calls,
            "requiresConfirmationForWrite": agent.requires_confirmation_for_write,
        }

    def _project_prompt(self, project) -> str | None:
        if not project:
            return None

        parts: list[str] = []

        if project.name:
            parts.append(f"Projeto atual: {project.name}")

        if project.description:
            parts.append(f"Descrição do projeto: {project.description}")

        if project.instructions:
            parts.append(f"Instruções do projeto: {project.instructions}")

        if not parts:
            return None

        return "\n".join(parts)

    def _specialization(self, agent) -> dict | None:
        if not agent:
            return None

        metadata = agent.metadata or {}

        return self.specialization_service.parse(metadata.get("specialization"))

    @staticmethod
    def _parse_agent_id(value: UUID | str | None) -> UUID | None:
        if not value:
            return None

        if isinstance(value, UUID):
            return value

        normalized = str(value).strip()

        if not normalized:
            return None

        try:
            return UUID(normalized)
        except ValueError:
            return None

    def _allowed_action_ids(self, agent, user_id: UUID) -> list[str]:
        if not agent:
            return []

        configured_actions = self.agent_repository.list_enabled_action_ids(
            agent_id=agent.id,
            user_id=user_id,
        )

        if configured_actions:
            return configured_actions

        metadata = agent.metadata or {}
        allowed = metadata.get("allowed_actions") or metadata.get("allowedActions")

        if isinstance(allowed, list):
            return [str(item) for item in allowed if str(item).strip()]

        return []

    def _action_provider_keys(self, agent, user_id: UUID) -> list[str]:
        if not agent:
            return []

        return self.agent_repository.list_enabled_provider_keys(
            agent_id=agent.id,
            user_id=user_id,
        )

    def _capabilities(self, agent) -> dict:
        if not agent:
            return {}

        metadata = agent.metadata or {}
        capabilities = metadata.get("capabilities")

        if isinstance(capabilities, dict):
            return capabilities

        return {}
