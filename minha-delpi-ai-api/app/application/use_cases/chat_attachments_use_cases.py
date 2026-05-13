import os
import uuid
from pathlib import Path
from uuid import UUID

from werkzeug.utils import secure_filename

from app.application.dto.chat_attachment_response import ChatAttachmentResponse
from app.application.dto.create_chat_attachment_request import CreateChatAttachmentRequest
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
    InvalidChatSessionInputError,
)
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

MAX_ATTACHMENT_SIZE_BYTES = 25 * 1024 * 1024


def _attachment_to_response(attachment) -> ChatAttachmentResponse:
    return ChatAttachmentResponse(
        id=str(attachment.id),
        session_id=str(attachment.session_id),
        message_id=str(attachment.message_id) if attachment.message_id else None,
        project_id=str(attachment.project_id) if attachment.project_id else None,
        agent_key=attachment.agent_key,
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        content_type=attachment.content_type,
        size_bytes=attachment.size_bytes,
        status=attachment.status,
        metadata=attachment.metadata,
        created_at=attachment.created_at,
        updated_at=attachment.updated_at,
    )


class CreateChatAttachmentUseCase:
    def __init__(
        self,
        attachment_repository: ChatAttachmentRepositoryPort,
        session_repository: ChatSessionRepositoryPort,
        storage_root: str | None = None,
    ):
        self.attachment_repository = attachment_repository
        self.session_repository = session_repository
        self.storage_root = Path(
            storage_root
            or os.getenv("CHAT_ATTACHMENT_STORAGE_PATH")
            or "/tmp/minha-delpi-chat-attachments"
        )

    def execute(self, request: CreateChatAttachmentRequest) -> ChatAttachmentResponse:
        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)

        session = self.session_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        original_filename = self._validate_filename(request.original_filename)
        size_bytes = self._validate_size(request.size_bytes)
        content = self._validate_content(request.content, size_bytes)

        safe_name = secure_filename(original_filename) or "arquivo"
        extension = Path(safe_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidChatSessionInputError("File type is not allowed")

        storage_dir = self.storage_root / str(user_id) / str(session_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}{extension}"
        storage_path = storage_dir / filename
        storage_path.write_bytes(content)

        metadata = dict(request.metadata or {})
        metadata.update(
            {
                "extension": extension,
                "storage": "local",
                "indexed": False,
            }
        )

        attachment = self.attachment_repository.create_attachment(
            user_id=user_id,
            session_id=session_id,
            project_id=session.project_id,
            agent_key=session.agent_key,
            filename=filename,
            original_filename=original_filename,
            content_type=request.content_type,
            size_bytes=size_bytes,
            storage_path=str(storage_path),
            metadata=metadata,
        )

        return _attachment_to_response(attachment)

    def _validate_filename(self, value: str) -> str:
        if not isinstance(value, str):
            raise InvalidChatSessionInputError("Filename must be a string")

        normalized = value.strip()

        if not normalized:
            raise InvalidChatSessionInputError("Filename is required")

        if len(normalized) > 255:
            raise InvalidChatSessionInputError("Filename exceeds maximum length")

        return normalized

    def _validate_size(self, value: int) -> int:
        if not isinstance(value, int):
            raise InvalidChatSessionInputError("File size must be an integer")

        if value <= 0:
            raise InvalidChatSessionInputError("File is empty")

        if value > MAX_ATTACHMENT_SIZE_BYTES:
            raise InvalidChatSessionInputError("File exceeds maximum size")

        return value

    def _validate_content(self, value: bytes, size_bytes: int) -> bytes:
        if not isinstance(value, bytes):
            raise InvalidChatSessionInputError("File content is required")

        if len(value) != size_bytes:
            raise InvalidChatSessionInputError("File size mismatch")

        return value


class ListChatAttachmentsUseCase:
    def __init__(
        self,
        attachment_repository: ChatAttachmentRepositoryPort,
        session_repository: ChatSessionRepositoryPort,
    ):
        self.attachment_repository = attachment_repository
        self.session_repository = session_repository

    def execute(self, *, user_id: str, session_id: str) -> list[ChatAttachmentResponse]:
        user_uuid = UUID(user_id)
        session_uuid = UUID(session_id)

        session = self.session_repository.get_session_by_id(session_uuid)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_uuid:
            raise ChatSessionAccessDeniedError()

        attachments = self.attachment_repository.list_session_attachments(
            user_id=user_uuid,
            session_id=session_uuid,
        )

        return [_attachment_to_response(attachment) for attachment in attachments]


class DeleteChatAttachmentUseCase:
    def __init__(self, attachment_repository: ChatAttachmentRepositoryPort):
        self.attachment_repository = attachment_repository

    def execute(self, *, user_id: str, attachment_id: str) -> bool:
        return self.attachment_repository.delete_attachment(
            user_id=UUID(user_id),
            attachment_id=UUID(attachment_id),
        )
