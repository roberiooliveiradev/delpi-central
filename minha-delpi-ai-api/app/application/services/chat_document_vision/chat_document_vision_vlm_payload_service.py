"""Montagem do payload multimodal VLM (full-page vs crops regionais DELPI)."""

from __future__ import annotations

from typing import Any

from app.application.services.chat_document_vision.chat_document_vision_config_service import (
    ChatDocumentVisionConfigService,
)
from app.application.services.chat_document_vision.chat_document_vision_facade_access import (
    vision_service,
)
from app.infrastructure.config.settings import Settings


class ChatDocumentVisionVlmPayloadService:
    """Constrói images_b64 + prompt para o gateway VLM."""

    @classmethod
    def build(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
        use_drawing_regions: bool = False,
        partial_ocr_texts: dict[str, str] | None = None,
        purpose: str | None = None,
        is_image: bool = False,
    ) -> dict[str, Any]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        warnings: list[str] = []
        ocr_purpose = ChatDocumentVisionContentService.vision_purpose("ocr")
        resolved_purpose = purpose or ocr_purpose

        if (
            use_drawing_regions
            and resolved_purpose == ocr_purpose
            and ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path)
        ):
            images_b64, region_labels, crop_warnings = cls._build_drawing_region_images(
                storage_path
            )
            warnings.extend(crop_warnings)

            if images_b64:
                partial = cls._compose_partial_ocr_hint(partial_ocr_texts)
                prompt = ChatDocumentVisionContentService.vlm_drawing_ocr_prompt(
                    partial_ocr=partial or None,
                )
                return {
                    "imagesB64": images_b64,
                    "regionLabels": region_labels,
                    "vlmRegionsSent": list(region_labels),
                    "vlmImageCount": len(images_b64),
                    "prompt": prompt,
                    "promptContext": {
                        "mode": "drawing_regions",
                        "partialOcrChars": len(partial),
                    },
                    "warnings": warnings,
                }

            warnings.append("vlm_drawing_crops_empty_fallback_full_page")

        images_b64, full_warnings = cls._build_full_page_images(
            storage_path,
            filename=filename,
            content_type=content_type,
        )
        warnings.extend(full_warnings)
        prompt = ChatDocumentVisionContentService.vlm_prompt(
            resolved_purpose,
            is_image=is_image
            or ChatDocumentVisionConfigService.is_image(content_type, filename),
        )

        return {
            "imagesB64": images_b64,
            "regionLabels": ["page"] * len(images_b64),
            "vlmRegionsSent": ["page"] * len(images_b64) if images_b64 else [],
            "vlmImageCount": len(images_b64),
            "prompt": prompt,
            "promptContext": {"mode": "full_page"},
            "warnings": warnings,
        }

    @classmethod
    def _compose_partial_ocr_hint(
        cls,
        partial_ocr_texts: dict[str, str] | None,
    ) -> str:
        if not isinstance(partial_ocr_texts, dict):
            return ""

        chunks: list[str] = []

        for key in ("stamp", "bom", "title", "dimensions"):
            value = str(partial_ocr_texts.get(key) or "").strip()

            if value:
                chunks.append(f"{key.upper()}:\n{value}")

        return "\n\n".join(chunks).strip()

    @classmethod
    def _base_matrix(cls) -> Any:
        import fitz

        dpi = max(72, int(Settings.CHAT_DOCUMENT_VISION_DPI))
        zoom = dpi / 72.0
        return fitz.Matrix(zoom, zoom)

    @classmethod
    def _build_full_page_images(
        cls,
        storage_path: str,
        *,
        filename: str,
        content_type: str,
    ) -> tuple[list[str], list[str]]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )

        warnings: list[str] = []
        max_images = ChatDocumentVisionContentService.vlm_max_images()
        images_b64: list[str] = []

        if ChatDocumentVisionConfigService.is_pdf(content_type, filename, storage_path):
            pages, page_warnings = vision_service()._rasterize_pdf_pages(storage_path)
            warnings.extend(page_warnings)
            images_b64 = [
                vision_service()._pil_to_base64_png(page)
                for page in pages[:max_images]
            ]
        elif ChatDocumentVisionConfigService.is_image(content_type, filename):
            try:
                from PIL import Image

                with Image.open(storage_path) as image:
                    images_b64 = [
                        vision_service()._pil_to_base64_png(image.convert("RGB"))
                    ]
            except Exception as exc:
                warnings.append(f"vlm_image_open_failed:{exc.__class__.__name__}")
        else:
            warnings.append("vlm_unsupported_content_type")

        return images_b64, warnings

    @classmethod
    def _build_drawing_region_images(
        cls,
        storage_path: str,
    ) -> tuple[list[str], list[str], list[str]]:
        from app.domain.services.chat_document_vision_content_service import (
            ChatDocumentVisionContentService,
        )
        from app.domain.services.chat_drawing_region_service import (
            ChatDrawingRegionService,
        )

        warnings: list[str] = []
        images_b64: list[str] = []
        region_labels: list[str] = []
        max_images = ChatDocumentVisionContentService.vlm_max_images()
        region_keys = ChatDocumentVisionContentService.vlm_drawing_regions()

        try:
            import fitz
        except ImportError as exc:
            return [], [], [f"dependencies_unavailable:{exc.__class__.__name__}"]

        try:
            document = fitz.open(storage_path)
        except Exception as exc:
            return [], [], [f"pdf_open_failed:{exc.__class__.__name__}"]

        try:
            if int(document.page_count or 0) < 1:
                warnings.append("vlm_drawing_no_pages")
                return [], [], warnings

            page = document.load_page(0)
            base_matrix = cls._base_matrix()
            detail_matrix = ChatDrawingRegionService._scale_matrix(
                base_matrix,
                ChatDrawingRegionService.detail_zoom_multiplier(),
            )
            region_bboxes, _layout_meta = ChatDrawingRegionService.resolve_region_bboxes_for_page(
                page,
                matrix=base_matrix,
            )

            for region in region_keys:
                if len(images_b64) >= max_images:
                    break

                bbox = region_bboxes.get(region)

                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue

                image = ChatDrawingRegionService.render_region_image(
                    page,
                    bbox=bbox,
                    matrix=detail_matrix,
                )

                if image is None:
                    warnings.append(f"vlm_region_render_failed:{region}")
                    continue

                images_b64.append(vision_service()._pil_to_base64_png(image))
                region_labels.append(region)

            if (
                ChatDocumentVisionContentService.vlm_include_overview()
                and len(images_b64) < max_images
            ):
                try:
                    from PIL import Image

                    pixmap = page.get_pixmap(matrix=base_matrix, alpha=False)
                    overview = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples,
                    )
                    images_b64.append(vision_service()._pil_to_base64_png(overview))
                    region_labels.append("overview")
                except Exception as exc:
                    warnings.append(f"vlm_overview_render_failed:{exc.__class__.__name__}")
        finally:
            document.close()

        return images_b64, region_labels, warnings
