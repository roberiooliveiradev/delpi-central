from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat_attachment import ChatAttachment


class ChatAttachmentRepositoryPort(ABC):
    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def list_session_attachments(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> list[ChatAttachment]:
        raise NotImplementedError

    @abstractmethod
    def list_attachments_by_ids(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attachment_ids: list[UUID],
    ) -> list[ChatAttachment]:
        raise NotImplementedError

    @abstractmethod
    def attach_to_message(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attachment_ids: list[UUID],
        message_id: UUID,
    ) -> list[ChatAttachment]:
        raise NotImplementedError

    @abstractmethod
    def update_status(
        self,
        *,
        attachment_id: UUID,
        status: str,
        metadata: dict | None = None,
    ) -> ChatAttachment | None:
        raise NotImplementedError

    @abstractmethod
    def delete_attachment(
        self,
        *,
        user_id: UUID,
        attachment_id: UUID,
    ) -> bool:
        raise NotImplementedError
