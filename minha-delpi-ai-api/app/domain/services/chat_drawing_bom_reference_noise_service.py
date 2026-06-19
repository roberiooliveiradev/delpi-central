"""Ruído de referência cliente (ex.: código WEG DC:Z-855) — não confundir com BOM Protheus."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingBomReferenceNoiseService:
    @classmethod
    def filter_bom_rows(cls, bom_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            row
            for row in bom_rows
            if isinstance(row, dict) and not cls.is_client_reference_row(row)
        ]

    @classmethod
    def collect_reference_noise_codes(cls, pdf_extract: dict) -> set[str]:
        codes: set[str] = set()

        for row in pdf_extract.get("bomRows") or []:
            if not isinstance(row, dict):
                continue

            if not cls.is_client_reference_row(row):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("code") or "")
            )

            if code:
                codes.add(code)

        for code in cls._codes_from_reference_haystack(pdf_extract):
            codes.add(code)

        return codes

    @classmethod
    def is_client_reference_row(cls, row: dict[str, Any]) -> bool:
        code = ChatProductQueryIntentService.normalize_product_code(
            str(row.get("code") or "")
        )
        description = str(row.get("description") or "").strip()
        quantity = str(row.get("quantity") or "").strip()
        blob = " ".join(part for part in (code, description, quantity) if part).upper()

        if not blob.strip():
            return False

        for pattern in ChatDrawingPatternsService.bom_client_reference_noise_patterns():
            if pattern.search(blob):
                return True

        if cls._description_is_revision_only(description) and cls._quantity_looks_like_dc_suffix(
            quantity
        ):
            return True

        return False

    @classmethod
    def _description_is_revision_only(cls, description: str) -> bool:
        normalized = str(description or "").strip().upper()

        if not normalized:
            return False

        return bool(re.fullmatch(r"REV\s*:?\s*\d+", normalized))

    @classmethod
    def _quantity_looks_like_dc_suffix(cls, quantity: str) -> bool:
        normalized = str(quantity or "").strip()

        if not normalized or not normalized.isdigit():
            return False

        return len(normalized) <= 4

    @classmethod
    def _codes_from_reference_haystack(cls, pdf_extract: dict) -> set[str]:
        parts: list[str] = []
        source_metadata = pdf_extract.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ("stampText", "annotationText", "cadReferenceText"):
                text = str(source_metadata.get(key) or "").strip()

                if text:
                    parts.append(text)

        title_block = pdf_extract.get("titleBlock")

        if isinstance(title_block, dict):
            text = str(title_block.get("rawText") or "").strip()

            if text:
                parts.append(text)

        haystack = "\n".join(parts)
        codes: set[str] = set()

        for pattern in ChatDrawingPatternsService.client_reference_code_patterns():
            for match in pattern.finditer(haystack):
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if code:
                    codes.add(code)

        return codes
