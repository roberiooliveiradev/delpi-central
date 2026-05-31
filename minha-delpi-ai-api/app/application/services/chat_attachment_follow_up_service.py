"""Sugestões após envio de anexo (Playbook 07 — anexos e arquivos)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatAttachmentFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        had_attachments: bool,
        attachments: list[dict] | None = None,
    ) -> None:
        if not had_attachments:
            return

        if attachments:
            summaries = ChatAttachmentPreviewService.summarize_attachments(attachments)

            if summaries:
                metadata["attachmentSummaries"] = summaries

        labels = _playbook().get("attachmentFollowUpChips") or [
            "Resumir",
            "Corrigir",
            "Traduzir",
            "Extrair pendências",
        ]
        queries = _playbook().get("attachmentFollowUpQueries") or {}

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        if suggestions:
            metadata["attachmentFollowUpSuggestions"] = suggestions
