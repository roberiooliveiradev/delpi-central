"""Acesso lazy à fachada — evita import circular e preserva patches de teste."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.services.chat_document_vision_service import ChatDocumentVisionService


def vision_service() -> type[ChatDocumentVisionService]:
    from app.application.services.chat_document_vision_service import ChatDocumentVisionService

    return ChatDocumentVisionService
