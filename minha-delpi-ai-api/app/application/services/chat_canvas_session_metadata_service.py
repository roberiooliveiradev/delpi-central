"""Metadata de sessão da lousa — Playbook 05 §13–§14."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_canvas_content_service import ChatCanvasOpenPayload


class ChatCanvasSessionMetadataService:
    @classmethod
    def attach_open(
        cls,
        metadata: dict,
        *,
        open_payload: ChatCanvasOpenPayload,
        operation: str,
        previous_messages: list[Any] | None = None,
    ) -> None:
        version = cls._next_version(previous_messages) + 1
        document_type = cls._infer_document_type(open_payload.markdown)

        metadata["canvas"] = {
            "active": True,
            "title": str(open_payload.title or "Lousa").strip(),
            "documentType": document_type,
            "version": version,
            "lastOperation": str(operation or "open").strip(),
            "sourceMessageId": open_payload.source_message_id,
            "lastUpdatedFromMessageId": open_payload.source_message_id,
        }

        metadata["canvasVersion"] = {
            "version": version,
            "operation": str(operation or "open").strip(),
            "sourceMessageId": open_payload.source_message_id,
        }

    @classmethod
    def _next_version(cls, previous_messages: list[Any] | None) -> int:
        highest = 0

        for message in previous_messages or []:
            metadata = (
                getattr(message, "metadata", None)
                if not isinstance(message, dict)
                else message.get("metadata")
            )

            if not isinstance(metadata, dict):
                continue

            canvas = metadata.get("canvas")

            if isinstance(canvas, dict):
                token = canvas.get("version")

                if isinstance(token, int) and token > highest:
                    highest = token

            canvas_open = metadata.get("canvasOpen")

            if isinstance(canvas_open, dict):
                token = canvas_open.get("version")

                if isinstance(token, int) and token > highest:
                    highest = token

        return highest

    @classmethod
    def _infer_document_type(cls, markdown: str) -> str:
        lowered = str(markdown or "").lower()

        if "checklist" in lowered or "- [ ]" in markdown:
            return "checklist"

        if "ata de" in lowered or "## decis" in lowered:
            return "minutes"

        if "comunicado" in lowered:
            return "announcement"

        if "plano de ação" in lowered or "plano de acao" in lowered:
            return "action_plan"

        if "relatório" in lowered or "relatorio" in lowered:
            return "report"

        return "document"
