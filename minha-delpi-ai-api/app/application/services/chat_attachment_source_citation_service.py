"""Indicação de fonte quando a resposta usa anexo indexado — Playbook 05."""

from __future__ import annotations


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

        lowered_answer = str(answer or "").lower()

        if all(name.lower() in lowered_answer for name in filenames[:1]):
            return

        if len(filenames) == 1:
            note = f"Com base no arquivo **{filenames[0]}** anexado nesta conversa."
        else:
            joined = ", ".join(filenames[:3])
            note = f"Com base nos arquivos anexados: **{joined}**."

        metadata["attachmentSourceCitation"] = {
            "filenames": filenames[:5],
            "note": note,
        }
