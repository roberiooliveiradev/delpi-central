"""Formatação canônica de OCR e descrição visual para o contexto do LLM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatDocumentVisionContextService:
    @classmethod
    def format_vision_block(
        cls,
        vision: dict[str, Any] | None,
        *,
        filename: str = "",
    ) -> str:
        if not isinstance(vision, dict) or not vision:
            return ""

        text_excerpt = str(
            vision.get("textExcerpt") or vision.get("fullText") or ""
        ).strip()
        image_description = str(vision.get("imageDescription") or "").strip()
        resolved_filename = str(filename or vision.get("filename") or "").strip()

        if not text_excerpt and not image_description:
            return ""

        lines = [f"[{ChatDocumentVisionContentService.context_label('sectionTitle')}]"]

        if resolved_filename:
            lines.append(
                f"{ChatDocumentVisionContentService.context_label('filenameLabel')}: "
                f"{resolved_filename}"
            )

        if image_description:
            lines.append(
                f"{ChatDocumentVisionContentService.context_label('descriptionLabel')}:"
            )
            lines.append(image_description)

        if text_excerpt:
            lines.append(
                f"{ChatDocumentVisionContentService.context_label('textLabel')}:"
            )
            lines.append(text_excerpt)

        return "\n".join(lines).strip()

    @classmethod
    def enrich_tool_context(
        cls,
        tool_context: dict[str, Any] | None,
        *,
        filename: str = "",
    ) -> dict[str, Any]:
        payload = dict(tool_context or {})
        block = cls.format_vision_block(payload.get("documentVision"), filename=filename)

        if not block:
            return payload

        existing = str(payload.get("context") or "").strip()
        payload["context"] = f"{existing}\n\n{block}".strip() if existing else block

        return payload
