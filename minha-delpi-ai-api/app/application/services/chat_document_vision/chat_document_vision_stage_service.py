"""Estágios OCR/VLM — visão de documentos."""

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
from app.application.services.chat_document_vision.document_vision_runtime import vision_runtime
from app.application.services.chat_document_vision.chat_document_vision_facade_access import vision_service


class ChatDocumentVisionStageService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def maybe_vlm_fallback(
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
        if not vision_service()._auto_vlm_fallback_enabled():
            return payload

        if not vision_service()._needs_vlm_fallback(
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
            if ChatDocumentVisionConfigService.is_image(content_type, filename) and ChatDocumentVisionConfigService.image_describe_enabled()
            else ChatDocumentVisionContentService.vision_purpose("ocr")
        )
        if vision_purpose:
            fallback_purpose = vision_purpose

        vlm = vision_service()._stage_ollama_vlm(
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
        return vision_service()._build_from_text(
            vlm_text,
            engine="ollama_vlm",
            stages=stages,
            page_count=payload.get("pageCount"),
            warnings=warnings,
            source_metadata={"vlmFallback": True},
        )

    @classmethod
    def stage_native(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
    ) -> dict[str, Any]:
        from app.domain.services.chat_pdf_document_extraction_service import (
            ChatPdfDocumentExtractionService,
        )

        extracted = ChatPdfDocumentExtractionService.extract_from_storage_path(
            storage_path,
            filename=filename or Path(storage_path).name,
            layout_profile=ChatPdfDocumentExtractionService.LAYOUT_GENERIC,
            enable_region_ocr=False,
        )

        if not extracted.get("supported"):
            return vision_service()._build_from_text(
                "",
                engine="native",
                stages=["native"],
                warnings=list(extracted.get("warnings") or [])
                or [str(extracted.get("reason") or "unsupported")],
            )

        metadata = extracted.get("parseMetadata")

        if not isinstance(metadata, dict):
            metadata = {}

        return vision_service()._build_from_text(
            str(extracted.get("fullText") or "").strip(),
            engine=str(extracted.get("engine") or metadata.get("extractor") or "native"),
            stages=list(extracted.get("stages") or ["native"]),
            source_metadata={**metadata, "filename": filename},
        )

    @classmethod
    def stage_tesseract_pdf(cls, storage_path: str) -> dict[str, Any]:
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
        max_pages = max(1, int(vision_runtime().get("documentVisionMaxPages", 10)))
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
            region_texts: dict[str, str] = {}
            detail_ocr_applied = False

            for index in range(page_count):
                page = document.load_page(index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                raw = pytesseract.image_to_string(image, lang=lang)
                chunk = str(raw or "").strip()

                if chunk:
                    texts.append(chunk)

                if index == 0 and vision_runtime().get("documentVisionStampCropEnabled"):
                    from app.domain.services.chat_drawing_region_service import (
                        ChatDrawingRegionService,
                    )

                    region_texts, regions = ChatDrawingRegionService.ocr_drawing_regions(
                        page,
                        matrix=matrix,
                        lang=lang,
                    )
                    cropped = str(region_texts.get("stamp") or "").strip()

                    if cropped and cropped not in chunk:
                        texts.append(cropped)
                        stamp_text = cropped
                        stamp_crop_used = True
                    elif cropped:
                        stamp_text = cropped
                        stamp_crop_used = True

                    bom_text = str(region_texts.get("bom") or "").strip()

                    if bom_text and bom_text not in chunk:
                        texts.append(bom_text)

                    detail_ocr_applied = any(
                        isinstance(meta, dict) and meta.get("detailPass")
                        for meta in regions.values()
                    )
        finally:
            document.close()

        if stamp_crop_used:
            warnings.append("stamp_crop_applied")

        if detail_ocr_applied:
            warnings.append("region_detail_ocr_applied")

        return {
            "fullText": "\n\n".join(texts).strip(),
            "engine": "tesseract",
            "pageCount": page_count if "page_count" in locals() else 0,
            "warnings": warnings,
            "stampCrop": stamp_crop_used,
            "stampText": stamp_text if stamp_crop_used else "",
            "detailOcrApplied": detail_ocr_applied,
            "regionTexts": region_texts,
            "bomText": region_texts.get("bom", ""),
            "dimensionsText": region_texts.get("dimensions", ""),
            "titleText": region_texts.get("title", ""),
            "regions": regions,
        }

    @classmethod
    def extract_image_document(
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

        if resolved_purpose == describe_purpose and ChatDocumentVisionConfigService.image_describe_enabled():
            vlm = vision_service()._stage_ollama_vlm(
                storage_path,
                filename=filename,
                content_type=content_type,
                purpose=describe_purpose,
            )
            warnings.extend(vlm.get("warnings") or [])
            image_description = str(vlm.get("imageDescription") or "").strip()

            if image_description:
                stages.append("ollama_vlm_describe")
                payload = vision_service()._build_from_text(
                    "",
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                )
                payload["imageDescription"] = image_description
                return vision_service()._finalize_result(
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
            vlm = vision_service()._stage_ollama_vlm(
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
                payload = vision_service()._build_from_text(
                    str(vlm.get("fullText") or ""),
                    engine="ollama_vlm",
                    stages=stages,
                    warnings=warnings,
                )

                if vlm.get("imageDescription"):
                    payload["imageDescription"] = vlm["imageDescription"]

                return vision_service()._finalize_result(
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
            neural = vision_service()._stage_neural_backend(
                storage_path,
                filename=filename,
                content_type=content_type,
                backend=backend,
            )
            warnings.extend(neural.get("warnings") or [])

            if str(neural.get("fullText") or "").strip():
                stages.append(backend)
                return vision_service()._finalize_result(
                    neural,
                    engine=backend,
                    stages=stages,
                    warnings=warnings,
                    started=started,
                )

            warnings.append(f"{backend}_unavailable_fallback_tesseract")
            backend = "tesseract"

        if backend in {"native", "text"}:
            native = vision_service()._stage_native(
                storage_path,
                filename=filename,
                content_type=content_type,
            )
            stages.append("native")
            merged_text = str(native.get("fullText") or "").strip()
            warnings.extend(native.get("warnings") or [])

        if backend in {"tesseract", "auto", "paddleocr", "docling"}:
            ocr = vision_service()._stage_tesseract_image(storage_path)
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

        payload = vision_service()._build_from_text(
            merged_text,
            engine="tesseract" if "tesseract_image" in stages else "native",
            stages=stages or ["native"],
            warnings=warnings,
        )

        if backend == "auto":
            payload = cls.maybe_vlm_fallback(
                payload,
                storage_path=storage_path,
                filename=filename,
                content_type=content_type,
                stages=stages,
                warnings=warnings,
                vision_purpose=resolved_purpose,
            )

        if resolved_purpose == hybrid_purpose and ChatDocumentVisionConfigService.image_describe_enabled():
            payload = cls.append_image_description(
                payload,
                storage_path=storage_path,
                filename=filename,
                content_type=content_type,
                stages=stages,
                warnings=warnings,
            )

        return vision_service()._finalize_result(
            payload,
            engine=str(payload.get("engine") or "tesseract"),
            stages=stages or ["tesseract_image"],
            warnings=warnings,
            started=started,
            vision_purpose=resolved_purpose,
        )

    @classmethod
    def stage_tesseract_image(cls, storage_path: str) -> dict[str, Any]:
        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        max_chars = max(1, int(vision_runtime().get("documentVisionMaxChars", 12000)))

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
    def append_image_description(
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

        vlm = vision_service()._stage_ollama_vlm(
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
    def maybe_enrich_with_description(
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

        purpose = vision_service()._resolve_vision_purpose(
            message,
            content_type=content_type,
            filename=filename,
        )
        hybrid = ChatDocumentVisionContentService.vision_purpose("hybrid")
        describe = ChatDocumentVisionContentService.vision_purpose("describe")

        if purpose not in {hybrid, describe} or not ChatDocumentVisionConfigService.image_describe_enabled():
            return payload

        stages = list(payload.get("stages") or [])
        warnings = list(payload.get("warnings") or [])

        return cls.append_image_description(
            payload,
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            stages=stages,
            warnings=warnings,
        )

    @classmethod
    def ocr_stamp_regions(cls, page, *, matrix, lang: str) -> str:
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
    def vision_timeout_seconds(cls) -> float:
        return max(5.0, float(Settings.CHAT_DOCUMENT_VISION_TIMEOUT_SECONDS))

    @classmethod
    def truncate_vision_text(cls, text: str) -> str:
        max_chars = max(1, int(vision_runtime().get("documentVisionMaxChars", 12000)))
        normalized = str(text or "").strip()

        if len(normalized) <= max_chars:
            return normalized

        return f"{normalized[: max_chars - 1]}…"

    @classmethod
    def rasterize_pdf_pages(cls, storage_path: str) -> tuple[list[Any], list[str]]:
        warnings: list[str] = []

        try:
            import fitz
            from PIL import Image
        except ImportError as exc:
            return [], [f"dependencies_unavailable:{exc.__class__.__name__}"]

        dpi = max(72, int(Settings.CHAT_DOCUMENT_VISION_DPI))
        max_pages = max(1, int(vision_runtime().get("documentVisionMaxPages", 10)))
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
    def pil_to_base64_png(cls, image: Any) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @classmethod
    def stage_ollama_vlm(
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
        max_vlm_pages = max(
            1,
            min(3, int(vision_runtime().get("documentVisionMaxPages", 10))),
        )

        images_b64: list[str] = []

        if ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path):
            pages, page_warnings = cls.rasterize_pdf_pages(storage_path)
            warnings.extend(page_warnings)
            images_b64 = [vision_service()._pil_to_base64_png(page) for page in pages[:max_vlm_pages]]
        elif ChatDocumentVisionConfigService.is_image(content_type, filename):
            try:
                from PIL import Image

                with Image.open(storage_path) as image:
                    images_b64 = [vision_service()._pil_to_base64_png(image.convert("RGB"))]
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
            is_image=ChatDocumentVisionConfigService.is_image(content_type, filename),
        )

        if not prompt:
            warnings.append("vlm_prompt_missing")
            return {"fullText": "", "imageDescription": "", "warnings": warnings}

        max_predict = min(
            4096,
            int(vision_runtime().get("documentVisionMaxChars", 12000)),
        )

        try:
            from app.composition.vision_llm_composer import make_vision_llm_gateway

            gateway = make_vision_llm_gateway()
            content = gateway.describe(
                prompt=prompt,
                images_b64=images_b64,
                max_tokens=max_predict,
            )
            engine = f"{gateway.provider_name()}_vlm"
        except Exception as exc:
            warnings.append(f"vlm_request_failed:{exc.__class__.__name__}")
            return {"fullText": "", "warnings": warnings}

        if not content:
            warnings.append("vlm_empty_response")
            return {"fullText": "", "imageDescription": "", "warnings": warnings}

        describe_purpose = ChatDocumentVisionContentService.vision_purpose("describe")
        hybrid_purpose = ChatDocumentVisionContentService.vision_purpose("hybrid")

        if resolved_purpose == describe_purpose:
            description = cls.truncate_vision_text(content)
            return {
                "fullText": "",
                "imageDescription": description,
                "engine": engine,
                "warnings": warnings,
            }

        if resolved_purpose == hybrid_purpose:
            image_description, full_text = cls.parse_hybrid_vlm_response(content)
            built = vision_service()._build_from_text(
                cls.truncate_vision_text(full_text),
                engine=engine,
                stages=[engine],
                warnings=warnings,
            )
            built["imageDescription"] = cls.truncate_vision_text(image_description)
            return built

        text = cls.truncate_vision_text(content)
        return vision_service()._build_from_text(
            text,
            engine=engine,
            stages=[engine],
            warnings=warnings,
        )

    @classmethod
    def parse_hybrid_vlm_response(cls, content: str) -> tuple[str, str]:
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
    def stage_neural_backend(
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
                return vision_service()._stage_docling(storage_path, filename=filename, warnings=warnings)

            if backend == "paddleocr":
                return vision_service()._stage_paddleocr(storage_path, filename=filename, warnings=warnings)
        except Exception as exc:
            warnings.append(f"{backend}_error:{exc.__class__.__name__}")

        return {"fullText": "", "warnings": warnings}

    @classmethod
    def stage_docling(cls, storage_path: str, *, filename: str, warnings: list[str]) -> dict[str, Any]:
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

        text = cls.truncate_vision_text(text)

        if not text:
            warnings.append("docling_empty_text")
            return {"fullText": "", "warnings": warnings}

        return vision_service()._build_from_text(
            text,
            engine="docling",
            stages=["docling"],
            warnings=warnings,
        )

    @classmethod
    def stage_paddleocr(
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
        content_type = ChatDocumentVisionConfigService.default_content_type(filename)

        if ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path):
            pages, page_warnings = cls.rasterize_pdf_pages(storage_path)
            warnings.extend(page_warnings)

            for page in pages:
                segment = cls.paddleocr_from_image(engine, page)

                if segment:
                    parts.append(segment)
        else:
            segment = cls.paddleocr_from_path(engine, storage_path)

            if segment:
                parts.append(segment)

        text = cls.truncate_vision_text("\n\n".join(parts).strip())

        if not text:
            warnings.append("paddleocr_empty_text")
            return {"fullText": "", "warnings": warnings}

        return vision_service()._build_from_text(
            text,
            engine="paddleocr",
            stages=["paddleocr"],
            warnings=warnings,
        )

    @classmethod
    def paddleocr_from_path(cls, engine: Any, storage_path: str) -> str:
        try:
            from PIL import Image
        except ImportError:
            return ""

        try:
            with Image.open(storage_path) as image:
                return cls.paddleocr_from_image(engine, image.convert("RGB"))
        except Exception:
            return ""

    @classmethod
    def paddleocr_from_image(cls, engine: Any, image: Any) -> str:
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
