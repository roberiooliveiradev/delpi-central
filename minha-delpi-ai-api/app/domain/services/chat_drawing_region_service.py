"""Regiões gráficas normalizadas para OCR hierárquico de desenhos (Onda 14)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_DEFAULT_BBOXES: dict[str, list[float]] = {
    "stamp": [0.5, 0.62, 1.0, 1.0],
    "title": [0.2, 0.0, 0.8, 0.12],
    "bom": [0.0, 0.0, 0.55, 0.35],
    "dimensions": [0.0, 0.12, 1.0, 0.62],
}

_DRAWING_REGION_ORDER = ("stamp", "title", "bom", "dimensions")


class ChatDrawingRegionService:
    @classmethod
    def region_bboxes(cls) -> dict[str, list[float]]:
        node = ChatAssistantContentService.get_node("drawing_stamp", "regionBboxes")

        if not isinstance(node, dict):
            return dict(_DEFAULT_BBOXES)

        resolved: dict[str, list[float]] = {}

        for key, value in node.items():
            if isinstance(value, list) and len(value) == 4:
                resolved[str(key)] = [float(item) for item in value]

        return resolved or dict(_DEFAULT_BBOXES)

    @classmethod
    def stamp_bbox(cls) -> list[float]:
        return list(cls.region_bboxes().get("stamp") or _DEFAULT_BBOXES["stamp"])

    @classmethod
    def fitz_rect(cls, page: Any, bbox: list[float] | tuple[float, ...]) -> Any:
        import fitz

        width = float(page.rect.width)
        height = float(page.rect.height)
        x0, y0, x1, y1 = (float(value) for value in bbox)

        return fitz.Rect(
            width * x0,
            height * y0,
            width * x1,
            height * y1,
        )

    @classmethod
    def ocr_region_text(
        cls,
        page: Any,
        *,
        bbox: list[float] | tuple[float, ...],
        matrix: Any,
        lang: str,
    ) -> str:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return ""

        try:
            rect = cls.fitz_rect(page, bbox)
            pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            return str(pytesseract.image_to_string(image, lang=lang) or "").strip()
        except Exception:
            return ""

    @classmethod
    def build_region_metadata(
        cls,
        *,
        region: str,
        bbox: list[float],
        char_count: int,
        engine: str = "tesseract",
    ) -> dict[str, Any]:
        return {
            "bbox": list(bbox),
            "charCount": int(char_count),
            "engine": engine,
        }

    @classmethod
    def stamp_position_is_bottom_right(cls) -> bool:
        bbox = cls.stamp_bbox()

        return len(bbox) == 4 and bbox[0] >= 0.45 and bbox[1] >= 0.5

    @classmethod
    def ocr_drawing_regions(
        cls,
        page: Any,
        *,
        matrix: Any,
        lang: str,
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
        texts: dict[str, str] = {}
        metadata: dict[str, dict[str, Any]] = {}

        for region in _DRAWING_REGION_ORDER:
            bbox = cls.region_bboxes().get(region)

            if not bbox:
                continue

            text = cls.ocr_region_text(page, bbox=bbox, matrix=matrix, lang=lang).strip()

            if not text:
                continue

            texts[region] = text
            metadata[region] = cls.build_region_metadata(
                region=region,
                bbox=bbox,
                char_count=len(text),
            )

        return texts, metadata
