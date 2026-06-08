"""Arquivos extensos — Playbook 05 §8."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)


class ChatAttachmentLargeFileService:
    @classmethod
    def is_large_attachment(cls, attachment: dict) -> bool:
        if not isinstance(attachment, dict):
            return False

        meta = attachment.get("metadata")

        if not isinstance(meta, dict):
            return False

        preview = meta.get("preview")

        if not isinstance(preview, dict):
            return False

        char_count = preview.get("charCount")
        char_threshold = ChatAttachmentContentService.large_file_char_threshold()

        if isinstance(char_count, int) and char_count >= char_threshold:
            return True

        page_limit = preview.get("pageLimit")
        page_threshold = ChatAttachmentContentService.large_file_page_threshold()

        if isinstance(page_limit, int) and page_limit >= page_threshold:
            return True

        return False

    @classmethod
    def has_large_attachment(cls, attachments: list[dict] | None) -> bool:
        return any(cls.is_large_attachment(item) for item in (attachments or []))

    @classmethod
    def format_notice(cls) -> str | None:
        block = ChatAttachmentContentService.large_file_block()
        body = str(block.get("body") or "").strip()

        return body or None

    @classmethod
    def follow_up_labels(cls) -> list[str]:
        block = ChatAttachmentContentService.large_file_block()
        chips = block.get("chips")

        if isinstance(chips, list) and chips:
            return [str(item).strip() for item in chips if str(item).strip()]

        return ChatAttachmentContentService.follow_up_chips()[:6]
