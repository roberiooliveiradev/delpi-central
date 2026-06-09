"""Intenção de leitura de conteúdo em anexos (PDF/imagem) — skill document-vision-delpi."""

from __future__ import annotations

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatAttachmentDocumentIntentService:
    @classmethod
    def is_document_content_question(cls, message: str | None) -> bool:
        normalized = str(message or "").strip()
        min_length = ChatDocumentVisionContentService.min_message_length()

        if len(normalized) < min_length:
            return False

        patterns = (
            *ChatDocumentVisionContentService.read_content_patterns(),
            *ChatDocumentVisionContentService.describe_image_patterns(),
        )

        return any(pattern.search(normalized) for pattern in patterns)

    @classmethod
    def is_image_describe_question(cls, message: str | None) -> bool:
        normalized = str(message or "").strip()
        min_length = ChatDocumentVisionContentService.min_message_length()

        if len(normalized) < min_length:
            return False

        return any(
            pattern.search(normalized)
            for pattern in ChatDocumentVisionContentService.describe_image_patterns()
        )
