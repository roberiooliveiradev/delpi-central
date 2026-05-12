from uuid import UUID

from app.domain.entities.chat_artifact import ChatArtifact
from app.domain.ports.chat_artifact_repository_port import ChatArtifactRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_artifact_model import AiChatArtifactModel


class PostgresChatArtifactRepository(ChatArtifactRepositoryPort):
    def list_by_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> list[ChatArtifact]:
        models = (
            AiChatArtifactModel.query
            .filter(AiChatArtifactModel.session_id == session_id)
            .filter(AiChatArtifactModel.user_id == user_id)
            .order_by(AiChatArtifactModel.updated_at.desc())
            .all()
        )

        return [self._to_entity(model) for model in models]

    def create(
        self,
        session_id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        content: str,
        message_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> ChatArtifact:
        model = AiChatArtifactModel(
            session_id=session_id,
            user_id=user_id,
            message_id=message_id,
            type=type,
            title=title,
            content=content,
            artifact_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def get_by_id(
        self,
        artifact_id: UUID,
        user_id: UUID,
    ) -> ChatArtifact | None:
        model = (
            AiChatArtifactModel.query
            .filter(AiChatArtifactModel.id == artifact_id)
            .filter(AiChatArtifactModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def update(
        self,
        artifact_id: UUID,
        user_id: UUID,
        title: str | None = None,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> ChatArtifact | None:
        model = (
            AiChatArtifactModel.query
            .filter(AiChatArtifactModel.id == artifact_id)
            .filter(AiChatArtifactModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        if title is not None:
            model.title = title

        if content is not None:
            model.content = content

        if metadata is not None:
            model.artifact_metadata = metadata

        db.session.flush()

        return self._to_entity(model)

    def delete(
        self,
        artifact_id: UUID,
        user_id: UUID,
    ) -> bool:
        model = (
            AiChatArtifactModel.query
            .filter(AiChatArtifactModel.id == artifact_id)
            .filter(AiChatArtifactModel.user_id == user_id)
            .first()
        )

        if not model:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def _to_entity(self, model: AiChatArtifactModel) -> ChatArtifact:
        return ChatArtifact(
            id=model.id,
            session_id=model.session_id,
            message_id=model.message_id,
            user_id=model.user_id,
            type=model.type,
            title=model.title,
            content=model.content,
            metadata=model.artifact_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
