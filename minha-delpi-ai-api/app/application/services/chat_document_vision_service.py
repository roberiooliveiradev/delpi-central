"""Visão e OCR de documentos no chat base — Onda 13."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
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
    def _auto_vlm_fallback_enabled(cls) -> bool:
        return bool(
            Settings.CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK
            and Settings.CHAT_DOCUMENT_VISION_OLLAMA_MODEL
        )

    @classmethod
    def _needs_vlm_fallback(cls, text: str, *, legible: bool | None = None) -> bool:
        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        normalized = str(text or "").strip()

        if legible is False:
            return True

        return len(normalized) < min_legible

    @classmethod
    def _maybe_vlm_fallback(
        cls,
        payload: dict[str, Any],
        *,
        storage_path: str,
        filename: str,
        content_type: str,
        stages: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        if not cls._auto_vlm_fallback_enabled():
            return payload

        if not cls._needs_vlm_fallback(
            str(payload.get("fullText") or ""),
            legible=payload.get("legible"),
        ):
            return payload

        vlm = cls._stage_ollama_vlm(
            storage_path,
            filename=filename,
            content_type=content_type,
        )
        warnings.extend(vlm.get("warnings") or [])

        vlm_text = str(vlm.get("fullText") or "").strip()

        if not vlm_text:
            warnings.append("ollama_vlm_fallback_empty")
            return payload

        stages.append("ollama_vlm")
        return cls._build_from_text(
            vlm_text,
            engine="ollama_vlm",
            stages=stages,
            page_count=payload.get("pageCount"),
            warnings=warnings,
            source_metadata={"vlmFallback": True},
        )

    @classmethod
    def should_run_for_attachment(cls, skills: dict | None = None) -> bool:
        if not cls.is_enabled():
            return False

        resolved = skills if isinstance(skills, dict) else {}

        if resolved.get("documentVision"):
            return True

        if (
            Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING
            and resolved.get("drawingAnalysis")
        ):
            return True

        return cls.is_enabled()

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

        attachment = cls._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return base

        vision = cls.extract_from_storage_path(
            attachment.storage_path,
            filename=attachment.original_filename,
            content_type=attachment.content_type
            or cls._default_content_type(attachment.original_filename),
        )

        return cls.merge_into_drawing_parse(base, vision)

    @classmethod
    def to_document_vision_metadata(cls, vision: dict[str, Any]) -> dict[str, Any]:
        bom_rows = vision.get("bomRows") if isinstance(vision.get("bomRows"), list) else []

        title_block = vision.get("titleBlock")

        return {
            "schemaVersion": vision.get("schemaVersion") or cls.SCHEMA_VERSION,
            "engine": vision.get("engine"),
            "stages": vision.get("stages") or [],
            "legibilityScore": vision.get("legibilityScore"),
            "durationMs": vision.get("durationMs"),
            "charCount": vision.get("charCount"),
            "legible": vision.get("legible"),
            "pageCount": vision.get("pageCount"),
            "pagesProcessed": vision.get("pagesProcessed") or vision.get("pageCount"),
            "bomRowCount": len(bom_rows),
            "hasTitleBlock": bool(title_block),
            "tableCount": len(vision.get("tables") or [])
            if isinstance(vision.get("tables"), list)
            else 0,
        }

    @classmethod
    def _compute_vision_for_attachment(
        cls,
        attachment,
        *,
        skills: dict | None = None,
    ) -> dict[str, Any] | None:
        if not cls.should_run_for_attachment(skills):
            return None

        filename = attachment.original_filename or ""
        content_type = attachment.content_type or cls._default_content_type(filename)

        if not cls._is_vision_target(content_type, filename, attachment.storage_path):
            return None

        if str(attachment.status or "").lower() == "indexed":
            native = cls._stage_native(
                attachment.storage_path,
                filename=filename,
                content_type=content_type,
            )
            text = str(native.get("fullText") or "").strip()
            min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))

            if len(text) < min_legible:
                return cls.extract_from_storage_path(
                    attachment.storage_path,
                    filename=filename,
                    content_type=content_type,
                )

            started = time.perf_counter()
            built = cls._build_from_text(
                text,
                engine=str(native.get("engine") or "native"),
                stages=["native"],
                source_metadata=native.get("metadata") if isinstance(native.get("metadata"), dict) else {},
            )

            return cls._finalize_result(
                built,
                engine=str(built.get("engine") or "native"),
                stages=["native"],
                warnings=[],
                started=started,
            )

        return cls.extract_from_storage_path(
            attachment.storage_path,
            filename=filename,
            content_type=content_type,
        )

    @classmethod
    def persist_attachment_vision_metadata(
        cls,
        attachment,
        vision_meta: dict[str, Any],
    ) -> None:
        if not attachment or not vision_meta:
            return

        try:
            attachment_id = UUID(str(attachment.id))
        except (TypeError, ValueError):
            return

        try:
            from datetime import datetime, timezone

            from app.infrastructure.persistence.postgres_chat_attachment_repository import (
                PostgresChatAttachmentRepository,
            )

            PostgresChatAttachmentRepository().update_status(
                attachment_id=attachment_id,
                status=str(attachment.status or "ready"),
                metadata={
                    "documentVision": vision_meta,
                    "documentVisionAt": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            return

    @classmethod
    def refresh_attachment_vision_snapshot(
        cls,
        attachment,
        *,
        skills: dict | None = None,
        persist: bool = True,
    ) -> dict[str, Any] | None:
        """Recalcula visão/OCR e opcionalmente grava em `attachment.metadata.documentVision`."""
        vision = cls._compute_vision_for_attachment(attachment, skills=skills)

        if not vision:
            return None

        meta = cls.to_document_vision_metadata(vision)

        if persist:
            cls.persist_attachment_vision_metadata(attachment, meta)

        return meta

    @classmethod
    def build_attachment_vision_metadata(
        cls,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        attachment_ids: list | None = None,
        skills: dict | None = None,
        persist: bool = True,
    ) -> dict[str, Any] | None:
        """Snapshot leve para metadata/adminDebug em turnos só com anexo (ex.: boleto PDF)."""
        attachment = cls._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return None

        vision = cls._compute_vision_for_attachment(attachment, skills=skills)

        if not vision:
            return None

        meta = cls.to_document_vision_metadata(vision)

        if persist:
            cls.persist_attachment_vision_metadata(attachment, meta)

        return meta

    @classmethod
    def enrich_attachment_excerpt(
        cls,
        *,
        storage_path: str,
        filename: str,
        content_type: str | None,
        extracted_content: str,
        skills: dict | None = None,
    ) -> str:
        if not cls.should_run_for_attachment(skills):
            return extracted_content

        if not cls._is_vision_target(content_type, filename, storage_path):
            return extracted_content

        vision = cls.extract_from_storage_path(
            storage_path,
            filename=filename,
            content_type=content_type or cls._default_content_type(filename),
        )
        ocr_text = str(vision.get("fullText") or "").strip()

        if not ocr_text:
            return extracted_content

        if cls._should_replace_attachment_content(extracted_content, ocr_text):
            return ocr_text

        return f"{extracted_content.strip()}\n\n{ocr_text}".strip()

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

        if cls._is_image(content_type, filename):
            return cls._extract_image_document(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
                started=started,
            )

        if backend in {"ollama_vlm", "vlm"}:
            vlm = cls._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
            )

            if str(vlm.get("fullText") or "").strip():
                stages.append("ollama_vlm")
                return cls._finalize_result(
                    vlm,
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=list(vlm.get("warnings") or []),
                    started=started,
                )

            warnings.append("ollama_vlm_unavailable_fallback_auto")
            backend = "auto"

        if backend in {"docling", "paddleocr"}:
            neural = cls._stage_neural_backend(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
            )

            if str(neural.get("fullText") or "").strip():
                stages.append(backend)
                return cls._finalize_result(
                    neural,
                    engine=backend,
                    stages=stages,
                    warnings=list(neural.get("warnings") or []),
                    started=started,
                )

            warnings.append(f"{backend}_unavailable_fallback_auto")
            backend = "auto"

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

            if ocr.get("stampCrop"):
                stages.append("tesseract_stamp_crop")

            if ocr.get("fullText"):
                merged_text = f"{full_text}\n\n{ocr['fullText']}".strip()
                native = cls._build_from_text(
                    merged_text,
                    engine=ocr.get("engine") or "tesseract",
                    stages=stages,
                    page_count=ocr.get("pageCount"),
                    warnings=warnings + list(ocr.get("warnings") or []),
                    source_metadata={"stampText": str(ocr.get("stampText") or "")},
                )
            elif ocr.get("warnings"):
                warnings.extend(ocr["warnings"])

        if backend == "auto":
            native = cls._maybe_vlm_fallback(
                native,
                storage_path=storage_path,
                filename=filename,
                content_type=content_type,
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
            merged["bomHints"] = cls._bom_rows_to_hints(bom_rows)

        if title_block:
            merged["titleBlock"] = title_block

            fields = title_block.get("fields") if isinstance(title_block.get("fields"), dict) else {}

            if not merged.get("productCode") and fields.get("code"):
                merged["productCode"] = fields["code"]

            if not merged.get("revision") and fields.get("rev"):
                merged["revision"] = fields["rev"]

        return merged

    @classmethod
    def _bom_rows_to_hints(cls, bom_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    @classmethod
    def _resolve_first_document_attachment(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ):
        attachments = cls._list_attachments(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachments:
            return None

        pdf_match = None
        image_match = None

        for attachment in attachments:
            name = str(attachment.original_filename or "").lower()
            content_type = str(attachment.content_type or "").lower()

            if content_type == "application/pdf" or name.endswith(".pdf"):
                return attachment

            if image_match is None and cls._is_image(content_type, name):
                image_match = attachment

        return image_match

    @classmethod
    def _list_attachments(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ):
        if not user_id or not session_id or not attachment_ids:
            return []

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
                return []

            return repository.list_attachments_by_ids(
                user_id=UUID(str(user_id)),
                session_id=UUID(str(session_id)),
                attachment_ids=ids,
            )
        except Exception:
            return []

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

            stamp_crop_used = False
            stamp_text = ""

            for index in range(page_count):
                page = document.load_page(index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                raw = pytesseract.image_to_string(image, lang=lang)
                chunk = str(raw or "").strip()

                if chunk:
                    texts.append(chunk)

                if index == 0 and Settings.CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED:
                    cropped = cls._ocr_stamp_regions(page, matrix=matrix, lang=lang)

                    if cropped and cropped not in chunk:
                        texts.append(cropped)
                        stamp_text = cropped
                        stamp_crop_used = True
        finally:
            document.close()

        if stamp_crop_used:
            warnings.append("stamp_crop_applied")

        return {
            "fullText": "\n\n".join(texts).strip(),
            "engine": "tesseract",
            "pageCount": page_count if "page_count" in locals() else 0,
            "warnings": warnings,
            "stampCrop": stamp_crop_used,
            "stampText": stamp_text if stamp_crop_used else "",
        }

    @classmethod
    def _extract_image_document(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
        backend: str,
        started: float,
    ) -> dict[str, Any]:
        stages: list[str] = []
        warnings: list[str] = []
        merged_text = ""

        if backend in {"ollama_vlm", "vlm"}:
            vlm = cls._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
            )
            warnings.extend(vlm.get("warnings") or [])

            if str(vlm.get("fullText") or "").strip():
                stages.append("ollama_vlm")
                payload = cls._build_from_text(
                    str(vlm["fullText"]),
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                )
                return cls._finalize_result(
                    payload,
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                    started=started,
                )

            warnings.append("ollama_vlm_unavailable_fallback_auto")
            backend = "tesseract"

        if backend in {"docling", "paddleocr"}:
            neural = cls._stage_neural_backend(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
            )
            warnings.extend(neural.get("warnings") or [])

            if str(neural.get("fullText") or "").strip():
                stages.append(backend)
                return cls._finalize_result(
                    neural,
                    engine=backend,
                    stages=stages,
                    warnings=warnings,
                    started=started,
                )

            warnings.append(f"{backend}_unavailable_fallback_tesseract")
            backend = "tesseract"

        if backend in {"native", "text"}:
            native = cls._stage_native(
                storage_path,
                filename=filename,
                content_type=content_type,
            )
            stages.append("native")
            merged_text = str(native.get("fullText") or "").strip()
            warnings.extend(native.get("warnings") or [])

        if backend in {"tesseract", "auto", "paddleocr", "docling"}:
            ocr = cls._stage_tesseract_image(storage_path)
            stages.append("tesseract_image")
            warnings.extend(ocr.get("warnings") or [])

            ocr_text = str(ocr.get("fullText") or "").strip()

            if ocr_text:
                merged_text = (
                    f"{merged_text}\n\n{ocr_text}".strip()
                    if merged_text
                    else ocr_text
                )

        if not merged_text and backend in {"tesseract", "auto"}:
            warnings.append("no_text_detected")

        payload = cls._build_from_text(
            merged_text,
            engine="tesseract" if "tesseract_image" in stages else "native",
            stages=stages or ["native"],
            warnings=warnings,
        )

        if backend == "auto":
            payload = cls._maybe_vlm_fallback(
                payload,
                storage_path=storage_path,
                filename=filename,
                content_type=content_type,
                stages=stages,
                warnings=warnings,
            )

        return cls._finalize_result(
            payload,
            engine=str(payload.get("engine") or "tesseract"),
            stages=stages or ["tesseract_image"],
            warnings=warnings,
            started=started,
        )

    @classmethod
    def _stage_tesseract_image(cls, storage_path: str) -> dict[str, Any]:
        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        max_chars = max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_CHARS))

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            return {
                "fullText": "",
                "engine": "tesseract",
                "warnings": [f"dependencies_unavailable:{exc.__class__.__name__}"],
            }

        try:
            with Image.open(storage_path) as image:
                rgb = image.convert("RGB")
                raw = pytesseract.image_to_string(rgb, lang=lang)
        except Exception as exc:
            return {
                "fullText": "",
                "engine": "tesseract",
                "warnings": [f"ocr_failed:{exc.__class__.__name__}"],
            }

        text = " ".join(str(raw or "").split()).strip()

        if not text:
            return {
                "fullText": "",
                "engine": "tesseract",
                "warnings": ["no_text_detected"],
            }

        if len(text) > max_chars:
            text = f"{text[: max_chars - 1]}…"

        return {
            "fullText": text,
            "engine": "tesseract",
            "charCount": len(text),
            "warnings": [],
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

        from app.domain.services.chat_document_vision_bom_service import (
            ChatDocumentVisionBomService,
        )

        bom_rows = ChatDocumentVisionBomService.extract_bom_rows(
            text,
            exclude_product_code=parsed.get("productCode"),
        )

        if bom_rows:
            parsed["bomRows"] = bom_rows
            parsed["componentCodes"] = ChatDocumentVisionBomService.merge_component_codes_from_rows(
                list(parsed.get("componentCodes") or []),
                bom_rows,
            )
            if "bom_heuristic" not in stages:
                stages = [*stages, "bom_heuristic"]

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
        char_count = int(parsed.get("charCount") or 0)
        legibility_score = min(1.0, char_count / float(min_legible * 2))

        if parsed.get("productCode"):
            legibility_score = min(1.0, legibility_score + 0.25)

        from app.domain.services.chat_document_vision_title_block_service import (
            ChatDocumentVisionTitleBlockService,
        )

        stamp_text = str((source_metadata or {}).get("stampText") or "").strip()
        title_block = ChatDocumentVisionTitleBlockService.build(
            text=text,
            product_code=parsed.get("productCode"),
            revision=parsed.get("revision"),
            stamp_text=stamp_text or None,
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

        return result

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

        bom_rows = payload.get("bomRows") if isinstance(payload.get("bomRows"), list) else []

        return {
            "schemaVersion": cls.SCHEMA_VERSION,
            "engine": engine,
            "stages": stages,
            "durationMs": duration_ms,
            "warnings": warnings,
            "pageCount": payload.get("pageCount"),
            "pagesProcessed": payload.get("pagesProcessed") or payload.get("pageCount"),
            "legible": bool(payload.get("legible")),
            "legibilityScore": payload.get("legibilityScore"),
            "productCode": payload.get("productCode"),
            "revision": payload.get("revision"),
            "customerReference": payload.get("customerReference"),
            "description": payload.get("description"),
            "componentCodes": payload.get("componentCodes") or [],
            "intermediateCodes": payload.get("intermediateCodes") or [],
            "dimensions": payload.get("dimensions") or {},
            "titleBlock": payload.get("titleBlock"),
            "bomRows": bom_rows,
            "bomRowCount": len(bom_rows),
            "tables": payload.get("tables") if isinstance(payload.get("tables"), list) else [],
            "titleBlock": payload.get("titleBlock"),
            "fullText": payload.get("fullText") or "",
            "charCount": int(payload.get("charCount") or 0),
        }

    @classmethod
    def _ocr_stamp_regions(cls, page, *, matrix, lang: str) -> str:
        """Recorte heurístico do carimbo (faixa superior + canto superior direito)."""
        try:
            import fitz
            import pytesseract
            from PIL import Image
        except ImportError:
            return ""

        width = float(page.rect.width)
        height = float(page.rect.height)
        regions = (
            fitz.Rect(0, 0, width, height * 0.32),
            fitz.Rect(width * 0.42, 0, width, height * 0.38),
        )
        parts: list[str] = []

        for rect in regions:
            pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            text = str(pytesseract.image_to_string(image, lang=lang) or "").strip()

            if text and text not in parts:
                parts.append(text)

        return "\n".join(parts).strip()

    @classmethod
    def _vision_timeout_seconds(cls) -> float:
        return max(5.0, float(Settings.CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS))

    @classmethod
    def _truncate_vision_text(cls, text: str) -> str:
        max_chars = max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_CHARS))
        normalized = str(text or "").strip()

        if len(normalized) <= max_chars:
            return normalized

        return f"{normalized[: max_chars - 1]}…"

    @classmethod
    def _rasterize_pdf_pages(cls, storage_path: str) -> tuple[list[Any], list[str]]:
        warnings: list[str] = []

        try:
            import fitz
            from PIL import Image
        except ImportError as exc:
            return [], [f"dependencies_unavailable:{exc.__class__.__name__}"]

        dpi = max(72, int(Settings.CHAT_DOCUMENT_VISION_DPI))
        max_pages = max(1, int(Settings.CHAT_DOCUMENT_VISION_MAX_PAGES))
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        images: list[Any] = []

        try:
            document = fitz.open(storage_path)
        except Exception as exc:
            return [], [f"pdf_open_failed:{exc.__class__.__name__}"]

        try:
            for index, page in enumerate(document):
                if index >= max_pages:
                    warnings.append("max_pages_reached")
                    break

                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                images.append(
                    Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                )
        finally:
            document.close()

        return images, warnings

    @classmethod
    def _pil_to_base64_png(cls, image: Any) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @classmethod
    def _stage_ollama_vlm(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        warnings: list[str] = []
        model = Settings.CHAT_DOCUMENT_VISION_OLLAMA_MODEL
        base_url = (
            Settings.CHAT_DOCUMENT_VISION_OLLAMA_BASE_URL
            or Settings.OLLAMA_BASE_URL
        ).strip().rstrip("/")
        max_vlm_pages = max(1, min(3, int(Settings.CHAT_DOCUMENT_VISION_MAX_PAGES)))

        try:
            import requests
        except ImportError:
            warnings.append("requests_unavailable")
            return {"fullText": "", "warnings": warnings}

        images_b64: list[str] = []

        if cls._is_pdf(content_type, filename, storage_path):
            pages, page_warnings = cls._rasterize_pdf_pages(storage_path)
            warnings.extend(page_warnings)
            images_b64 = [cls._pil_to_base64_png(page) for page in pages[:max_vlm_pages]]
        elif cls._is_image(content_type, filename):
            try:
                from PIL import Image

                with Image.open(storage_path) as image:
                    images_b64 = [cls._pil_to_base64_png(image.convert("RGB"))]
            except Exception as exc:
                warnings.append(f"vlm_image_open_failed:{exc.__class__.__name__}")
        else:
            warnings.append("vlm_unsupported_content_type")
            return {"fullText": "", "warnings": warnings}

        if not images_b64:
            warnings.append("vlm_no_images")
            return {"fullText": "", "warnings": warnings}

        prompt = (
            "Extraia todo o texto visível deste documento técnico "
            "(carimbo, lista de materiais, cotas, notas). "
            "Responda apenas com o texto extraído, sem comentários."
        )
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": images_b64,
                }
            ],
            "stream": False,
            "options": {"num_predict": min(4096, int(Settings.CHAT_DOCUMENT_VISION_MAX_CHARS))},
        }

        try:
            response = requests.post(url, json=payload, timeout=cls._vision_timeout_seconds())
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            warnings.append(f"ollama_vlm_request_failed:{exc.__class__.__name__}")
            return {"fullText": "", "warnings": warnings}

        message = data.get("message") if isinstance(data, dict) else {}
        content = str((message or {}).get("content") or "").strip()

        if not content:
            warnings.append("ollama_vlm_empty_response")
            return {"fullText": "", "warnings": warnings}

        text = cls._truncate_vision_text(content)
        return cls._build_from_text(
            text,
            engine="ollama_vlm",
            stages=["ollama_vlm"],
            warnings=warnings,
        )

    @classmethod
    def _stage_neural_backend(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
        backend: str,
    ) -> dict[str, Any]:
        """Backends opcionais (Docling/Paddle) — profile vision; fallback para auto se indisponível."""
        warnings: list[str] = []

        try:
            if backend == "docling":
                return cls._stage_docling(storage_path, filename=filename, warnings=warnings)

            if backend == "paddleocr":
                return cls._stage_paddleocr(storage_path, filename=filename, warnings=warnings)
        except Exception as exc:
            warnings.append(f"{backend}_error:{exc.__class__.__name__}")

        return {"fullText": "", "warnings": warnings}

    @classmethod
    def _stage_docling(cls, storage_path: str, *, filename: str, warnings: list[str]) -> dict[str, Any]:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            warnings.append("docling_not_installed")
            return {"fullText": "", "warnings": warnings}

        try:
            converter = DocumentConverter()
            result = converter.convert(storage_path)
            document = result.document
            text = ""

            if hasattr(document, "export_to_markdown"):
                text = str(document.export_to_markdown() or "")
            elif hasattr(document, "export_to_text"):
                text = str(document.export_to_text() or "")
        except Exception as exc:
            warnings.append(f"docling_failed:{exc.__class__.__name__}")
            return {"fullText": "", "warnings": warnings}

        text = cls._truncate_vision_text(text)

        if not text:
            warnings.append("docling_empty_text")
            return {"fullText": "", "warnings": warnings}

        return cls._build_from_text(
            text,
            engine="docling",
            stages=["docling"],
            warnings=warnings,
        )

    @classmethod
    def _stage_paddleocr(
        cls,
        storage_path: str,
        *,
        filename: str,
        warnings: list[str],
    ) -> dict[str, Any]:
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            warnings.append("paddleocr_not_installed")
            return {"fullText": "", "warnings": warnings}

        use_gpu = os.getenv("CHAT_DOCUMENT_VISION_PADDLE_USE_GPU", "false").lower() == "true"

        try:
            engine = PaddleOCR(use_angle_cls=True, lang="por", use_gpu=use_gpu, show_log=False)
        except Exception as exc:
            warnings.append(f"paddleocr_init_failed:{exc.__class__.__name__}")
            return {"fullText": "", "warnings": warnings}

        parts: list[str] = []
        content_type = cls._default_content_type(filename)

        if cls._is_pdf(content_type, filename, storage_path):
            pages, page_warnings = cls._rasterize_pdf_pages(storage_path)
            warnings.extend(page_warnings)

            for page in pages:
                segment = cls._paddleocr_from_image(engine, page)

                if segment:
                    parts.append(segment)
        else:
            segment = cls._paddleocr_from_path(engine, storage_path)

            if segment:
                parts.append(segment)

        text = cls._truncate_vision_text("\n\n".join(parts).strip())

        if not text:
            warnings.append("paddleocr_empty_text")
            return {"fullText": "", "warnings": warnings}

        return cls._build_from_text(
            text,
            engine="paddleocr",
            stages=["paddleocr"],
            warnings=warnings,
        )

    @classmethod
    def _paddleocr_from_path(cls, engine: Any, storage_path: str) -> str:
        try:
            from PIL import Image
        except ImportError:
            return ""

        try:
            with Image.open(storage_path) as image:
                return cls._paddleocr_from_image(engine, image.convert("RGB"))
        except Exception:
            return ""

    @classmethod
    def _paddleocr_from_image(cls, engine: Any, image: Any) -> str:
        try:
            import numpy as np
        except ImportError:
            return ""

        try:
            array = np.array(image)
            result = engine.ocr(array, cls=True)
        except Exception:
            return ""

        lines: list[str] = []

        for block in result or []:
            if not isinstance(block, list):
                continue

            for item in block:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue

                text_part = item[1]

                if isinstance(text_part, (list, tuple)) and text_part:
                    line = str(text_part[0] or "").strip()

                    if line:
                        lines.append(line)

        return "\n".join(lines).strip()

    @classmethod
    def _is_pdf(cls, content_type: str, filename: str, storage_path: str) -> bool:
        lowered = f"{content_type} {filename} {storage_path}".lower()
        return "pdf" in lowered or lowered.endswith(".pdf")

    @classmethod
    def _is_image(cls, content_type: str, filename: str) -> bool:
        lowered = f"{content_type} {filename}".lower()
        return any(
            token in lowered
            for token in (
                "image/png",
                "image/jpeg",
                "image/jpg",
                "image/webp",
                "image/tiff",
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".tif",
                ".tiff",
            )
        )

    @classmethod
    def _is_vision_target(cls, content_type: str | None, filename: str, storage_path: str) -> bool:
        content_type = str(content_type or "")
        filename = str(filename or "")

        return cls._is_pdf(content_type, filename, storage_path) or cls._is_image(
            content_type,
            filename,
        )

    @classmethod
    def _default_content_type(cls, filename: str) -> str:
        lowered = str(filename or "").lower()

        if lowered.endswith(".pdf"):
            return "application/pdf"

        if lowered.endswith(".png"):
            return "image/png"

        if lowered.endswith(".webp"):
            return "image/webp"

        if lowered.endswith((".jpg", ".jpeg")):
            return "image/jpeg"

        return "application/octet-stream"

    @classmethod
    def _should_replace_attachment_content(cls, extracted: str, ocr_text: str) -> bool:
        normalized = str(extracted or "").strip()

        if not normalized:
            return True

        placeholders = (
            "Conteúdo visual indexado por metadados",
            "descreva o que precisa",
            "texto alternativo",
        )

        if any(token in normalized for token in placeholders):
            return True

        min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))

        return len(normalized) < min_legible and len(ocr_text) >= min_legible
