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
from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)
from app.domain.services.chat_pdf_annotation_table_service import (
    ChatPdfAnnotationTableService,
)


class ChatDrawingPdfExtractionService:
    @classmethod
    def max_pages(cls) -> int:
        return max(1, int(ChatDomainConfigService.chat_drawing_pdf_max_pages()))

    @classmethod
    def extract_from_storage_path(cls, storage_path: str, *, filename: str = "") -> dict[str, Any]:
        from app.domain.services.chat_drawing_extraction_quality_retry_service import (
            ChatDrawingExtractionQualityRetryService,
        )

        return ChatDrawingExtractionQualityRetryService.extract_until_confident(
            storage_path,
            filename=filename or Path(storage_path).name,
        )

    @classmethod
    def _extract_single_pass(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        extraction_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_pdf_document_extraction_service import (
            ChatPdfDocumentExtractionService,
        )

        options = extraction_options if isinstance(extraction_options, dict) else {}
        enable_region_ocr = options.get("enableRegionOcr")

        extracted = ChatPdfDocumentExtractionService.extract_from_storage_path(
            storage_path,
            filename=filename or Path(storage_path).name,
            page_limit=cls.max_pages(),
            layout_profile=ChatPdfDocumentExtractionService.LAYOUT_DRAWING_DELPI,
            enable_region_ocr=enable_region_ocr,
            region_ocr_dpi_multiplier=float(options.get("regionOcrDpiMultiplier") or 1.0),
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

        page_count = int(extracted.get("pageCount") or 0)

        if page_count > 0:
            metadata = {
                **metadata,
                "pageCount": page_count,
                "pagesProcessed": page_count,
            }

        metadata = {**metadata, "storagePath": storage_path}

        return cls.parse_from_text(
            str(extracted.get("fullText") or "").strip(),
            metadata=metadata,
            storage_path=storage_path,
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
        storage_path: str = "",
    ) -> dict[str, Any]:
        normalized = str(text or "").strip()
        meta = metadata if isinstance(metadata, dict) else {}
        cad_text = cls._cad_reference_text(meta)
        scope_text = cls._merge_scope_text(normalized, cad_text)

        char_count = len(scope_text)

        from app.domain.services.chat_drawing_stamp_extraction_service import (
            ChatDrawingStampExtractionService,
        )

        stamp_text = str(meta.get("stampText") or "").strip()
        filename_code = ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            str(meta.get("filename") or "")
        )

        stamp_extract = ChatDrawingStampExtractionService.extract(
            stamp_text=stamp_text or cad_text[:1200],
            title_text=cls._title_scope_text(scope_text, stamp_text=stamp_text or cad_text),
            filename_code=filename_code,
        )
        product_code, stamp_source = ChatDrawingPdfProductContextService.resolve_product_code(
            stamp_extract=stamp_extract,
            full_text=scope_text,
            metadata=meta,
        )

        from app.domain.services.chat_drawing_regional_scope_service import (
            ChatDrawingRegionalScopeService,
        )

        validation_scopes = ChatDrawingRegionalScopeService.resolve(
            metadata=meta,
            full_text=scope_text,
            product_code=product_code or filename_code,
        )
        meta = {**meta, "validationScopes": validation_scopes}

        bom_payload = ChatDrawingPdfBomExtractionService.extract(
            full_text=scope_text,
            metadata=meta,
            product_code=product_code,
        )

        from app.domain.services.chat_drawing_dimensions_extraction_service import (
            ChatDrawingDimensionsExtractionService,
        )

        dimensions_scope = validation_scopes.get("dimensions")
        dimensions_region_text = ""

        if isinstance(dimensions_scope, dict):
            dimensions_region_text = str(dimensions_scope.get("text") or "").strip()
            dimensions_fallback = str(dimensions_scope.get("fallbackText") or "").strip()
        else:
            dimensions_fallback = cad_text or normalized

        if not dimensions_region_text:
            dimensions_region_text = str(meta.get("dimensionsText") or "").strip()

        dimensions = ChatDrawingDimensionsExtractionService.merge_dimensions(
            ChatDrawingDimensionsExtractionService.extract_dimensions(
                normalized or cad_text
            ),
            region_text=dimensions_region_text,
            fallback_text=dimensions_fallback or cad_text or normalized,
        )

        component_codes = list(bom_payload.get("componentCodes") or [])
        min_chars = max(1, int(ChatDomainConfigService.chat_drawing_pdf_min_legible_chars()))
        legible = char_count >= min_chars and bool(
            product_code or cls._extract_revision(scope_text) or component_codes
        )
        revision = (
            stamp_extract.get("revision")
            or cls._extract_revision(scope_text)
            or cls._extract_revision(cad_text)
        )

        payload: dict[str, Any] = {
            "productCode": product_code,
            "productCodeSource": stamp_source,
            "revision": revision,
            "internalRevision": cls._extract_internal_revision(scope_text or cad_text),
            "customerReference": cls._extract_labeled_value(
                scope_text,
                labels=("COD. CLIENTE", "COD CLIENTE", "CÓD. CLIENTE", "REFERENCIA CLIENTE"),
            ),
            "description": stamp_extract.get("description")
            or cls._extract_labeled_value(
                scope_text,
                labels=("DESCRIÇÃO", "DESCRICAO", "DESCRIPTION"),
            )
            or cls._extract_chicote_description(scope_text or cad_text),
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

        title_block = ChatDrawingStampExtractionService.build_title_block(
            stamp_extract,
            raw_text=(stamp_text or cad_text or scope_text)[:800],
        )

        if title_block:
            payload["titleBlock"] = title_block

        if metadata:
            payload["sourceMetadata"] = metadata

        if bom_payload.get("bomRows"):
            payload["bomRows"] = bom_payload["bomRows"]

        if bom_payload.get("bomSource"):
            payload["bomSource"] = bom_payload["bomSource"]

        payload["validationScopes"] = ChatDrawingRegionalScopeService.serialize(
            validation_scopes
        )

        regions_meta = meta.get("regions")

        if isinstance(regions_meta, dict):
            layout = regions_meta.get("_layoutAnalysis")

            if isinstance(layout, dict) and layout:
                payload["pageLayoutAnalysis"] = layout

        for key in ChatDrawingPatternsService.multipage_page_count_keys():
            raw = meta.get(key)

            try:
                count = int(raw or 0)
            except (TypeError, ValueError):
                continue

            if count > 0:
                payload["pageCount"] = count
                payload["pagesProcessed"] = count
                break

        from app.domain.services.chat_drawing_bom_vision_refinement_service import (
            ChatDrawingBomVisionRefinementService,
        )

        return ChatDrawingBomVisionRefinementService.apply(
            payload,
            storage_path=storage_path,
            product_code=str(payload.get("productCode") or ""),
        )

    @classmethod
    def _cad_reference_text(cls, metadata: dict[str, Any]) -> str:
        cad = str(metadata.get("cadReferenceText") or "").strip()

        if cad:
            return cad

        parts: list[str] = []
        annotation_text = str(metadata.get("annotationText") or "").strip()

        if annotation_text:
            parts.append(annotation_text)

        tables = metadata.get("annotationTables")

        if isinstance(tables, list):
            table_text = ChatPdfAnnotationTableService.table_text(tables).strip()

            if table_text:
                parts.append(table_text)

        return "\n\n".join(parts).strip()

    @classmethod
    def _merge_scope_text(cls, full_text: str, cad_text: str) -> str:
        parts = [part for part in (full_text, cad_text) if str(part or "").strip()]
        return "\n\n".join(parts).strip()

    @classmethod
    def _extract_chicote_description(cls, text: str) -> str | None:
        match = re.search(
            r"(CHICOTE(?:\s+DE\s+LIGA[ÇC][ÃA]O)?[^\n|]{0,40})",
            str(text or ""),
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return match.group(1).strip()[:80]

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
        blob = str(text or "")
        matches: list[str] = []

        for pattern in ChatDrawingPatternsService.internal_revision_table_patterns():
            matches.extend(str(item) for item in pattern.findall(blob))

        if not matches:
            legacy = ChatDrawingPatternsService.internal_revision_table().findall(blob)

            if legacy:
                matches.extend(str(item) for item in legacy)

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
