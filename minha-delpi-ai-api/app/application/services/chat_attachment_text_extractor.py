"""Fachada de extração de anexos — delega ao pipeline canônico de workspace."""

from __future__ import annotations

from app.application.services.chat_workspace_file_text_extraction_service import (
    ChatWorkspaceFileTextExtractionService,
)


class ChatAttachmentTextExtractor:
    SUPPORTED_TEXT_EXTENSIONS = ChatWorkspaceFileTextExtractionService.SUPPORTED_TEXT_EXTENSIONS
    SUPPORTED_OPTIONAL_EXTENSIONS = (
        ChatWorkspaceFileTextExtractionService.SUPPORTED_OFFICE_EXTENSIONS
        | ChatWorkspaceFileTextExtractionService.SUPPORTED_DOCUMENT_EXTENSIONS
    )
    SUPPORTED_IMAGE_EXTENSIONS = ChatWorkspaceFileTextExtractionService.SUPPORTED_IMAGE_EXTENSIONS

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return ChatWorkspaceFileTextExtractionService.supported_extensions()

    def extract(
        self,
        *,
        storage_path: str,
        filename: str,
        content_type: str | None,
        pdf_page_limit: int | None = None,
    ) -> dict:
        return ChatWorkspaceFileTextExtractionService.extract(
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            pdf_page_limit=pdf_page_limit,
        )
