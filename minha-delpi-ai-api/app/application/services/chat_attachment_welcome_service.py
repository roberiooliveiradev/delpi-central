"""Resposta automática ao enviar anexo (Playbook 07)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.application.services.chat_attachment_large_file_service import (
    ChatAttachmentLargeFileService,
)
from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)


class ChatAttachmentWelcomeService:
    @classmethod
    def should_welcome(cls, message: str, *, attachment_ids: list | None) -> bool:
        if not attachment_ids:
            return False

        raw = str(message or "").strip()

        if not raw:
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        if (
            len(normalized) <= ChatAttachmentContentService.max_handoff_message_length()
            and ChatAttachmentContentService.handoff_pattern().search(normalized)
        ):
            return True

        if normalized in ChatAttachmentContentService.short_ack_messages():
            return True

        return False

    @classmethod
    def build_direct_answer(cls, *, attachments: list[dict] | None) -> str | None:
        block = ChatAttachmentContentService.welcome_block()

        if not block:
            return None

        title = str(block.get("title") or "").strip()
        intro = str(block.get("intro") or "").strip()
        bullets = block.get("bullets") or []
        hint = str(block.get("hint") or "").strip()
        bullet_suffix = str(block.get("bulletSuffix") or ";").strip() or ";"

        if not title or not intro:
            return None

        names: list[str] = []

        for item in attachments or []:
            if not isinstance(item, dict):
                continue

            name = str(
                item.get("original_filename")
                or item.get("filename")
                or ""
            ).strip()

            if name and name not in names:
                names.append(name)

        files_line = ""

        if names:
            if len(names) == 1:
                single_label = str(block.get("filesSingleLabel") or "Arquivo").strip()
                files_line = f"\n\n**{single_label}:** {names[0]}"
            else:
                multiple_label = str(block.get("filesMultipleLabel") or "Arquivos").strip()
                listed = "\n".join(f"- {name}" for name in names[:5])
                files_line = f"\n\n**{multiple_label}:**\n{listed}"

        reading_line = ChatAttachmentPreviewService.format_reading_lines(attachments)

        bullet_lines = "\n".join(
            f"- {str(item).strip().rstrip('.')}{bullet_suffix}"
            for item in bullets[:8]
            if str(item).strip()
        )

        parts = [title, "", intro + files_line]

        if reading_line:
            parts.append(reading_line)

        if ChatAttachmentLargeFileService.has_large_attachment(attachments):
            large_notice = ChatAttachmentLargeFileService.format_notice()

            if large_notice:
                parts.extend(["", large_notice])

        unreadable = [
            item
            for item in (attachments or [])
            if isinstance(item, dict)
            and str(item.get("status") or "") in {"unsupported", "index_failed"}
        ]

        if unreadable and len(unreadable) == len(list(attachments or [])):
            unreadable_body = ChatAttachmentContentService.unreadable_body()

            if unreadable_body:
                parts.extend(["", unreadable_body])

        parts.extend(["", bullet_lines, "", hint])

        return "\n".join(parts).strip()
