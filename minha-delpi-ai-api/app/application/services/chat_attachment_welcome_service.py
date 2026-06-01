"""Resposta automática ao enviar anexo (Playbook 07)."""

from __future__ import annotations

import re
from functools import lru_cache
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
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatAttachmentWelcomeService:
    _HANDOFF_RE = re.compile(
        r"^(?:segue|anexo|arquivo|em anexo|veja (?:o )?anexo|conforme anexo)\b",
        re.IGNORECASE,
    )

    @classmethod
    def should_welcome(cls, message: str, *, attachment_ids: list | None) -> bool:
        if not attachment_ids:
            return False

        raw = str(message or "").strip()

        if not raw:
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        if len(normalized) <= 48 and cls._HANDOFF_RE.search(normalized):
            return True

        if normalized in {
            "ok",
            "pronto",
            "enviado",
            "segue",
            "anexo",
            "arquivo",
            "veja o anexo",
            "em anexo",
        }:
            return True

        return False

    @classmethod
    def build_direct_answer(cls, *, attachments: list[dict] | None) -> str | None:
        block = _playbook().get("attachmentWelcome") or {}

        if not isinstance(block, dict):
            return None

        title = str(block.get("title") or "Arquivo recebido.").strip()
        intro = str(
            block.get("intro")
            or "Posso ajudar com o conteúdo anexado nesta mensagem."
        ).strip()
        bullets = block.get("bullets") or [
            "resumo",
            "correção de texto",
            "tradução",
            "extração de pendências",
            "checklist",
            "análise dos dados",
        ]
        hint = str(
            block.get("hint")
            or "Escolha uma ação nos chips abaixo ou descreva o que precisa."
        ).strip()

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
                files_line = f"\n\n**Arquivo:** {names[0]}"
            else:
                listed = "\n".join(f"- {name}" for name in names[:5])
                files_line = f"\n\n**Arquivos:**\n{listed}"

        reading_line = ChatAttachmentPreviewService.format_reading_lines(attachments)

        bullet_lines = "\n".join(
            f"- {str(item).strip().rstrip('.')};" for item in bullets[:8]
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
            block = _playbook().get("attachmentUnreadable") or {}
            unreadable_body = str(block.get("body") or "").strip()

            if unreadable_body:
                parts.extend(["", unreadable_body])

        parts.extend(["", bullet_lines, "", hint])

        return "\n".join(parts).strip()
