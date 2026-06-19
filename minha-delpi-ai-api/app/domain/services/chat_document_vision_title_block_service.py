"""Carimbo / title block heurístico — Onda 13 + parse hierárquico Onda 14."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatDocumentVisionTitleBlockService:
    """Monta `titleBlock` a partir de OCR de carimbo e campos já extraídos."""

    @classmethod
    def build(
        cls,
        *,
        text: str,
        product_code: str | None = None,
        revision: str | None = None,
        stamp_text: str | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_drawing_stamp_extraction_service import (
            ChatDrawingStampExtractionService,
        )

        stamp = str(stamp_text or "").strip()
        body = str(text or "").strip()
        extract = ChatDrawingStampExtractionService.extract(
            stamp_text=stamp,
            title_text=body,
        )

        if product_code and not extract.get("productCode"):
            extract = {
                **extract,
                "productCode": product_code,
                "productCodeSource": extract.get("productCodeSource") or "context",
            }

        if revision and not extract.get("revision"):
            extract = {**extract, "revision": revision}

        snippet = cls._extract_stamp_snippet(body)
        raw = stamp or snippet

        if not extract.get("productCode") and not extract.get("revision") and not raw:
            return None

        if not raw:
            raw = body[:800]

        return ChatDrawingStampExtractionService.build_title_block(extract, raw_text=raw)

    @classmethod
    def _extract_stamp_snippet(cls, text: str) -> str:
        stamp_line_re = ChatDocumentVisionContentService.title_block_stamp_line_pattern()
        min_length = ChatDocumentVisionContentService.title_block_min_line_length()
        max_lines = ChatDocumentVisionContentService.title_block_max_stamp_lines()
        lines: list[str] = []

        for line in str(text or "").splitlines():
            stripped = line.strip()

            if len(stripped) < min_length:
                continue

            if stamp_line_re.search(stripped):
                lines.append(stripped)

            if len(lines) >= max_lines:
                break

        return "\n".join(lines).strip()
