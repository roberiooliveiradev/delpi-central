"""Extração estruturada de desenhos técnicos em PDF — Onda 12.2."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_domain_config_service import ChatDomainConfigService

_REV_PATTERN = re.compile(
    r"(?:REV(?:IS[AÃ]O)?\.?|REVISION)\s*[:.]?\s*(\d{1,3})",
    re.IGNORECASE,
)
_COMPONENT_CODE_RE = re.compile(r"\b(90\d{6}|50\d{6}|10\d{6}|100\d{5})\b")
_INTERMEDIATE_CODE_RE = re.compile(r"\b(50\d{6})\b")
_LENGTH_RE = re.compile(
    r"(?:COMPR(?:IMENTO)?\s*(?:TOTAL)?|LENGTH)\s*[:.]?\s*(\d+[,.]?\d*)\s*mm?",
    re.IGNORECASE,
)
_DECAPE_LEFT_RE = re.compile(
    r"DECAPE\s*E(?:SQUERDO)?\s*[:.]?\s*(\d+[,.]?\d*)",
    re.IGNORECASE,
)
_DECAPE_RIGHT_RE = re.compile(
    r"DECAPE\s*D(?:IREITO)?\s*[:.]?\s*(\d+[,.]?\d*)",
    re.IGNORECASE,
)


class ChatDrawingPdfExtractionService:
    @classmethod
    def max_pages(cls) -> int:
        return max(1, int(ChatDomainConfigService.chat_drawing_pdf_max_pages()))

    @classmethod
    def extract_from_storage_path(cls, storage_path: str, *, filename: str = "") -> dict[str, Any]:
        from app.application.services.chat_attachment_text_extractor import (
            ChatAttachmentTextExtractor,
        )

        extracted = ChatAttachmentTextExtractor().extract(
            storage_path=storage_path,
            filename=filename or Path(storage_path).name,
            content_type="application/pdf",
        )

        if not extracted.get("supported"):
            return cls._empty(
                reason=str((extracted.get("metadata") or {}).get("reason") or "unsupported"),
            )

        text = str(extracted.get("content") or "").strip()

        return cls.parse_from_text(
            text,
            metadata=extracted.get("metadata") if isinstance(extracted.get("metadata"), dict) else {},
        )

    @classmethod
    def parse_from_attachment_context(cls, attachment_context: str | None) -> dict[str, Any] | None:
        if not attachment_context or not str(attachment_context).strip():
            return None

        blocks = str(attachment_context).split("###")

        merged = ""

        for block in blocks[1:]:
            lines = block.strip().splitlines()

            if len(lines) <= 1:
                continue

            merged += "\n".join(lines[1:]) + "\n\n"

        if not merged.strip():
            merged = str(attachment_context)

        parsed = cls.parse_from_text(merged.strip())

        if parsed.get("productCode") or parsed.get("legible"):
            return parsed

        return None

    @classmethod
    def parse_from_text(
        cls,
        text: str,
        *,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        normalized = str(text or "").strip()
        char_count = len(normalized)

        from app.domain.services.chat_drawing_stamp_extraction_service import (
            ChatDrawingStampExtractionService,
        )

        stamp_extract = ChatDrawingStampExtractionService.extract(
            title_text=cls._title_scope_text(normalized),
        )
        product_code = stamp_extract.get("productCode")
        stamp_source = stamp_extract.get("productCodeSource")

        if not product_code:
            product_code = cls._extract_fallback_product_code(normalized)

        revision = cls._extract_revision(normalized)
        customer_reference = cls._extract_labeled_value(
            normalized,
            labels=("COD. CLIENTE", "COD CLIENTE", "CÓD. CLIENTE", "REFERENCIA CLIENTE"),
        )
        description = cls._extract_labeled_value(
            normalized,
            labels=("DESCRIÇÃO", "DESCRICAO", "DESCRIPTION"),
        )

        component_codes = cls._extract_component_codes(normalized, exclude=product_code)
        intermediate_codes = sorted(_INTERMEDIATE_CODE_RE.findall(normalized))
        dimensions = cls._extract_dimensions(normalized)

        min_chars = max(1, int(ChatDomainConfigService.chat_drawing_pdf_min_legible_chars()))
        legible = char_count >= min_chars and bool(
            product_code or revision or component_codes
        )

        payload: dict[str, Any] = {
            "productCode": product_code,
            "productCodeSource": stamp_source,
            "revision": revision,
            "customerReference": customer_reference,
            "description": description,
            "componentCodes": component_codes,
            "intermediateCodes": intermediate_codes,
            "dimensions": dimensions,
            "charCount": char_count,
            "legible": legible,
            "extractor": (metadata or {}).get("extractor") or "text_parse",
        }

        if stamp_extract.get("productCodeCandidates"):
            payload["productCodeCandidates"] = stamp_extract["productCodeCandidates"]

        if stamp_extract.get("conflicts"):
            payload["conflicts"] = stamp_extract["conflicts"]

        if metadata:
            payload["sourceMetadata"] = metadata

        return payload

    @classmethod
    def _title_scope_text(cls, text: str, *, stamp_text: str = "") -> str:
        from app.domain.services.chat_document_vision_title_block_service import (
            ChatDocumentVisionTitleBlockService,
        )

        parts: list[str] = []

        if stamp_text.strip():
            parts.append(stamp_text.strip())

        snippet = ChatDocumentVisionTitleBlockService._extract_stamp_snippet(text)

        if snippet:
            parts.append(snippet)

        if not parts:
            parts.append(str(text or "")[:1200])

        return "\n".join(parts)[:2000]

    @classmethod
    def _extract_fallback_product_code(cls, text: str) -> str | None:
        codes_90 = re.findall(r"\b(90\d{6})\b", text)

        if codes_90:
            return ChatProductQueryIntentService.normalize_product_code(codes_90[0])

        product_code = ChatProductQueryIntentService.extract_product_code(text)

        if product_code and re.match(r"^90\d{6}$", product_code):
            return product_code

        codes_50 = re.findall(r"\b(50\d{6})\b", text)

        if codes_50:
            return ChatProductQueryIntentService.normalize_product_code(codes_50[0])

        return None

    @classmethod
    def _extract_revision(cls, text: str) -> str | None:
        match = _REV_PATTERN.search(text)

        if match:
            return match.group(1).zfill(2)

        return None

    @classmethod
    def _extract_labeled_value(cls, text: str, *, labels: tuple[str, ...]) -> str | None:
        upper = text.upper()

        for label in labels:
            idx = upper.find(label)

            if idx < 0:
                continue

            snippet = text[idx : idx + 120]
            parts = re.split(r"[:|\n]", snippet, maxsplit=1)

            if len(parts) < 2:
                continue

            value = parts[1].strip().split("\n", 1)[0].strip()

            if value:
                return value[:80]

        return None

    @classmethod
    def _extract_component_codes(
        cls,
        text: str,
        *,
        exclude: str | None,
    ) -> list[str]:
        exclude_norm = ChatProductQueryIntentService.normalize_product_code(exclude or "")
        found: list[str] = []

        for match in _COMPONENT_CODE_RE.finditer(text):
            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if not code or code == exclude_norm:
                continue

            if code not in found:
                found.append(code)

        return found

    @classmethod
    def _extract_dimensions(cls, text: str) -> dict[str, float | None]:
        dimensions: dict[str, float | None] = {
            "totalLengthMm": None,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
        }

        length_match = _LENGTH_RE.search(text)

        if length_match:
            dimensions["totalLengthMm"] = cls._parse_number(length_match.group(1))

        left_match = _DECAPE_LEFT_RE.search(text)

        if left_match:
            dimensions["leftDecapeMm"] = cls._parse_number(left_match.group(1))

        right_match = _DECAPE_RIGHT_RE.search(text)

        if right_match:
            dimensions["rightDecapeMm"] = cls._parse_number(right_match.group(1))

        return dimensions

    @classmethod
    def _parse_number(cls, raw: str) -> float | None:
        from app.domain.services.chat_drawing_tolerance_service import (
            ChatDrawingToleranceService,
        )

        return ChatDrawingToleranceService.parse_mm(raw)

    @classmethod
    def _empty(cls, *, reason: str) -> dict[str, Any]:
        return {
            "productCode": None,
            "revision": None,
            "customerReference": None,
            "description": None,
            "componentCodes": [],
            "intermediateCodes": [],
            "dimensions": {},
            "charCount": 0,
            "legible": False,
            "extractor": reason,
        }
