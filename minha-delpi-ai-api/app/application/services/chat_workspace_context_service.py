from uuid import UUID

from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort


class ChatWorkspaceContextService:
    def __init__(
        self,
        project_repository: ChatProjectRepositoryPort,
        agent_repository: ChatAgentRepositoryPort,
    ):
        self.project_repository = project_repository
        self.agent_repository = agent_repository

    def build_context(self, *, session, user_id: UUID) -> dict:
        project = None
        agent = None

        if session.project_id:
            result = self.project_repository.get_accessible_by_id(
                project_id=session.project_id,
                user_id=user_id,
            )

            if result:
                project, _role = result

        agent_key = session.agent_key or (project.default_agent_key if project else None)

        if agent_key:
            agent = self.agent_repository.get_enabled_by_key(agent_key, user_id=user_id)

        return {
            "project": self._project_metadata(project),
            "agent": self._agent_metadata(agent),
            "projectPrompt": self._project_prompt(project),
            "agentPrompt": agent.system_prompt if agent else None,
            "agentKey": agent.key if agent else None,
            "actionProviderKeys": self._action_provider_keys(agent, user_id),
            "allowedActionIds": self._allowed_action_ids(agent, user_id),
            "actionsEnabled": bool(agent and self._allowed_action_ids(agent, user_id)),
            "capabilities": self._capabilities(agent),
        }

    def _project_metadata(self, project) -> dict | None:
        if not project:
            return None

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "instructions": project.instructions,
            "defaultAgentKey": project.default_agent_key,
            "metadata": project.metadata,
        }

    def _agent_metadata(self, agent) -> dict | None:
        if not agent:
            return None

        return {
            "key": agent.key,
            "name": agent.name,
            "description": agent.description,
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
