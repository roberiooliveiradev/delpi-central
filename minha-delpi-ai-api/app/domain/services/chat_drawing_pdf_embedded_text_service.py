"""Compatibilidade — delega para ChatPdfEmbeddedTextService (chat base)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_pdf_embedded_text_service import ChatPdfEmbeddedTextService


class ChatDrawingPdfEmbeddedTextService:
    @classmethod
    def extract(
        cls,
        storage_path: str,
        *,
        page_limit: int | None = None,
    ) -> dict[str, Any]:
        return ChatPdfEmbeddedTextService.extract(
            storage_path,
            page_limit=page_limit,
        )
