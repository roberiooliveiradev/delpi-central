"""Indicação de fonte quando a resposta usa anexo indexado — Playbook 05."""

from __future__ import annotations

from app.domain.services.chat_attachment_content_service import ChatAttachmentContentService


class ChatAttachmentSourceCitationService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        attachments: list[dict] | None,
        answer: str,
    ) -> None:
        items = attachments if isinstance(attachments, list) else []
        indexed = [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("status") or "") == "indexed"
        ]

        if not indexed:
            return

        filenames = [
            str(item.get("original_filename") or "").strip()
            for item in indexed
            if str(item.get("original_filename") or "").strip()
        ]

        if not filenames:
            return

        if cls._should_skip_citation(answer=answer, filenames=filenames):
            return

        max_listed = ChatAttachmentContentService.source_citation_max_filenames_listed()
        max_stored = ChatAttachmentContentService.source_citation_max_filenames_stored()

        if len(filenames) == 1:
            note = ChatAttachmentContentService.source_citation_single(
                filename=filenames[0],
            )
        else:
            joined = ", ".join(filenames[:max_listed])
            note = ChatAttachmentContentService.source_citation_multiple(
                filenames=joined,
            )

        metadata["attachmentSourceCitation"] = {
            "filenames": filenames[:max_stored],
            "note": note,
        }

    @classmethod
    def _should_skip_citation(cls, *, answer: str, filenames: list[str]) -> bool:
        lowered_answer = str(answer or "").lower()

        if filenames and all(name.lower() in lowered_answer for name in filenames[:1]):
            return True

        from app.domain.services.chat_drawing_validation_content_service import (
            ChatDrawingValidationContentService,
        )

        report_title = ChatDrawingValidationContentService.get(
            "report",
            "title",
            default="",
        ).strip()

        if report_title and report_title in str(answer or ""):
            return True

        pdf_attached_label = ChatDrawingValidationContentService.get(
            "reportFields",
            "pdf",
            "attached",
            default="PDF anexado",
        ).strip()
        pdf_attached_yes = ChatDrawingValidationContentService.get(
            "reportFields",
            "pdf",
            "attachedYes",
            default="Sim",
        ).strip()

        if (
            pdf_attached_label.lower() in lowered_answer
            and pdf_attached_yes.lower() in lowered_answer
        ):
            return True

        return False
