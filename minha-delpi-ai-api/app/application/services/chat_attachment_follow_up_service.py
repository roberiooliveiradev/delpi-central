"""Sugestões após envio de anexo (Playbook 07 — anexos e arquivos)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

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


class ChatAttachmentFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        had_attachments: bool,
        attachments: list[dict] | None = None,
        message: str | None = None,
    ) -> None:
        if not had_attachments:
            return

        if attachments:
            summaries = ChatAttachmentPreviewService.summarize_attachments(attachments)

            if summaries:
                metadata["attachmentSummaries"] = summaries

        labels = list(
            _playbook().get("attachmentFollowUpChips")
            or [
                "Resumir",
                "Corrigir",
                "Traduzir",
                "Extrair pendências",
                "Criar checklist",
                "Colocar na lousa",
            ]
        )
        queries = dict(_playbook().get("attachmentFollowUpQueries") or {})

        if message:
            from app.domain.services.chat_text_task_intent_service import (
                ChatTextTaskIntentService,
            )

            category = ChatTextTaskIntentService.classify(message)

            extra_labels = (_playbook().get("attachmentTextTaskChips") or {}).get(category)

            if isinstance(extra_labels, list):
                for label in extra_labels:
                    if label not in labels:
                        labels.append(str(label))

        if attachments and len(attachments) >= 2 and "Comparar" not in labels:
            labels.append("Comparar")

        if attachments and ChatAttachmentLargeFileService.has_large_attachment(attachments):
            for label in ChatAttachmentLargeFileService.follow_up_labels():
                if label not in labels:
                    labels.insert(0, label)

        suggestions: list[dict[str, str]] = []

        for label in labels[:10]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        if suggestions:
            metadata["attachmentFollowUpSuggestions"] = suggestions
