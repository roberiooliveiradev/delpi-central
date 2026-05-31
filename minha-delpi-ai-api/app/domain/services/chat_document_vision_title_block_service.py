"""Carimbo / title block heurístico — Onda 13 (contrato DocumentVisionResult)."""

from __future__ import annotations

import re
from typing import Any

_STAMP_LINE_RE = re.compile(
    r"(?:PRODUTO|C[ÓO]DIGO|DESENHO|REV(?:\.|IS[ÃA]O)?|CLIENTE|MATERIAL)\b",
    re.IGNORECASE,
)


class ChatDocumentVisionTitleBlockService:
    """Monta `titleBlock` a partir de OCR de carimbo e campos já extraídos."""

    # Faixa superior + canto superior direito (normalizado 0–1), alinhado ao crop Tesseract.
    DEFAULT_BBOX = [0.0, 0.0, 1.0, 0.38]

    @classmethod
    def build(
        cls,
        *,
        text: str,
        product_code: str | None = None,
        revision: str | None = None,
        stamp_text: str | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        raw = str(stamp_text or "").strip() or cls._extract_stamp_snippet(text)
        code = str(product_code or "").strip()
        rev = str(revision or "").strip()

        if not code and raw:
            code = ChatProductQueryIntentService.extract_product_code(raw) or ""

        if not code and text:
            code = ChatProductQueryIntentService.extract_product_code(text) or ""

        if not rev and raw:
            rev_match = re.search(
                r"REV(?:\.|IS[ÃA]O)?\s*[:.]?\s*(\d{1,3})",
                raw,
                re.IGNORECASE,
            )

            if rev_match:
                rev = rev_match.group(1).strip()

        if not raw and not code:
            return None

        fields: dict[str, str] = {}

        if code:
            fields["code"] = ChatProductQueryIntentService.normalize_product_code(code)

        if rev:
            fields["rev"] = rev

        return {
            "rawText": raw[:800] if raw else "",
            "bbox": list(cls.DEFAULT_BBOX),
            "fields": fields,
        }

    @classmethod
    def _extract_stamp_snippet(cls, text: str) -> str:
        lines: list[str] = []

        for line in str(text or "").splitlines():
            stripped = line.strip()

            if len(stripped) < 4:
                continue

            if _STAMP_LINE_RE.search(stripped):
                lines.append(stripped)

            if len(lines) >= 12:
                break

        return "\n".join(lines).strip()
