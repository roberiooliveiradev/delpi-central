from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.infrastructure.db.models.chat_agent_model import AiChatAgentModel


class PostgresChatAgentRepository(ChatAgentRepositoryPort):
    def list_enabled(self) -> list[ChatAgent]:
        models = (
            AiChatAgentModel.query
            .filter(AiChatAgentModel.enabled.is_(True))
            .order_by(AiChatAgentModel.name.asc())
            .all()
        )

        return [self._to_entity(model) for model in models]

    def get_enabled_by_key(self, key: str) -> ChatAgent | None:
        model = (
            AiChatAgentModel.query
            .filter(AiChatAgentModel.key == key)
            .filter(AiChatAgentModel.enabled.is_(True))
            .first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def _to_entity(self, model: AiChatAgentModel) -> ChatAgent:
        return ChatAgent(
            id=model.id,
            key=model.key,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            enabled=model.enabled,
            metadata=model.agent_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
