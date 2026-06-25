"""Seleção de anexo PDF/imagem para visão de documentos e desenhos."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar
from uuid import UUID

from app.domain.entities.chat_attachment import ChatAttachment
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatAttachmentDocumentSelectionService:
    _repository_loader: ClassVar[Callable[[], ChatAttachmentRepositoryPort] | None] = None

    @classmethod
    def configure(cls, loader: Callable[[], ChatAttachmentRepositoryPort]) -> None:
        cls._repository_loader = loader

    @classmethod
    def _repository(cls) -> ChatAttachmentRepositoryPort:
        if cls._repository_loader is None:
            raise RuntimeError(
                "ChatAttachmentRepositoryPort não configurado — "
                "chame configure_domain_persistence_ports()"
            )

        return cls._repository_loader()

    @classmethod
    def resolve_first_document_attachment(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ) -> ChatAttachment | None:
        attachments = cls.list_attachments(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachments:
            return None

        image_match = None

        for attachment in attachments:
            name = str(attachment.original_filename or "").lower()
            content_type = str(attachment.content_type or "").lower()

            if cls.is_pdf(content_type, name):
                return attachment

            if image_match is None and cls.is_image(content_type, name):
                image_match = attachment

        return image_match

    @classmethod
    def list_attachments(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ) -> list[ChatAttachment]:
        if not user_id or not session_id or not attachment_ids:
            return []

        try:
            ids: list[UUID] = []

            for raw in attachment_ids:
                try:
                    ids.append(UUID(str(raw)))
                except (TypeError, ValueError):
                    continue

            if not ids:
                return []

            return cls._repository().list_attachments_by_ids(
                user_id=UUID(str(user_id)),
                session_id=UUID(str(session_id)),
                attachment_ids=ids,
            )
        except Exception:
            return []

    @classmethod
    def is_pdf(cls, content_type: str, filename: str) -> bool:
        lowered = f"{content_type} {filename}".lower()

        return "pdf" in lowered or lowered.endswith(".pdf")

    @classmethod
    def is_image(cls, content_type: str, filename: str) -> bool:
        lowered = f"{content_type} {filename}".lower()

        for extension in ChatDocumentVisionContentService.image_extensions():
            token = str(extension or "").strip().lower()

            if token and token in lowered:
                return True

        for prefix in ChatDocumentVisionContentService.document_mime_prefixes():
            token = str(prefix or "").strip().lower()

            if token.startswith("image/") and token in lowered:
                return True

        return False
