from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
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
        project_id: UUID | None = None,
        agent_id: UUID | None = None,
    ) -> ChatSession:
        model = AiChatSessionModel(
            user_id=user_id,
            title=title,
            context=context,
            project_id=project_id,
            agent_id=agent_id,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_session_entity(model)

    def list_sessions_by_user(
        self,
        user_id: UUID,
        archived: bool = False,
    ) -> list[ChatSession]:
        query = AiChatSessionModel.query.filter(
            AiChatSessionModel.user_id == user_id
        )

        if archived:
            query = query.filter(AiChatSessionModel.archived_at.isnot(None))
        else:
            query = query.filter(AiChatSessionModel.archived_at.is_(None))

        models = (
            query
            .order_by(
                AiChatSessionModel.is_pinned.desc(),
                AiChatSessionModel.pinned_at.desc().nullslast(),
                AiChatSessionModel.updated_at.desc(),
            )
            .all()
        )

        return [self._to_session_entity(model) for model in models]


    def rename_session(
        self,
        session_id: UUID,
        user_id: UUID,
        title: str,
    ) -> ChatSession | None:
        model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        model.title = title
        model.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_session_entity(model)

    def update_session_agent_id(
        self,
        session_id: UUID,
        user_id: UUID,
        agent_id: UUID | None,
    ) -> bool:
        model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not model:
            return False

        model.agent_id = agent_id
        model.updated_at = datetime.now(timezone.utc)
        db.session.flush()

        return True

    def get_session_by_id(self, session_id: UUID) -> ChatSession | None:
        model = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == session_id
        ).first()

        if not model:
            return None

        return self._to_session_entity(model)


    def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not model:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def set_session_pinned(
        self,
        session_id: UUID,
        user_id: UUID,
        pinned: bool,
    ) -> ChatSession | None:
        model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .filter(AiChatSessionModel.archived_at.is_(None))
            .first()
        )

        if not model:
            return None

        now = datetime.now(timezone.utc)
        model.is_pinned = pinned
        model.pinned_at = now if pinned else None
        model.updated_at = now

        db.session.flush()

        return self._to_session_entity(model)

    def set_session_archived(
        self,
        session_id: UUID,
        user_id: UUID,
        archived: bool,
    ) -> ChatSession | None:
        model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        now = datetime.now(timezone.utc)
        model.archived_at = now if archived else None
        model.updated_at = now

        if archived:
            model.is_pinned = False
            model.pinned_at = None

        db.session.flush()

        return self._to_session_entity(model)

    def update_user_message(
        self,
        message_id: UUID,
        user_id: UUID,
        content: str,
        metadata_patch: dict | None = None,
    ) -> ChatMessage | None:
        model = (
            AiChatMessageModel.query
            .join(AiChatSessionModel, AiChatSessionModel.id == AiChatMessageModel.session_id)
            .filter(AiChatMessageModel.id == message_id)
            .filter(AiChatMessageModel.role == "user")
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not model:
            return None

        model.content = content

        metadata = dict(model.message_metadata or {})
        metadata["edited"] = True
        metadata.update(metadata_patch or {})
        if "editMode" not in metadata:
            metadata["editMode"] = "manual"
        model.message_metadata = metadata

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == model.session_id
        ).first()

        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_message_entity(model)

    def get_user_message_for_user(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
        session_id: UUID | None = None,
    ) -> ChatMessage | None:
        query = (
            AiChatMessageModel.query.join(
                AiChatSessionModel,
                AiChatSessionModel.id == AiChatMessageModel.session_id,
            )
            .filter(AiChatMessageModel.id == message_id)
            .filter(AiChatMessageModel.role == "user")
            .filter(AiChatSessionModel.user_id == user_id)
        )

        if session_id is not None:
            query = query.filter(AiChatMessageModel.session_id == session_id)

        model = query.first()

        if not model:
            return None

        return self._to_message_entity(model)

    def delete_messages_after(
        self,
        *,
        session_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> int:
        anchor = self.get_user_message_for_user(
            message_id=message_id,
            user_id=user_id,
            session_id=session_id,
        )

        if not anchor:
            return 0

        anchor_model = AiChatMessageModel.query.filter_by(id=message_id).first()

        if not anchor_model:
            return 0

        deleted = (
            AiChatMessageModel.query.filter(
                AiChatMessageModel.session_id == session_id,
                AiChatMessageModel.created_at > anchor_model.created_at,
            ).delete(synchronize_session=False)
        )

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == session_id,
            AiChatSessionModel.user_id == user_id,
        ).first()

        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return int(deleted or 0)

    def list_all_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        models = (
            AiChatMessageModel.query
            .filter(AiChatMessageModel.session_id == session_id)
            .order_by(AiChatMessageModel.created_at.asc(), AiChatMessageModel.id.asc())
            .all()
        )

        return [self._to_message_entity(model) for model in models]

    def list_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == session_id
        ).first()

        if not session:
            return []

        all_messages = self.list_all_messages_by_session(session_id)

        return ChatMessageBranchService.build_active_path(
            all_messages,
            session.active_leaf_message_id,
        )

    def get_message_by_id(
        self,
        message_id: UUID,
        *,
        user_id: UUID | None = None,
    ) -> ChatMessage | None:
        query = AiChatMessageModel.query.filter(AiChatMessageModel.id == message_id)

        if user_id is not None:
            query = query.join(
                AiChatSessionModel,
                AiChatSessionModel.id == AiChatMessageModel.session_id,
            ).filter(AiChatSessionModel.user_id == user_id)

        model = query.first()

        if not model:
            return None

        return self._to_message_entity(model)

    def set_active_leaf_message_id(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        message_id: UUID,
    ) -> ChatSession | None:
        session_model = (
            AiChatSessionModel.query
            .filter(AiChatSessionModel.id == session_id)
            .filter(AiChatSessionModel.user_id == user_id)
            .first()
        )

        if not session_model:
            return None

        message = self.get_message_by_id(message_id, user_id=user_id)

        if not message or message.session_id != session_id:
            return None

        session_model.active_leaf_message_id = message_id
        session_model.updated_at = datetime.now(timezone.utc)
        db.session.flush()

        return self._to_session_entity(session_model)

    def create_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: dict | None = None,
        parent_message_id: UUID | None = None,
    ) -> ChatMessage:
        model = AiChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata,
            parent_message_id=parent_message_id,
        )

        db.session.add(model)

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == session_id
        ).first()

        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_message_entity(model)

    def patch_message_metadata(
        self,
        message_id: UUID,
        metadata_patch: dict | None = None,
    ) -> ChatMessage | None:
        if not metadata_patch:
            return None

        model = AiChatMessageModel.query.filter(
            AiChatMessageModel.id == message_id,
        ).first()

        if not model:
            return None

        metadata = dict(model.message_metadata or {})
        metadata.update(metadata_patch)
        model.message_metadata = metadata

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == model.session_id
        ).first()

        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_message_entity(model)

    def update_assistant_message(
        self,
        message_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> ChatMessage | None:
        model = AiChatMessageModel.query.filter(
            AiChatMessageModel.id == message_id,
            AiChatMessageModel.role == "assistant",
        ).first()

        if not model:
            return None

        model.content = content
        model.message_metadata = metadata

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == model.session_id
        ).first()

        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_message_entity(model)

    def _to_session_entity(self, model: AiChatSessionModel) -> ChatSession:
        return ChatSession(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            context=model.context,
            project_id=model.project_id,
            agent_id=model.agent_id,
            is_pinned=bool(model.is_pinned),
            pinned_at=model.pinned_at,
            archived_at=model.archived_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            active_leaf_message_id=model.active_leaf_message_id,
        )

    def _to_message_entity(self, model: AiChatMessageModel) -> ChatMessage:
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            metadata=model.message_metadata,
            created_at=model.created_at,
            parent_message_id=model.parent_message_id,
        )
