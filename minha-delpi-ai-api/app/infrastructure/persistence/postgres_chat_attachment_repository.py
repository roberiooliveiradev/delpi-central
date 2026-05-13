from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.chat_attachment import ChatAttachment
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.chat_attachment_model import AiChatAttachmentModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class PostgresChatAttachmentRepository(ChatAttachmentRepositoryPort):
    def create_attachment(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        project_id: UUID | None,
        agent_key: str | None,
        filename: str,
        original_filename: str,
        content_type: str | None,
        size_bytes: int,
        storage_path: str,
        metadata: dict | None = None,
    ) -> ChatAttachment:
        model = AiChatAttachmentModel(
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            agent_key=agent_key,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            attachment_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_entity(model)

    def list_session_attachments(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> list[ChatAttachment]:
        models = (
            AiChatAttachmentModel.query
            .filter(AiChatAttachmentModel.user_id == user_id)
            .filter(AiChatAttachmentModel.session_id == session_id)
            .order_by(AiChatAttachmentModel.created_at.asc())
            .all()
        )

        return [self._to_entity(model) for model in models]

    def list_attachments_by_ids(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attachment_ids: list[UUID],
    ) -> list[ChatAttachment]:
        if not attachment_ids:
            return []

        models = (
            AiChatAttachmentModel.query
            .filter(AiChatAttachmentModel.user_id == user_id)
            .filter(AiChatAttachmentModel.session_id == session_id)
            .filter(AiChatAttachmentModel.id.in_(attachment_ids))
            .all()
        )

        return [self._to_entity(model) for model in models]

    def attach_to_message(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attachment_ids: list[UUID],
        message_id: UUID,
    ) -> list[ChatAttachment]:
        if not attachment_ids:
            return []

        now = datetime.now(timezone.utc)

        models = (
            AiChatAttachmentModel.query
            .filter(AiChatAttachmentModel.user_id == user_id)
            .filter(AiChatAttachmentModel.session_id == session_id)
            .filter(AiChatAttachmentModel.id.in_(attachment_ids))
            .all()
        )

        for model in models:
            model.message_id = message_id
            model.updated_at = now

        db.session.flush()

        return [self._to_entity(model) for model in models]


    def update_status(
        self,
        *,
        attachment_id: UUID,
        status: str,
        metadata: dict | None = None,
    ) -> ChatAttachment | None:
        model = AiChatAttachmentModel.query.filter(
            AiChatAttachmentModel.id == attachment_id
        ).first()

        if not model:
            return None

        model.status = status
        model.updated_at = datetime.now(timezone.utc)

        if metadata is not None:
            next_metadata = dict(model.attachment_metadata or {})
            next_metadata.update(metadata)
            model.attachment_metadata = next_metadata

        db.session.flush()

        return self._to_entity(model)

    def delete_attachment(
        self,
        *,
        user_id: UUID,
        attachment_id: UUID,
    ) -> bool:
        model = (
            AiChatAttachmentModel.query
            .filter(AiChatAttachmentModel.user_id == user_id)
            .filter(AiChatAttachmentModel.id == attachment_id)
            .first()
        )

        if not model:
            return False

        db.session.delete(model)
        db.session.flush()

        return True

    def _to_entity(self, model: AiChatAttachmentModel) -> ChatAttachment:
        return ChatAttachment(
            id=model.id,
            user_id=model.user_id,
            session_id=model.session_id,
            message_id=model.message_id,
            project_id=model.project_id,
            agent_key=model.agent_key,
            filename=model.filename,
            original_filename=model.original_filename,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
            storage_path=model.storage_path,
            status=model.status,
            metadata=model.attachment_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
