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

        product_code = ChatProductQueryIntentService.normalize_product_code(
            str(pdf_extract.get("productCode") or "")
        )

        for code in cls._codes_from_client_reference_block(
            cls._text_haystack(pdf_extract),
            product_code=product_code,
        ):
            codes.add(code)

        codes |= cls._collect_wire_gauge_false_codes_from_bom_haystack(pdf_extract)

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

        if cls._is_wire_gauge_false_code_row(row):
            return True

        for pattern in ChatDrawingPatternsService.bom_client_reference_noise_patterns():
            if pattern.search(blob):
                return True

        if cls._description_is_revision_only(description) and cls._quantity_looks_like_dc_suffix(
            quantity
        ):
            return True

        return False

    @classmethod
    def _is_wire_gauge_false_code_row(cls, row: dict[str, Any]) -> bool:
        """Linha BOM cuja descrição começa com bitola (AWG/ANG) — OCR gera falso 10xxxxxx."""
        description = str(row.get("description") or "").strip().upper()

        if not description:
            return False

        for pattern in ChatDrawingPatternsService.bom_wire_gauge_row_noise_patterns():
            if pattern.search(description):
                return True

        return False

    @classmethod
    def _collect_wire_gauge_false_codes_from_bom_haystack(cls, pdf_extract: dict) -> set[str]:
        """Códigos 10xxxxxx em linhas BOM OCR com bitola inline (ex.: 22-20ANG)."""
        source_metadata = pdf_extract.get("sourceMetadata")

        if not isinstance(source_metadata, dict):
            return set()

        region_texts = source_metadata.get("regionTexts")

        if not isinstance(region_texts, dict):
            return set()

        bom_text = str(region_texts.get("bom") or "").strip()

        if not bom_text:
            return set()

        inline_patterns = ChatDrawingPatternsService.bom_wire_gauge_inline_noise_patterns()
        component_pattern = ChatDrawingPatternsService.component_code()
        codes: set[str] = set()

        for line in bom_text.splitlines():
            upper = str(line or "").strip().upper()

            if not upper or not cls._line_looks_like_ocr_table_noise(upper):
                continue

            if not any(pattern.search(upper) for pattern in inline_patterns):
                continue

            for match in component_pattern.finditer(line):
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if code:
                    codes.add(code)

        return codes

    @classmethod
    def _line_looks_like_ocr_table_noise(cls, line: str) -> bool:
        return "|" in line or line.lstrip().startswith("[")

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
    def _text_haystack(cls, pdf_extract: dict) -> str:
        parts: list[str] = []
        full_text = str(pdf_extract.get("fullText") or "").strip()

        if full_text:
            parts.append(full_text)

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

        return "\n".join(parts)

    @classmethod
    def _codes_from_reference_haystack(cls, pdf_extract: dict) -> set[str]:
        haystack = cls._text_haystack(pdf_extract)
        codes: set[str] = set()

        for pattern in ChatDrawingPatternsService.client_reference_code_patterns():
            for match in pattern.finditer(haystack):
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if code:
                    codes.add(code)

        return codes

    @classmethod
    def _codes_from_client_reference_block(
        cls,
        text: str,
        *,
        product_code: str,
    ) -> set[str]:
        lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]

        if not lines:
            return set()

        codes: set[str] = set()
        ref_context = False
        bom_header = ChatDrawingPatternsService.bom_table_header()
        component_pattern = ChatDrawingPatternsService.component_code()
        ref_markers = ChatDrawingPatternsService.bom_client_reference_noise_patterns()

        for line in lines:
            upper = line.upper()

            if bom_header.search(upper) or ("QTD" in upper and "COD" in upper):
                ref_context = False
                continue

            if any(pattern.search(upper) for pattern in ref_markers):
                ref_context = True
                continue

            line_digits = "".join(char for char in line if char.isdigit())

            if product_code and line_digits == product_code:
                ref_context = False
                continue

            if not ref_context:
                continue

            matches = list(component_pattern.finditer(line))

            if not matches:
                continue

            for match in matches:
                code = ChatProductQueryIntentService.normalize_product_code(
                    str(match.group(1) or "")
                )

                if not code or code == product_code:
                    continue

                if ChatDrawingPatternsService.is_intermediate_family(str(code)):
                    continue

                if line_digits == code or (len(line) <= 24 and len(matches) == 1):
                    codes.add(code)

        return codes
