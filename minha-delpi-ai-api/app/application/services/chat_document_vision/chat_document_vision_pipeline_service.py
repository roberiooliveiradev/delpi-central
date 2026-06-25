"""Pipeline de extração — visão de documentos."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.config.settings import Settings

from app.application.services.chat_document_vision.chat_document_vision_config_service import (
    ChatDocumentVisionConfigService,
)
from app.application.services.chat_document_vision.chat_document_vision_facade_access import vision_service


class ChatDocumentVisionPipelineService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def needs_vlm_fallback(cls, text: str, *, legible: bool | None = None) -> bool:
        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        normalized = str(text or "").strip()

        if legible is False:
            return True

        return len(normalized) < min_legible

    @classmethod
    def resolve_vision_purpose(
        cls,
        message: str | None,
        *,
        content_type: str = "",
        filename: str = "",
    ) -> str:
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )

        return ChatDocumentVisionSkillService.resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )

    @classmethod
    def extract_drawing_pdf(
        cls,
        storage_path: str,
        *,
        filename: str,
    ) -> dict[str, Any]:
        """Extração DELPI canônica (perfil drawing_delpi + OCR regional) para análise de desenho."""
        from app.domain.services.chat_drawing_pdf_extraction_service import (
            ChatDrawingPdfExtractionService,
        )

        started = time.perf_counter()
        drawing = ChatDrawingPdfExtractionService.extract_from_storage_path(
            storage_path,
            filename=filename,
        )
        source = (
            drawing.get("sourceMetadata")
            if isinstance(drawing.get("sourceMetadata"), dict)
            else {}
        )
        stages = list(source.get("stages") or [])
        engine = str(drawing.get("extractor") or source.get("extractor") or "drawing_delpi")
        bom_rows = drawing.get("bomRows") if isinstance(drawing.get("bomRows"), list) else []
        char_count = int(drawing.get("charCount") or 0)
        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        legibility_score = (
            min(1.0, char_count / float(min_legible * 2)) if char_count else 0.0
        )

        return {
            **drawing,
            "engine": engine,
            "stages": stages,
            "schemaVersion": cls.SCHEMA_VERSION,
            "durationMs": round((time.perf_counter() - started) * 1000, 2),
            "legibilityScore": legibility_score,
            "bomRowCount": len(bom_rows),
            "warnings": [],
            "filename": filename,
        }

    @classmethod
    def extract_from_storage_path(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        content_type: str = "application/pdf",
        message: str | None = None,
        vision_purpose: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        backend = str(Settings.CHAT_DOCUMENT_VISION_BACKEND or "auto").strip().lower()
        stages: list[str] = []
        warnings: list[str] = []
        resolved_purpose = vision_purpose or ChatDocumentVisionPipelineService.resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )

        if ChatDocumentVisionConfigService.is_image(content_type, filename):
            result = vision_service()._extract_image_document(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
                started=started,
                vision_purpose=resolved_purpose,
            )
            result["filename"] = filename
            result["visionPurpose"] = resolved_purpose
            return result

        if backend in {"ollama_vlm", "vlm"}:
            vlm = vision_service()._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
                purpose=resolved_purpose,
            )

            if str(vlm.get("fullText") or "").strip() or str(
                vlm.get("imageDescription") or ""
            ).strip():
                stages.append("ollama_vlm")
                return cls.finalize_result(
                    vlm,
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=list(vlm.get("warnings") or []),
                    started=started,
                    vision_purpose=resolved_purpose,
                )

            warnings.append("ollama_vlm_unavailable_fallback_auto")
            backend = "auto"

        if backend in {"docling", "paddleocr"}:
            neural = vision_service()._stage_neural_backend(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
            )

            if str(neural.get("fullText") or "").strip():
                stages.append(backend)
                return cls.finalize_result(
                    neural,
                    engine=backend,
                    stages=stages,
                    warnings=list(neural.get("warnings") or []),
                    started=started,
                )

            warnings.append(f"{backend}_unavailable_fallback_auto")
            backend = "auto"

        native = vision_service()._stage_native(storage_path, filename=filename, content_type=content_type)
        stages.append("native")
        full_text = str(native.get("fullText") or "")
        char_count = len(full_text.strip())

        if backend in {"native", "text"}:
            return cls.finalize_result(
                native,
                engine="native",
                stages=stages,
                warnings=warnings,
                started=started,
            )

        from app.domain.services.chat_drawing_native_text_gate_service import (
            ChatDrawingNativeTextGateService,
        )
        from app.domain.services.chat_drawing_product_code_resolution_service import (
            ChatDrawingProductCodeResolutionService,
        )

        filename_code = ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            filename
        )
        native_plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
            full_text,
            product_code=str(native.get("productCode") or ""),
            filename_code=filename_code,
        )

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        needs_ocr = backend in {"tesseract", "auto"} and (
            backend == "tesseract"
            or char_count < min_legible
            or not native.get("legible")
            or not native_plausible
        )

        if needs_ocr and ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path):
            ocr = vision_service()._stage_tesseract_pdf(storage_path)
            stages.append("tesseract_pdf")

            if ocr.get("stampCrop"):
                stages.append("tesseract_stamp_crop")

            if ocr.get("detailOcrApplied"):
                stages.append("tesseract_region_detail")

            if ocr.get("fullText"):
                merged_text = f"{full_text}\n\n{ocr['fullText']}".strip()
                native = cls.build_from_text(
                    merged_text,
                    engine=ocr.get("engine") or "tesseract",
                    stages=stages,
                    page_count=ocr.get("pageCount"),
                    warnings=warnings + list(ocr.get("warnings") or []),
                    source_metadata={
                        "stampText": str(ocr.get("stampText") or ""),
                        "regionTexts": (
                            ocr.get("regionTexts")
                            if isinstance(ocr.get("regionTexts"), dict)
                            else {}
                        ),
                        "bomText": str(ocr.get("bomText") or ""),
                        "dimensionsText": str(ocr.get("dimensionsText") or ""),
                        "titleText": str(ocr.get("titleText") or ""),
                        "regions": ocr.get("regions") if isinstance(ocr.get("regions"), dict) else {},
                        "filename": filename,
                    },
                )
            elif ocr.get("warnings"):
                warnings.extend(ocr["warnings"])

        if backend == "auto":
            native = vision_service()._maybe_vlm_fallback(
                native,
                storage_path=storage_path,
                filename=filename,
                content_type=content_type,
                stages=stages,
                warnings=warnings,
            )

        return cls.finalize_result(
            native,
            engine=str(native.get("engine") or "native"),
            stages=stages,
            warnings=warnings,
            started=started,
        )

    @classmethod
    def build_from_text(
        cls,
        text: str,
        *,
        engine: str,
        stages: list[str],
        warnings: list[str] | None = None,
        page_count: int | None = None,
        source_metadata: dict | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_drawing_pdf_extraction_service import (
            ChatDrawingPdfExtractionService,
        )

        stamp_text = str((source_metadata or {}).get("stampText") or "").strip()
        attachment_filename = str((source_metadata or {}).get("filename") or "").strip()
        region_texts = (source_metadata or {}).get("regionTexts")

        if not isinstance(region_texts, dict):
            region_texts = {}

        bom_text = str(
            region_texts.get("bom")
            or (source_metadata or {}).get("bomText")
            or ""
        ).strip()
        dimensions_text = str(
            region_texts.get("dimensions")
            or (source_metadata or {}).get("dimensionsText")
            or ""
        ).strip()

        parse_metadata = {
            "extractor": engine,
            **(source_metadata or {}),
            "bomText": bom_text,
            "dimensionsText": dimensions_text,
        }

        parsed = ChatDrawingPdfExtractionService.parse_from_text(
            text,
            metadata=parse_metadata,
        )

        from app.domain.services.chat_drawing_product_code_resolution_service import (
            ChatDrawingProductCodeResolutionService,
        )

        filename_code = ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            attachment_filename
        )

        from app.domain.services.chat_drawing_stamp_extraction_service import (
            ChatDrawingStampExtractionService,
        )

        stamp_extract = ChatDrawingStampExtractionService.extract(
            stamp_text=stamp_text,
            title_text=ChatDrawingPdfExtractionService._title_scope_text(
                text,
                stamp_text=stamp_text,
            ),
            filename_code=filename_code,
        )

        if stamp_extract.get("productCode"):
            parsed["productCode"] = stamp_extract["productCode"]
            parsed["productCodeSource"] = stamp_extract.get("productCodeSource")

        if stamp_extract.get("revision") and not parsed.get("revision"):
            parsed["revision"] = stamp_extract["revision"]

        if stamp_extract.get("intermediateCodes"):
            parsed["intermediateCodes"] = sorted(
                set(list(parsed.get("intermediateCodes") or []))
                | set(stamp_extract.get("intermediateCodes") or [])
            )

        if stamp_extract.get("productCodeCandidates"):
            parsed["productCodeCandidates"] = stamp_extract["productCodeCandidates"]

        if stamp_extract.get("conflicts"):
            parsed["conflicts"] = stamp_extract["conflicts"]

        from app.domain.services.chat_document_vision_bom_service import (
            ChatDocumentVisionBomService,
        )

        bom_rows = ChatDocumentVisionBomService.extract_bom_rows(
            bom_text,
            exclude_product_code=parsed.get("productCode"),
            region_scoped=bool(bom_text),
        ) if bom_text else ChatDocumentVisionBomService.extract_bom_rows(
            text,
            exclude_product_code=parsed.get("productCode"),
        )

        bom_codes = ChatDocumentVisionBomService.bom_component_codes(bom_rows)

        if parsed.get("productCodeCandidates"):
            parsed["productCodeCandidates"] = (
                ChatDocumentVisionBomService.demote_bom_codes_in_candidates(
                    list(parsed.get("productCodeCandidates") or []),
                    bom_codes,
                )
            )

        if bom_rows:
            parsed["bomRows"] = bom_rows
            parsed["componentCodes"] = ChatDocumentVisionBomService.merge_component_codes_from_rows(
                list(parsed.get("componentCodes") or []),
                bom_rows,
            )
            stage_name = "bom_region" if bom_text else "bom_heuristic"

            if stage_name not in stages:
                stages = [*stages, stage_name]

        if dimensions_text:
            from app.domain.services.chat_drawing_dimensions_extraction_service import (
                ChatDrawingDimensionsExtractionService,
            )

            parsed["dimensions"] = ChatDrawingDimensionsExtractionService.merge_dimensions(
                parsed.get("dimensions") if isinstance(parsed.get("dimensions"), dict) else {},
                region_text=dimensions_text,
                fallback_text=text,
            )

            if "dimensions_ocr" not in stages:
                stages = [*stages, "dimensions_ocr"]

        if (
            filename_code
            and parsed.get("productCode")
            and filename_code != parsed["productCode"]
        ):
            parsed["conflicts"] = list(parsed.get("conflicts") or []) + [
                {
                    "type": "stamp_vs_filename",
                    "severity": "pending",
                    "filenameCode": filename_code,
                    "stampCode": parsed["productCode"],
                }
            ]

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        char_count = int(parsed.get("charCount") or 0)
        legibility_score = min(1.0, char_count / float(min_legible * 2))

        if parsed.get("productCode"):
            legibility_score = min(1.0, legibility_score + 0.25)

        from app.domain.services.chat_document_vision_title_block_service import (
            ChatDocumentVisionTitleBlockService,
        )

        title_block = ChatDrawingStampExtractionService.build_title_block(
            stamp_extract,
            raw_text=stamp_text or ChatDocumentVisionTitleBlockService._extract_stamp_snippet(text),
        )

        result = {
            **parsed,
            "schemaVersion": cls.SCHEMA_VERSION,
            "engine": engine,
            "stages": stages,
            "warnings": warnings or [],
            "fullText": text,
            "pageCount": page_count,
            "pagesProcessed": page_count,
            "legibilityScore": round(legibility_score, 3),
            "charCount": char_count,
        }

        if title_block:
            result["titleBlock"] = title_block

        from app.domain.services.chat_document_vision_tables_service import (
            ChatDocumentVisionTablesService,
        )

        tables = ChatDocumentVisionTablesService.extract_tables(text)

        if tables:
            result["tables"] = tables

            if "table_heuristic" not in stages:
                stages = [*stages, "table_heuristic"]
                result["stages"] = stages

        if isinstance(source_metadata, dict) and isinstance(source_metadata.get("regions"), dict):
            result["regions"] = source_metadata["regions"]

        return result

    @classmethod
    def finalize_result(
        cls,
        payload: dict[str, Any],
        *,
        engine: str,
        stages: list[str],
        warnings: list[str],
        started: float,
        vision_purpose: str | None = None,
    ) -> dict[str, Any]:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        bom_rows = payload.get("bomRows") if isinstance(payload.get("bomRows"), list) else []
        full_text = str(payload.get("fullText") or "")
        image_description = str(payload.get("imageDescription") or "").strip()
        char_count = int(payload.get("charCount") or 0)

        if not char_count and full_text:
            char_count = len(full_text.strip())

        return {
            "schemaVersion": cls.SCHEMA_VERSION,
            "engine": engine,
            "stages": stages,
            "durationMs": duration_ms,
            "warnings": warnings,
            "pageCount": payload.get("pageCount"),
            "pagesProcessed": payload.get("pagesProcessed") or payload.get("pageCount"),
            "legible": bool(payload.get("legible") or full_text.strip()),
            "legibilityScore": payload.get("legibilityScore"),
            "productCode": payload.get("productCode"),
            "productCodeSource": payload.get("productCodeSource"),
            "productCodeCandidates": payload.get("productCodeCandidates") or [],
            "conflicts": payload.get("conflicts") or [],
            "revision": payload.get("revision"),
            "internalRevision": payload.get("internalRevision"),
            "customerReference": payload.get("customerReference"),
            "description": payload.get("description"),
            "componentCodes": payload.get("componentCodes") or [],
            "intermediateCodes": payload.get("intermediateCodes") or [],
            "dimensions": payload.get("dimensions") or {},
            "titleBlock": payload.get("titleBlock"),
            "bomRows": bom_rows,
            "bomRowCount": len(bom_rows),
            "tables": payload.get("tables") if isinstance(payload.get("tables"), list) else [],
            "fullText": full_text,
            "imageDescription": image_description or None,
            "hasImageDescription": bool(image_description),
            "visionPurpose": vision_purpose or payload.get("visionPurpose"),
            "charCount": char_count,
            "regions": payload.get("regions") if isinstance(payload.get("regions"), dict) else {},
        }
