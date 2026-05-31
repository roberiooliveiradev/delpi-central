"""Visão e OCR de documentos no chat base — Onda 13."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.config.settings import Settings


class ChatDocumentVisionService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def is_enabled(cls) -> bool:
        return Settings.CHAT_DOCUMENT_VISION_ENABLED

    @classmethod
    def should_run_for_drawing(cls, skills: dict | None) -> bool:
        if not cls.is_enabled():
            return False

        resolved = skills if isinstance(skills, dict) else {}

        if resolved.get("documentVision"):
            return True

        return bool(
            Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING
            and resolved.get("drawingAnalysis")
        )

    @classmethod
    def enrich_drawing_extract(
        cls,
        parsed: dict[str, Any] | None,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
    ) -> dict[str, Any]:
        base = dict(parsed) if isinstance(parsed, dict) else {}

        if not cls.should_run_for_drawing(skills):
            return base

        attachment = cls._resolve_first_pdf_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return base

        vision = cls.extract_from_storage_path(
            attachment.storage_path,
            filename=attachment.original_filename,
            content_type=attachment.content_type or "application/pdf",
        )

        return cls.merge_into_drawing_parse(base, vision)

    @classmethod
    def extract_from_storage_path(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        content_type: str = "application/pdf",
    ) -> dict[str, Any]:
        started = time.perf_counter()
        backend = str(Settings.CHAT_DOCUMENT_VISION_BACKEND or "auto").strip().lower()
        stages: list[str] = []
        warnings: list[str] = []

        native = cls._stage_native(storage_path, filename=filename, content_type=content_type)
        stages.append("native")
        full_text = str(native.get("fullText") or "")
        char_count = len(full_text.strip())

        if backend in {"native", "text"}:
            return cls._finalize_result(
                native,
                engine="native",
                stages=stages,
                warnings=warnings,
                started=started,
            )

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        needs_ocr = backend in {"tesseract", "auto"} and (
            backend == "tesseract"
            or char_count < min_legible
            or not native.get("legible")
        )

        if needs_ocr and cls._is_pdf(content_type, filename, storage_path):
            ocr = cls._stage_tesseract_pdf(storage_path)
            stages.append("tesseract_pdf")

            if ocr.get("fullText"):
                merged_text = f"{full_text}\n\n{ocr['fullText']}".strip()
                native = cls._build_from_text(
                    merged_text,
                    engine=ocr.get("engine") or "tesseract",
                    stages=stages,
                    page_count=ocr.get("pageCount"),
                    warnings=warnings + list(ocr.get("warnings") or []),
                )
            elif ocr.get("warnings"):
                warnings.extend(ocr["warnings"])

        elif needs_ocr and cls._is_image(content_type, filename):
            ocr = cls._stage_tesseract_image(storage_path)
            stages.append("tesseract_image")

            if ocr.get("fullText"):
                merged_text = f"{full_text}\n\n{ocr['fullText']}".strip()
                native = cls._build_from_text(
                    merged_text,
                    engine="tesseract",
                    stages=stages,
                    warnings=warnings,
                )

        return cls._finalize_result(
            native,
            engine=str(native.get("engine") or "native"),
            stages=stages,
            warnings=warnings,
            started=started,
        )

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
            "customerReference",
            "description",
        ):
            if not merged.get(key) and doc.get(key):
                merged[key] = doc[key]

        for key in ("componentCodes", "intermediateCodes"):
            existing = list(merged.get(key) or [])
            incoming = doc.get(key)

            if not isinstance(incoming, list):
                incoming = []

            for code in incoming:
                if code and code not in existing:
                    existing.append(code)

            merged[key] = existing

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
        merged["documentVision"] = {
            "schemaVersion": doc.get("schemaVersion"),
            "engine": doc.get("engine"),
            "stages": doc.get("stages"),
            "legibilityScore": doc.get("legibilityScore"),
            "durationMs": doc.get("durationMs"),
        }

        return merged

    @classmethod
    def _resolve_first_pdf_attachment(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ):
        if not user_id or not session_id or not attachment_ids:
            return None

        try:
            from app.infrastructure.persistence.postgres_chat_attachment_repository import (
                PostgresChatAttachmentRepository,
            )

            repository = PostgresChatAttachmentRepository()
            ids = []

            for raw in attachment_ids:
                try:
                    ids.append(UUID(str(raw)))
                except (TypeError, ValueError):
                    continue

            if not ids:
                return None

            attachments = repository.list_attachments_by_ids(
                user_id=UUID(str(user_id)),
                session_id=UUID(str(session_id)),
                attachment_ids=ids,
            )
        except Exception:
            return None

        for attachment in attachments:
            name = str(attachment.original_filename or "").lower()
            content_type = str(attachment.content_type or "").lower()

            if content_type == "application/pdf" or name.endswith(".pdf"):
                return attachment

        return None

    @classmethod
    def _stage_native(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        from app.application.services.chat_attachment_text_extractor import (
            ChatAttachmentTextExtractor,
        )

        extracted = ChatAttachmentTextExtractor().extract(
            storage_path=storage_path,
            filename=filename or Path(storage_path).name,
            content_type=content_type,
        )

        if not extracted.get("supported"):
            return cls._build_from_text(
                "",
                engine="native",
                stages=["native"],
                warnings=[
                    str((extracted.get("metadata") or {}).get("reason") or "unsupported"),
                ],
            )

        text = str(extracted.get("content") or "").strip()
        metadata = extracted.get("metadata") if isinstance(extracted.get("metadata"), dict) else {}

        return cls._build_from_text(
            text,
            engine=str(metadata.get("extractor") or "native"),
            stages=["native"],
            source_metadata=metadata,
        )

    @classmethod
    def _stage_tesseract_pdf(cls, storage_path: str) -> dict[str, Any]:
        try:
            import fitz
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            return {
                "fullText": "",
                "warnings": [f"dependencies_unavailable:{exc.__class__.__name__}"],
            }

        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        dpi = max(72, int(Settings.CHAT_DOCUMENT_VISION_DPI))
        max_pages = max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_PAGES))
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        texts: list[str] = []
        warnings: list[str] = []

        try:
            document = fitz.open(storage_path)
        except Exception as exc:
            return {
                "fullText": "",
                "warnings": [f"pdf_open_failed:{exc.__class__.__name__}"],
            }

        try:
            page_count = min(document.page_count, max_pages)

            if document.page_count > max_pages:
                warnings.append(f"truncated_pages:{document.page_count}>{max_pages}")

            for index in range(page_count):
                page = document.load_page(index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                raw = pytesseract.image_to_string(image, lang=lang)
                chunk = str(raw or "").strip()

                if chunk:
                    texts.append(chunk)
        finally:
            document.close()

        return {
            "fullText": "\n\n".join(texts).strip(),
            "engine": "tesseract",
            "pageCount": page_count if "page_count" in locals() else 0,
            "warnings": warnings,
        }

    @classmethod
    def _stage_tesseract_image(cls, storage_path: str) -> dict[str, Any]:
        from app.application.services.chat_attachment_image_ocr_service import (
            ChatAttachmentImageOcrService,
        )

        result = ChatAttachmentImageOcrService.try_extract_text(Path(storage_path))

        return {
            "fullText": str(result.get("text") or "").strip(),
            "engine": "tesseract",
            "warnings": [str(result.get("reason"))] if result.get("reason") else [],
        }

    @classmethod
    def _build_from_text(
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

        parsed = ChatDrawingPdfExtractionService.parse_from_text(
            text,
            metadata={"extractor": engine, **(source_metadata or {})},
        )

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        char_count = int(parsed.get("charCount") or 0)
        legibility_score = min(1.0, char_count / float(min_legible * 2))

        if parsed.get("productCode"):
            legibility_score = min(1.0, legibility_score + 0.25)

        return {
            **parsed,
            "schemaVersion": cls.SCHEMA_VERSION,
            "engine": engine,
            "stages": stages,
            "warnings": warnings or [],
            "fullText": text,
            "pageCount": page_count,
            "legibilityScore": round(legibility_score, 3),
            "charCount": char_count,
        }

    @classmethod
    def _finalize_result(
        cls,
        payload: dict[str, Any],
        *,
        engine: str,
        stages: list[str],
        warnings: list[str],
        started: float,
    ) -> dict[str, Any]:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        return {
            "schemaVersion": cls.SCHEMA_VERSION,
            "engine": engine,
            "stages": stages,
            "durationMs": duration_ms,
            "warnings": warnings,
            "pageCount": payload.get("pageCount"),
            "legible": bool(payload.get("legible")),
            "legibilityScore": payload.get("legibilityScore"),
            "productCode": payload.get("productCode"),
            "revision": payload.get("revision"),
            "customerReference": payload.get("customerReference"),
            "description": payload.get("description"),
            "componentCodes": payload.get("componentCodes") or [],
            "intermediateCodes": payload.get("intermediateCodes") or [],
            "dimensions": payload.get("dimensions") or {},
            "fullText": payload.get("fullText") or "",
            "charCount": int(payload.get("charCount") or 0),
        }

    @classmethod
    def _is_pdf(cls, content_type: str, filename: str, storage_path: str) -> bool:
        lowered = f"{content_type} {filename} {storage_path}".lower()
        return "pdf" in lowered or lowered.endswith(".pdf")

    @classmethod
    def _is_image(cls, content_type: str, filename: str) -> bool:
        lowered = f"{content_type} {filename}".lower()
        return any(
            token in lowered
            for token in ("image/png", "image/jpeg", "image/jpg", "image/webp", ".png", ".jpg", ".jpeg")
        )
