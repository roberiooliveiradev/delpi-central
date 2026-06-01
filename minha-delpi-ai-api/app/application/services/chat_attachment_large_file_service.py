"""Arquivos extensos — Playbook 05 §8."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService

_LARGE_CHAR_THRESHOLD = 120_000
_LARGE_PAGE_THRESHOLD = 40


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


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

        if isinstance(char_count, int) and char_count >= _LARGE_CHAR_THRESHOLD:
            return True

        page_limit = preview.get("pageLimit")

        if isinstance(page_limit, int) and page_limit >= _LARGE_PAGE_THRESHOLD:
            return True

        return False

    @classmethod
    def has_large_attachment(cls, attachments: list[dict] | None) -> bool:
        return any(cls.is_large_attachment(item) for item in (attachments or []))

    @classmethod
    def format_notice(cls) -> str | None:
        block = _playbook().get("attachmentLargeFile") or {}

        if not isinstance(block, dict):
            return None

        body = str(block.get("body") or "").strip()

        return body or None

    @classmethod
    def follow_up_labels(cls) -> list[str]:
        block = _playbook().get("attachmentLargeFile") or {}
        chips = block.get("chips")

        if isinstance(chips, list) and chips:
            return [str(item).strip() for item in chips if str(item).strip()]

        return [
            "Resumo geral",
            "Trabalhar por seção",
            "Extrair pendências",
            "Procurar termo",
            "Criar checklist",
            "Colocar na lousa",
        ]
