"""Visão e OCR de documentos no chat base — Onda 13."""

from __future__ import annotations

import base64
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.infrastructure.config.settings import Settings


def _default_attachment_repository() -> ChatAttachmentRepositoryPort:
    from app.composition.repository_composer import make_chat_attachment_repository

    return make_chat_attachment_repository()


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
    def _image_describe_enabled(cls) -> bool:
        return bool(
            Settings.CHAT_DOCUMENT_VISION_IMAGE_DESCRIBE_ENABLED
            and Settings.CHAT_DOCUMENT_VISION_OLLAMA_MODEL
        )

    @classmethod
    def _resolve_vision_purpose(
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
        vision_purpose: str | None = None,
    ) -> dict[str, Any]:
        if not cls._auto_vlm_fallback_enabled():
            return payload

        if not cls._needs_vlm_fallback(
            str(payload.get("fullText") or ""),
            legible=payload.get("legible"),
        ):
            return payload

        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
        fallback_purpose = (
            describe_purpose
            if cls._is_image(content_type, filename) and cls._image_describe_enabled()
            else ChatDocumentVisionContentService.vision_purpose("ocr")
        )
        if vision_purpose:
            fallback_purpose = vision_purpose

        vlm = cls._stage_ollama_vlm(
            storage_path,
            filename=filename,
            content_type=content_type,
            purpose=fallback_purpose,
        )
        warnings.extend(vlm.get("warnings") or [])

        if fallback_purpose == describe_purpose:
            image_description = str(vlm.get("imageDescription") or "").strip()

            if not image_description:
                warnings.append("ollama_vlm_describe_fallback_empty")
                return payload

            stages.append("ollama_vlm_describe")
            merged = dict(payload)
            merged["imageDescription"] = image_description
            merged["engine"] = "ollama_vlm"
            merged["visionPurpose"] = describe_purpose
            return merged

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
    def should_run_for_attachment(
        cls,
        skills: dict | None = None,
        *,
        intent_route: str | None = None,
        has_agent: bool = False,
        message: str | None = None,
    ) -> bool:
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )

        return ChatDocumentVisionSkillService.should_run_for_attachment_turn(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
            message=message,
        )

    @classmethod
    def should_run_for_drawing(cls, skills: dict | None) -> bool:
        from app.domain.services.chat_document_vision_skill_service import (
            ChatDocumentVisionSkillService,
        )

        return ChatDocumentVisionSkillService.should_run_for_drawing(skills)

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

        merged = cls.merge_into_drawing_parse(base, vision)

        if vision:
            cls.persist_attachment_vision_metadata(
                attachment,
                cls.to_document_vision_metadata(vision),
            )

        return merged

    @classmethod
    def to_document_vision_metadata(cls, vision: dict[str, Any]) -> dict[str, Any]:
        bom_rows = vision.get("bomRows") if isinstance(vision.get("bomRows"), list) else []

        title_block = vision.get("titleBlock")
        text_excerpt = cls._truncate_vision_text(str(vision.get("fullText") or ""))
        image_description = cls._truncate_vision_text(
            str(vision.get("imageDescription") or "")
        )

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
            "visionPurpose": vision.get("visionPurpose"),
            "textExcerpt": text_excerpt or None,
            "imageDescription": image_description or None,
            "hasImageDescription": bool(image_description),
            "filename": vision.get("filename"),
        }

    @classmethod
    def _compute_vision_for_attachment(
        cls,
        attachment,
        *,
        skills: dict | None = None,
        message: str | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> dict[str, Any] | None:
        if not cls.should_run_for_attachment(
            skills,
            intent_route=intent_route,
            has_agent=has_agent,
            message=message,
        ):
            return None

        filename = attachment.original_filename or ""
        content_type = attachment.content_type or cls._default_content_type(filename)

        if not cls._is_vision_target(content_type, filename, attachment.storage_path):
            return None

        if str(attachment.status or "").lower() == "indexed":
            from app.domain.services.chat_document_vision_content_service import (
                ChatDocumentVisionContentService,
            )

            purpose = cls._resolve_vision_purpose(
                message,
                content_type=content_type,
                filename=filename,
            )
            describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
            hybrid_purpose = ChatDocumentVisionContentService.vision_purpose("hybrid")

            native = cls._stage_native(
                attachment.storage_path,
                filename=filename,
                content_type=content_type,
            )
            text = str(native.get("fullText") or "").strip()
            min_legible = max(1, int(Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS))
            source_metadata = (
                native.get("metadata") if isinstance(native.get("metadata"), dict) else {}
            )
            extractor = str(source_metadata.get("extractor") or native.get("engine") or "")
            is_image = cls._is_image(content_type, filename)
            metadata_only_image = is_image and extractor == "image_metadata"
            needs_semantic_vision = purpose in {describe_purpose, hybrid_purpose}

            if (
                len(text) < min_legible
                or metadata_only_image
                or needs_semantic_vision
            ):
                return cls.extract_from_storage_path(
                    attachment.storage_path,
                    filename=filename,
                    content_type=content_type,
                    message=message,
                )

            started = time.perf_counter()
            built = cls._build_from_text(
                text,
                engine=str(native.get("engine") or "native"),
                stages=["native"],
                source_metadata=native.get("metadata") if isinstance(native.get("metadata"), dict) else {},
            )

            result = cls._finalize_result(
                built,
                engine=str(built.get("engine") or "native"),
                stages=["native"],
                warnings=[],
                started=started,
                vision_purpose=cls._resolve_vision_purpose(
                    message,
                    content_type=content_type,
                    filename=filename,
                ),
            )
            result["filename"] = filename
            return cls._maybe_enrich_with_description(
                result,
                storage_path=attachment.storage_path,
                filename=filename,
                content_type=content_type,
                message=message,
            )

        vision = cls.extract_from_storage_path(
            attachment.storage_path,
            filename=filename,
            content_type=content_type,
            message=message,
        )
        vision["filename"] = filename
        return vision

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

            _default_attachment_repository().update_status(
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
        message: str | None = None,
        intent_route: str | None = None,
        has_agent: bool = False,
    ) -> dict[str, Any] | None:
        """Snapshot leve para metadata/adminDebug em turnos só com anexo (ex.: boleto PDF)."""
        attachment = cls._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return None

        vision = cls._compute_vision_for_attachment(
            attachment,
            skills=skills,
            message=message,
            intent_route=intent_route,
            has_agent=has_agent,
        )

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
        message: str | None = None,
    ) -> str:
        if not cls.should_run_for_attachment(skills):
            return extracted_content

        if not cls._is_vision_target(content_type, filename, storage_path):
            return extracted_content

        resolved_type = content_type or cls._default_content_type(filename)
        vision = cls.extract_from_storage_path(
            storage_path,
            filename=filename,
            content_type=resolved_type,
            message=message,
        )
        ocr_text = str(vision.get("fullText") or "").strip()
        image_description = str(vision.get("imageDescription") or "").strip()
        blocks: list[str] = []

        if image_description:
            from app.domain.services.chat_document_vision_content_service import (
                ChatDocumentVisionContentService,
            )

            blocks.append(
                "\n".join(
                    [
                        ChatDocumentVisionContentService.context_label("descriptionLabel"),
                        image_description,
                    ]
                )
            )

        if ocr_text:
            blocks.append(ocr_text)

        if not blocks:
            return extracted_content

        vision_excerpt = "\n\n".join(blocks).strip()

        if cls._should_replace_attachment_content(extracted_content, vision_excerpt):
            return vision_excerpt

        if not extracted_content.strip():
            return vision_excerpt

        return f"{extracted_content.strip()}\n\n{vision_excerpt}".strip()

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
        resolved_purpose = vision_purpose or cls._resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )

        if cls._is_image(content_type, filename):
            result = cls._extract_image_document(
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
            vlm = cls._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
                purpose=resolved_purpose,
            )

            if str(vlm.get("fullText") or "").strip() or str(
                vlm.get("imageDescription") or ""
            ).strip():
                stages.append("ollama_vlm")
                return cls._finalize_result(
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
                    source_metadata={
                        "stampText": str(ocr.get("stampText") or ""),
                        "regions": ocr.get("regions") if isinstance(ocr.get("regions"), dict) else {},
                        "filename": filename,
                    },
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
            repository = _default_attachment_repository()
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
            source_metadata={**metadata, "filename": filename},
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
            regions: dict[str, Any] = {}

            for index in range(page_count):
                page = document.load_page(index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                raw = pytesseract.image_to_string(image, lang=lang)
                chunk = str(raw or "").strip()

                if chunk:
                    texts.append(chunk)

                if index == 0 and Settings.CHAT_DOCUMENT_VISION_STAMP_CROP_ENABLED:
                    from app.domain.services.chat_drawing_region_service import (
                        ChatDrawingRegionService,
                    )

                    cropped = cls._ocr_stamp_regions(page, matrix=matrix, lang=lang)

                    if cropped and cropped not in chunk:
                        texts.append(cropped)
                        stamp_text = cropped
                        stamp_crop_used = True
                        regions["stamp"] = ChatDrawingRegionService.build_region_metadata(
                            region="stamp",
                            bbox=ChatDrawingRegionService.stamp_bbox(),
                            char_count=len(stamp_text),
                        )
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
            "regions": regions,
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
        vision_purpose: str | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        stages: list[str] = []
        warnings: list[str] = []
        merged_text = ""
        resolved_purpose = vision_purpose or ChatDocumentVisionContentService.vision_purpose(
            "ocr"
        )
        describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
        hybrid_purpose = ChatDocumentVisionContentService.vision_purpose("hybrid")

        if resolved_purpose == describe_purpose and cls._image_describe_enabled():
            vlm = cls._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
                purpose=describe_purpose,
            )
            warnings.extend(vlm.get("warnings") or [])
            image_description = str(vlm.get("imageDescription") or "").strip()

            if image_description:
                stages.append("ollama_vlm_describe")
                payload = cls._build_from_text(
                    "",
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                )
                payload["imageDescription"] = image_description
                return cls._finalize_result(
                    payload,
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                    started=started,
                    vision_purpose=describe_purpose,
                )

            warnings.append("ollama_vlm_describe_unavailable")
            backend = "tesseract"

        if backend in {"ollama_vlm", "vlm"}:
            vlm = cls._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
                purpose=resolved_purpose,
            )
            warnings.extend(vlm.get("warnings") or [])

            if str(vlm.get("fullText") or "").strip() or str(
                vlm.get("imageDescription") or ""
            ).strip():
                stages.append("ollama_vlm")
                payload = cls._build_from_text(
                    str(vlm.get("fullText") or ""),
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                )

                if vlm.get("imageDescription"):
                    payload["imageDescription"] = vlm["imageDescription"]

                return cls._finalize_result(
                    payload,
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                    started=started,
                    vision_purpose=resolved_purpose,
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
                vision_purpose=resolved_purpose,
            )

        if resolved_purpose == hybrid_purpose and cls._image_describe_enabled():
            payload = cls._append_image_description(
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
            vision_purpose=resolved_purpose,
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

        stamp_text = str((source_metadata or {}).get("stampText") or "").strip()
        attachment_filename = str((source_metadata or {}).get("filename") or "").strip()

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

        if (
            filename_code
            and parsed.get("productCode")
            and filename_code != parsed["productCode"]
            and ChatDrawingProductCodeResolutionService.ocr_code_likely_filename_drift(
                str(parsed["productCode"]),
                filename_code,
            )
        ):
            parsed["conflicts"] = list(parsed.get("conflicts") or []) + [
                {
                    "type": "stamp_vs_filename",
                    "severity": "pending",
                    "filenameCode": filename_code,
                    "stampCode": parsed["productCode"],
                }
            ]
            parsed["productCode"] = filename_code
            parsed["productCodeSource"] = "filename_crosscheck"

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
    def _finalize_result(
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

    @classmethod
    def _append_image_description(
        cls,
        payload: dict[str, Any],
        *,
        storage_path: str,
        filename: str,
        content_type: str,
        stages: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        if str(payload.get("imageDescription") or "").strip():
            return payload

        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        vlm = cls._stage_ollama_vlm(
            storage_path,
            filename=filename,
            content_type=content_type,
            purpose=ChatDocumentVisionContentService.vision_purpose("describe"),
        )
        warnings.extend(vlm.get("warnings") or [])
        image_description = str(vlm.get("imageDescription") or "").strip()

        if not image_description:
            warnings.append("ollama_vlm_hybrid_describe_empty")
            return payload

        stages.append("ollama_vlm_describe")
        merged = dict(payload)
        merged["imageDescription"] = image_description
        merged["stages"] = stages
        merged["warnings"] = warnings
        return merged

    @classmethod
    def _maybe_enrich_with_description(
        cls,
        payload: dict[str, Any],
        *,
        storage_path: str,
        filename: str,
        content_type: str,
        message: str | None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        purpose = cls._resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )
        hybrid = ChatDocumentVisionContentService.vision_purpose("hybrid")
        describe = ChatDocumentVisionContentService.vision_purpose("describe")

        if purpose not in {hybrid, describe} or not cls._image_describe_enabled():
            return payload

        stages = list(payload.get("stages") or [])
        warnings = list(payload.get("warnings") or [])

        return cls._append_image_description(
            payload,
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            stages=stages,
            warnings=warnings,
        )

    @classmethod
    def _ocr_stamp_regions(cls, page, *, matrix, lang: str) -> str:
        """Recorte do carimbo DELPI — base direita (``drawing_stamp.json`` regionBboxes.stamp)."""
        from app.domain.services.chat_drawing_region_service import (
            ChatDrawingRegionService,
        )

        stamp_bbox = ChatDrawingRegionService.stamp_bbox()
        text = ChatDrawingRegionService.ocr_region_text(
            page,
            bbox=stamp_bbox,
            matrix=matrix,
            lang=lang,
        )

        return text.strip()

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
        purpose: str | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

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
            return {"fullText": "", "imageDescription": "", "warnings": warnings}

        resolved_purpose = purpose or ChatDocumentVisionContentService.vision_purpose("ocr")
        prompt = ChatDocumentVisionContentService.vlm_prompt(
            resolved_purpose,
            is_image=cls._is_image(content_type, filename),
        )

        if not prompt:
            warnings.append("vlm_prompt_missing")
            return {"fullText": "", "imageDescription": "", "warnings": warnings}

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
            return {"fullText": "", "imageDescription": "", "warnings": warnings}

        describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
        hybrid_purpose = ChatDocumentVisionContentService.vision_purpose("hybrid")

        if resolved_purpose == describe_purpose:
            description = cls._truncate_vision_text(content)
            return {
                "fullText": "",
                "imageDescription": description,
                "engine": "ollama_vlm",
                "warnings": warnings,
            }

        if resolved_purpose == hybrid_purpose:
            image_description, full_text = cls._parse_hybrid_vlm_response(content)
            built = cls._build_from_text(
                cls._truncate_vision_text(full_text),
                engine="ollama_vlm",
                stages=["ollama_vlm"],
                warnings=warnings,
            )
            built["imageDescription"] = cls._truncate_vision_text(image_description)
            return built

        text = cls._truncate_vision_text(content)
        return cls._build_from_text(
            text,
            engine="ollama_vlm",
            stages=["ollama_vlm"],
            warnings=warnings,
        )

    @classmethod
    def _parse_hybrid_vlm_response(cls, content: str) -> tuple[str, str]:
        import re

        normalized = str(content or "").strip()
        description = ""
        text = normalized

        description_match = re.search(
            r"(?:DESCRIÇÃO|DESCRICAO)\s*:\s*(.*?)(?=(?:TEXTO)\s*:|$)",
            normalized,
            flags=re.IGNORECASE | re.DOTALL,
        )
        text_match = re.search(
            r"(?:TEXTO)\s*:\s*(.*)$",
            normalized,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if description_match:
            description = str(description_match.group(1) or "").strip()

        if text_match:
            text = str(text_match.group(1) or "").strip()
        elif description_match:
            text = ""

        return description, text

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
