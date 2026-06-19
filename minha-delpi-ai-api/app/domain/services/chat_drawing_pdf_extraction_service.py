"""Extração estruturada de desenhos técnicos em PDF — Onda 12.2."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_pdf_bom_extraction_service import (
    ChatDrawingPdfBomExtractionService,
)
from app.domain.services.chat_drawing_pdf_product_context_service import (
    ChatDrawingPdfProductContextService,
)


class ChatDrawingPdfExtractionService:
    @classmethod
    def max_pages(cls) -> int:
        return max(1, int(ChatDomainConfigService.chat_drawing_pdf_max_pages()))

    @classmethod
    def extract_from_storage_path(cls, storage_path: str, *, filename: str = "") -> dict[str, Any]:
        from app.domain.services.chat_pdf_document_extraction_service import (
            ChatPdfDocumentExtractionService,
        )

        extracted = ChatPdfDocumentExtractionService.extract_from_storage_path(
            storage_path,
            filename=filename or Path(storage_path).name,
            page_limit=cls.max_pages(),
            layout_profile=ChatPdfDocumentExtractionService.LAYOUT_DRAWING_DELPI,
            enable_region_ocr=True,
        )

        if not extracted.get("supported"):
            return cls._empty(
                reason=str(extracted.get("reason") or "unsupported"),
            )

        metadata = extracted.get("parseMetadata")

        if not isinstance(metadata, dict):
            metadata = {}
        elif extracted.get("stages"):
            metadata = {**metadata, "stages": list(extracted.get("stages") or [])}

        return cls.parse_from_text(
            str(extracted.get("fullText") or "").strip(),
            metadata=metadata,
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

        stamp_text = str((metadata or {}).get("stampText") or "").strip()

        stamp_extract = ChatDrawingStampExtractionService.extract(
            stamp_text=stamp_text,
            title_text=cls._title_scope_text(normalized, stamp_text=stamp_text),
        )
        product_code, stamp_source = ChatDrawingPdfProductContextService.resolve_product_code(
            stamp_extract=stamp_extract,
            full_text=normalized,
            metadata=metadata,
        )

        bom_payload = ChatDrawingPdfBomExtractionService.extract(
            full_text=normalized,
            metadata=metadata,
            product_code=product_code,
        )

        from app.domain.services.chat_drawing_dimensions_extraction_service import (
            ChatDrawingDimensionsExtractionService,
        )

        dimensions_text = str((metadata or {}).get("dimensionsText") or "").strip()
        dimensions = ChatDrawingDimensionsExtractionService.merge_dimensions(
            ChatDrawingDimensionsExtractionService.extract_dimensions(normalized),
            region_text=dimensions_text,
            fallback_text=normalized,
        )

        component_codes = list(bom_payload.get("componentCodes") or [])
        min_chars = max(1, int(ChatDomainConfigService.chat_drawing_pdf_min_legible_chars()))
        legible = char_count >= min_chars and bool(
            product_code or cls._extract_revision(normalized) or component_codes
        )

        payload: dict[str, Any] = {
            "productCode": product_code,
            "productCodeSource": stamp_source,
            "revision": cls._extract_revision(normalized),
            "internalRevision": cls._extract_internal_revision(normalized),
            "customerReference": cls._extract_labeled_value(
                normalized,
                labels=("COD. CLIENTE", "COD CLIENTE", "CÓD. CLIENTE", "REFERENCIA CLIENTE"),
            ),
            "description": cls._extract_labeled_value(
                normalized,
                labels=("DESCRIÇÃO", "DESCRICAO", "DESCRIPTION"),
            ),
            "componentCodes": component_codes,
            "intermediateCodes": list(bom_payload.get("intermediateCodes") or []),
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

        if bom_payload.get("bomRows"):
            payload["bomRows"] = bom_payload["bomRows"]

        if bom_payload.get("bomSource"):
            payload["bomSource"] = bom_payload["bomSource"]

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
    def _extract_revision(cls, text: str) -> str | None:
        match = ChatDrawingPatternsService.revision().search(text)

        if match:
            return match.group(1).zfill(2)

        return None

    @classmethod
    def _extract_internal_revision(cls, text: str) -> str | None:
        matches = ChatDrawingPatternsService.internal_revision_table().findall(str(text or ""))

        if not matches:
            return None

        return str(matches[-1]).zfill(2)

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
    def _extract_dimensions(cls, text: str) -> dict[str, float | None]:
        dimensions: dict[str, float | None] = {
            "totalLengthMm": None,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
        }

        length_match = ChatDrawingPatternsService.pdf_length_pattern().search(text)

        if length_match:
            dimensions["totalLengthMm"] = cls._parse_number(length_match.group(1))

        left_match = ChatDrawingPatternsService.pdf_decape_left_pattern().search(text)

        if left_match:
            dimensions["leftDecapeMm"] = cls._parse_number(left_match.group(1))

        right_match = ChatDrawingPatternsService.pdf_decape_right_pattern().search(text)

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
