from uuid import UUID

from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class PostgresChatSessionRepository(ChatSessionRepositoryPort):
    def create_session(
        self,
        user_id: UUID,
        title: str | None,
        context: str | None,
    ) -> ChatSession:
        model = AiChatSessionModel(
            user_id=user_id,
            title=title,
            context=context,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_session_entity(model)

    def list_sessions_by_user(self, user_id: UUID) -> list[ChatSession]:
        models = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.user_id == user_id)
            .order_by(AiChatSessionModel.updated_at.desc())
            .all()
        )

        return [self._to_session_entity(model) for model in models]

    def get_session_by_id(self, session_id: UUID) -> ChatSession | None:
        model = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == session_id
        ).first()

        if not model:
            return None

        return self._to_session_entity(model)

    def list_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        models = (
            AiChatMessageModel.query
            .filter(AiChatMessageModel.session_id == session_id)
            .order_by(AiChatMessageModel.created_at.asc())
            .all()
        )

        return [self._to_message_entity(model) for model in models]

    def _to_session_entity(self, model: AiChatSessionModel) -> ChatSession:
        return ChatSession(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            context=model.context,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_message_entity(self, model: AiChatMessageModel) -> ChatMessage:
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            metadata=model.message_metadata,
            created_at=model.created_at,
        )
