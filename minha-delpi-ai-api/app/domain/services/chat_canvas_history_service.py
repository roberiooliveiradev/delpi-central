"""Leitura de lousa (canvas) a partir do histórico de mensagens."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_attachment_content_service import ChatAttachmentContentService


class ChatCanvasHistoryService:
    @classmethod
    def find_active_canvas(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str, str, str | None]:
        """Markdown, título e sourceMessageId da lousa mais recente no histórico."""
        if not previous_messages:
            return "", ChatAttachmentContentService.canvas_default_title(), None

        for message in reversed(previous_messages):
            metadata = cls._message_metadata(message)
            canvas_open = metadata.get("canvasOpen") if isinstance(metadata, dict) else None

            if not isinstance(canvas_open, dict):
                continue

            markdown = str(canvas_open.get("markdown") or "").strip()

            if not markdown:
                continue

            title = str(canvas_open.get("title") or "").strip() or cls._derive_title(markdown)
            source_message_id = canvas_open.get("sourceMessageId") or canvas_open.get(
                "source_message_id"
            )

            return markdown, title, (
                str(source_message_id) if source_message_id is not None else None
            )

        return "", ChatAttachmentContentService.canvas_default_title(), None

    @classmethod
    def _derive_title(cls, markdown: str) -> str:
        for line in markdown.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                return (
                    stripped.lstrip("#").strip()[:80]
                    or ChatAttachmentContentService.canvas_default_title()
                )

            plain = stripped.replace("**", "").replace("*", "").strip()

            if plain:
                return plain[:80]

        return ChatAttachmentContentService.canvas_default_title()

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        metadata = getattr(message, "metadata", None)

        if metadata is None and isinstance(message, dict):
            metadata = message.get("metadata")

        return metadata if isinstance(metadata, dict) else {}
