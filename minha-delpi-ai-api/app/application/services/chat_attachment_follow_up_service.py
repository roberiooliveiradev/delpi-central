"""Sugestões após envio de anexo (Playbook 07 — anexos e arquivos)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_attachment_large_file_service import (
    ChatAttachmentLargeFileService,
)
from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)


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

        labels = list(ChatAttachmentContentService.follow_up_chips())
        queries = ChatAttachmentContentService.follow_up_queries()

        if message:
            from app.domain.services.chat_text_task_intent_service import (
                ChatTextTaskIntentService,
            )

            category = ChatTextTaskIntentService.classify(message)

            extra_labels = ChatAttachmentContentService.text_task_chips(category)

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
