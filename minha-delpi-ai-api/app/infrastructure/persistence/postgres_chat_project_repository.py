from uuid import UUID

from app.domain.entities.chat_project import ChatProject
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_project_model import AiChatProjectModel


class PostgresChatProjectRepository(ChatProjectRepositoryPort):
    def list_by_user(self, user_id: UUID) -> list[ChatProject]:
        models = (
            AiChatProjectModel.query
            .filter(AiChatProjectModel.user_id == user_id)
            .order_by(AiChatProjectModel.updated_at.desc())
            .all()
        )

        return [self._to_entity(model) for model in models]

    def create(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> ChatProject:
        model = AiChatProjectModel(
            user_id=user_id,
            name=name,
            description=description,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def get_by_id(self, project_id: UUID, user_id: UUID) -> ChatProject | None:
        model = (
            AiChatProjectModel.query
            .filter(AiChatProjectModel.id == project_id)
            .filter(AiChatProjectModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def update(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> ChatProject | None:
        model = (
            AiChatProjectModel.query
            .filter(AiChatProjectModel.id == project_id)
            .filter(AiChatProjectModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        if name is not None:
            model.name = name

        if description is not None:
            model.description = description

        db.session.flush()

        return self._to_entity(model)

    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        model = (
            AiChatProjectModel.query
            .filter(AiChatProjectModel.id == project_id)
            .filter(AiChatProjectModel.user_id == user_id)
            .first()
        )

        if not model:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def _to_entity(self, model: AiChatProjectModel) -> ChatProject:
        return ChatProject(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
