"""Carimbo / title block heurístico — Onda 13 + parse hierárquico Onda 14."""

from __future__ import annotations

from typing import Any


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

        raw = stamp or cls._extract_stamp_snippet(body) or body[:800]

        return ChatDrawingStampExtractionService.build_title_block(extract, raw_text=raw)

    @classmethod
    def _extract_stamp_snippet(cls, text: str) -> str:
        import re

        stamp_line_re = re.compile(
            r"(?:PRODUTO|C[ÓO]DIGO|DESENHO|REV(?:\.|IS[ÃA]O)?|CLIENTE|MATERIAL|CHICOTE)\b",
            re.IGNORECASE,
        )
        lines: list[str] = []

        for line in str(text or "").splitlines():
            stripped = line.strip()

            if len(stripped) < 4:
                continue

            if stamp_line_re.search(stripped):
                lines.append(stripped)

            if len(lines) >= 12:
                break

        return "\n".join(lines).strip()
