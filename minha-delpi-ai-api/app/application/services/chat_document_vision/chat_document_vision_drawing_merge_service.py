"""Merge visão → parse de desenho."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.config.settings import Settings


class ChatDocumentVisionDrawingMergeService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def merge_into_drawing_parse(
        cls,
        parsed: dict[str, Any] | None,
        vision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = dict(parsed) if isinstance(parsed, dict) else {}
        doc = vision if isinstance(vision, dict) else {}

        if not doc:
            return base

        merged = {**base}

        for key in (
            "productCode",
            "revision",
            "internalRevision",
            "customerReference",
            "description",
        ):
            if not merged.get(key) and doc.get(key):
                merged[key] = doc[key]

        # Haystack de REF/COD precisa do texto completo; visão pode enriquecer OCR.
        base_text = str(merged.get("fullText") or "").strip()
        doc_text = str(doc.get("fullText") or "").strip()

        if not base_text and doc_text:
            merged["fullText"] = doc_text
        elif (
            base_text
            and doc_text
            and doc_text not in base_text
            and len(doc_text) >= 40
        ):
            merged["fullText"] = f"{base_text}\n\n{doc_text}".strip()

        for key in ("componentCodes", "intermediateCodes"):
            existing = list(merged.get(key) or [])
            incoming = doc.get(key)

            if not isinstance(incoming, list):
                incoming = []

            if cls.vision_has_authoritative_bom(doc):
                merged[key] = cls.merge_authoritative_code_lists(
                    existing=existing,
                    incoming=incoming,
                    pdf_extract=cls.merge_reference_context(base, doc),
                )
            else:
                for code in incoming:
                    if code and code not in existing:
                        existing.append(code)

                merged[key] = existing

        from app.domain.services.chat_drawing_bom_reference_noise_service import (
            ChatDrawingBomReferenceNoiseService,
        )

        noise = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(merged)

        merged["componentCodes"] = [
            code
            for code in (merged.get("componentCodes") or [])
            if code not in noise
        ]

        dimensions = dict(merged.get("dimensions") or {})

        for dim_key, vision_key in (
            ("totalLengthMm", "totalLengthMm"),
            ("leftDecapeMm", "leftDecapeMm"),
            ("rightDecapeMm", "rightDecapeMm"),
        ):
            if dimensions.get(dim_key) is None and doc.get(vision_key) is not None:
                dimensions[dim_key] = doc[vision_key]

        merged["dimensions"] = dimensions
        merged["legible"] = bool(merged.get("legible") or doc.get("legible"))
        merged["charCount"] = max(int(merged.get("charCount") or 0), int(doc.get("charCount") or 0))
        merged["extractor"] = doc.get("engine") or merged.get("extractor") or "document_vision"
        bom_rows = doc.get("bomRows") if isinstance(doc.get("bomRows"), list) else []

        title_block = doc.get("titleBlock") if isinstance(doc.get("titleBlock"), dict) else None

        merged["documentVision"] = {
            "schemaVersion": doc.get("schemaVersion"),
            "engine": doc.get("engine"),
            "stages": doc.get("stages"),
            "legibilityScore": doc.get("legibilityScore"),
            "durationMs": doc.get("durationMs"),
            "bomRowCount": len(bom_rows),
            "hasTitleBlock": bool(title_block),
        }

        if bom_rows:
            merged["bomRows"] = bom_rows
            merged["bomHints"] = cls.bom_rows_to_hints(bom_rows)

        if doc.get("bomSource"):
            merged["bomSource"] = doc["bomSource"]

        if isinstance(doc.get("validationScopes"), dict):
            merged["validationScopes"] = doc["validationScopes"]

        if isinstance(doc.get("sourceMetadata"), dict):
            base_meta = (
                merged.get("sourceMetadata")
                if isinstance(merged.get("sourceMetadata"), dict)
                else {}
            )
            merged["sourceMetadata"] = {**base_meta, **doc["sourceMetadata"]}

        if title_block:
            merged["titleBlock"] = title_block

            fields = title_block.get("fields") if isinstance(title_block.get("fields"), dict) else {}

            if not merged.get("productCode") and fields.get("code"):
                merged["productCode"] = fields["code"]

            if not merged.get("revision") and fields.get("rev"):
                merged["revision"] = fields["rev"]

        return merged

    @classmethod
    def merge_reference_context(
        cls,
        base: dict[str, Any],
        doc: dict[str, Any],
    ) -> dict[str, Any]:
        context = dict(base)

        for key in ("productCode", "fullText", "titleBlock", "sourceMetadata"):
            if not context.get(key) and doc.get(key):
                context[key] = doc[key]

        return context

    @classmethod
    def merge_authoritative_code_lists(
        cls,
        *,
        existing: list[Any],
        incoming: list[Any],
        pdf_extract: dict[str, Any],
    ) -> list[Any]:
        from app.domain.services.chat_drawing_bom_reference_noise_service import (
            ChatDrawingBomReferenceNoiseService,
        )

        noise = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(
            pdf_extract
        )
        merged = list(incoming)
        seen = {str(code).strip() for code in merged if str(code or "").strip()}

        for code in existing:
            normalized = str(code or "").strip()

            if not normalized or normalized in seen or normalized in noise:
                continue

            merged.append(code)
            seen.add(normalized)

        return merged

    @classmethod
    def vision_has_authoritative_bom(cls, doc: dict[str, Any]) -> bool:
        bom_rows = doc.get("bomRows")

        if isinstance(bom_rows, list) and bom_rows:
            return True

        incoming_codes = [
            str(code).strip()
            for code in (doc.get("componentCodes") or [])
            if str(code or "").strip()
        ]

        if not incoming_codes:
            return False

        scopes = doc.get("validationScopes")

        if isinstance(scopes, dict):
            bom = scopes.get("bom")

            if isinstance(bom, dict) and bom.get("available"):
                return True

        bom_source = str(doc.get("bomSource") or "").strip()

        if bom_source in {
            "bom_region",
            "stamp_bom_table",
            "annotation_table",
            "pdf_annotations_bom",
            "full_text_section",
        }:
            return True

        return False

    @classmethod
    def bom_rows_to_hints(cls, bom_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        hints: list[dict[str, Any]] = []

        for row in bom_rows:
            if not isinstance(row, dict):
                continue

            code = str(row.get("code") or "").strip()

            if not code:
                continue

            hints.append(
                {
                    "componentCode": code,
                    "qty": row.get("quantity"),
                    "evidence": "bom_heuristic",
                }
            )

        return hints
