"""Extração heurística de BOM a partir de texto OCR — Onda 13.3.2."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_BOM_SECTION_RE = re.compile(
    r"(?:LISTA\s+DE\s+MATERIAIS|LISTA\s+MATERIAL|BOM\b|COMPONENTES|MAT[ÉE]RIA[\s-]*PRIMA)",
    re.IGNORECASE,
)
_COMPONENT_CODE_RE = re.compile(r"\b(90\d{6}|50\d{6}|10\d{6}|100\d{5})\b")
_QTY_RE = re.compile(r"\b(\d+[,.]?\d*)\s*(?:UN|PCS|PÇ|PC|PEÇAS?)?\b", re.IGNORECASE)


class ChatDocumentVisionBomService:
    @classmethod
    def extract_bom_rows(
        cls,
        text: str,
        *,
        exclude_product_code: str | None = None,
        max_rows: int = 40,
    ) -> list[dict[str, Any]]:
        normalized = str(text or "").strip()

        if not normalized or not _BOM_SECTION_RE.search(normalized):
            return []

        exclude = ChatProductQueryIntentService.normalize_product_code(
            exclude_product_code or ""
        )
        section_start = cls._bom_section_offset(normalized)
        section_text = normalized[section_start:]
        rows: list[dict[str, Any]] = []
        seen_codes: set[str] = set()

        for line in section_text.splitlines():
            if len(rows) >= max_rows:
                break

            row = cls._parse_bom_line(line, exclude=exclude, seen=seen_codes)

            if row:
                rows.append(row)
                seen_codes.add(str(row["code"]))

        return rows

    @classmethod
    def _bom_section_offset(cls, text: str) -> int:
        match = _BOM_SECTION_RE.search(text)

        if not match:
            return 0

        return match.start()

    @classmethod
    def _parse_bom_line(
        cls,
        line: str,
        *,
        exclude: str,
        seen: set[str],
    ) -> dict[str, Any] | None:
        stripped = str(line or "").strip()

        if len(stripped) < 6:
            return None

        code_match = _COMPONENT_CODE_RE.search(stripped)

        if not code_match:
            return None

        code = ChatProductQueryIntentService.normalize_product_code(code_match.group(1))

        if not code or code == exclude or code in seen:
            return None

        remainder = stripped[code_match.end() :].strip()
        qty = None
        description = remainder

        qty_match = _QTY_RE.search(remainder)

        if qty_match:
            qty = qty_match.group(1).replace(",", ".")
            description = remainder[qty_match.end() :].strip(" -|\t")

        return {
            "code": code,
            "quantity": qty,
            "description": (description or "")[:120] or None,
        }

    @classmethod
    def merge_component_codes_from_rows(
        cls,
        component_codes: list[str],
        bom_rows: list[dict[str, Any]],
    ) -> list[str]:
        merged = list(component_codes or [])

        for row in bom_rows:
            code = str(row.get("code") or "").strip()

            if code and code not in merged:
                merged.append(code)

        return merged
