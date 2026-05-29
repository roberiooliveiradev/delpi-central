import mimetypes
from pathlib import Path
from uuid import UUID

from app.application.dto.download_file_result import DownloadFileResult
from app.application.use_cases.chat_sources_use_cases import DeleteChatSourceUseCase
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.services.agent_knowledge_filename_service import AgentKnowledgeFilenameService


class DownloadChatAttachmentUseCase:
    def __init__(self, attachment_repository: ChatAttachmentRepositoryPort):
        self.attachment_repository = attachment_repository

    def execute(self, *, user_id: str, attachment_id: str) -> DownloadFileResult:
        attachment = self.attachment_repository.get_attachment_by_id(
            user_id=UUID(user_id),
            attachment_id=UUID(attachment_id),
        )

        if not attachment:
            raise ChatSessionNotFoundError("Attachment not found")

        storage_path = Path(attachment.storage_path)

        if not storage_path.is_file():
            raise FileNotFoundError("Attachment file is missing on storage")

        content = storage_path.read_bytes()
        filename = attachment.original_filename or attachment.filename
        content_type = attachment.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        return DownloadFileResult(
            content=content,
            filename=filename,
            content_type=content_type,
        )


class DownloadChatSourceUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        access_checker: DeleteChatSourceUseCase,
    ):
        self.knowledge_repository = knowledge_repository
        self.access_checker = access_checker

    def execute(self, *, user_id: str, source_id: str) -> DownloadFileResult:
        document = self.knowledge_repository.get_document_by_id(UUID(source_id))

        if not document:
            raise ChatSessionNotFoundError("Source not found")

        metadata = document.metadata or {}

        if not self.access_checker._can_delete(user_id=user_id, metadata=metadata):
            raise ChatSessionAccessDeniedError()

        original_filename = (
            metadata.get("originalFilename")
            or document.title
            or f"fonte-{source_id}.md"
        )
        filename = AgentKnowledgeFilenameService.normalize(
            original_filename,
            title=document.title,
        )

        storage_path = metadata.get("storagePath") or document.source_ref
        path = Path(str(storage_path)) if storage_path else None

        if path and path.is_file():
            content = path.read_bytes()
            content_type = metadata.get("contentType") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        else:
            text = str(document.content or "").strip()
            if not text:
                raise FileNotFoundError("Source content is unavailable")

            if not Path(filename).suffix:
                filename = f"{filename}.md"

            content = text.encode("utf-8")
            content_type = metadata.get("contentType") or "text/markdown; charset=utf-8"

        return DownloadFileResult(
            content=content,
            filename=filename,
            content_type=content_type,
        )
