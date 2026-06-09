"""Enriquecimento da resposta de upload/listagem de anexos (Playbook 07)."""

from __future__ import annotations

from typing import Any

from app.application.dto.chat_attachment_response import ChatAttachmentResponse
from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)


class ChatAttachmentResponseService:
    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any] | None,
        *,
        status: str,
    ) -> dict[str, Any]:
        meta = dict(metadata or {})
        preview = meta.get("preview") if isinstance(meta.get("preview"), dict) else None
        indexed = str(status or "") == "indexed" or bool(meta.get("indexed"))
        parsed = indexed and bool(preview)

        meta["readingStatus"] = ChatAttachmentPreviewService.reading_status_label(
            status=status,
            parsed=parsed,
            index_reason=meta.get("indexReason"),
            metadata=meta,
        )

        if preview:
            meta["preview"] = preview

        document_vision = meta.get("documentVision")

        if isinstance(document_vision, dict) and document_vision:
            meta["documentVisionSummary"] = ChatAttachmentPreviewService.document_vision_summary(
                document_vision,
            )

        return meta

    @classmethod
    def to_response(cls, attachment) -> ChatAttachmentResponse:
        status = str(getattr(attachment, "status", None) or "uploaded")
        metadata = cls.enrich_metadata(
            getattr(attachment, "metadata", None),
            status=status,
        )

        return ChatAttachmentResponse(
            id=str(attachment.id),
            session_id=str(attachment.session_id),
            message_id=str(attachment.message_id) if attachment.message_id else None,
            project_id=str(attachment.project_id) if attachment.project_id else None,
            agent_id=str(attachment.agent_id) if attachment.agent_id else None,
            filename=attachment.filename,
            original_filename=attachment.original_filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            status=status,
            metadata=metadata,
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
        )
