from app.application.dto.chat_agent_response import ChatAgentResponse
from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort


def _to_response(agent: ChatAgent) -> ChatAgentResponse:
    return ChatAgentResponse(
        id=str(agent.id),
        key=agent.key,
        name=agent.name,
        description=agent.description,
        enabled=agent.enabled,
        metadata=agent.metadata,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


class ListChatAgentsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self) -> list[ChatAgentResponse]:
        agents = self.repository.list_enabled()
        return [_to_response(agent) for agent in agents]
