"""Telemetria leve de anexos e lousa — Playbook 05 Fase 5."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("minha-delpi-ai-api.artifact")


class ChatAttachmentArtifactTelemetryService:
    @classmethod
    def attach_attachment_welcome(
        cls,
        metadata: dict,
        *,
        attachments: list[dict] | None,
    ) -> None:
        items = attachments if isinstance(attachments, list) else []

        if not items:
            return

        filenames = [
            str(item.get("original_filename") or item.get("filename") or "").strip()
            for item in items
            if isinstance(item, dict)
        ]
        filenames = [name for name in filenames if name]
        statuses = [
            str(item.get("status") or "").strip()
            for item in items
            if isinstance(item, dict)
        ]

        payload: dict[str, Any] = {
            "kind": "attachment",
            "count": len(items),
            "filenames": filenames[:5],
            "statuses": statuses[:5],
        }

        metadata["attachmentArtifact"] = payload

        logger.info(
            "attachment_welcome count=%s statuses=%s",
            payload["count"],
            ",".join(statuses[:3]) or "unknown",
        )

    @classmethod
    def attach_canvas_open(
        cls,
        metadata: dict,
        *,
        operation: str,
        document_type: str | None = None,
    ) -> None:
        canvas = metadata.get("canvas") if isinstance(metadata.get("canvas"), dict) else {}
        version = canvas.get("version")
        canvas_version = metadata.get("canvasVersion")
        operation_token = str(operation or "open").strip()

        if isinstance(canvas_version, dict):
            version = canvas_version.get("version", version)

        payload: dict[str, Any] = {
            "kind": "canvas",
            "operation": operation_token,
            "documentType": str(document_type or canvas.get("documentType") or "document"),
            "version": version if isinstance(version, int) else None,
        }

        metadata["canvasArtifact"] = payload

        logger.info(
            "canvas_opened operation=%s document_type=%s version=%s",
            operation_token,
            payload["documentType"],
            payload["version"],
        )
