"""Re-OCR de célula tabular — implementação chat base do TableCellRefinementPort."""

from __future__ import annotations

import re
from typing import Any

from app.domain.ports.table_cell_refinement_port import (
    TableCellRefinementPort,
    TableCellRefinementResult,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_pdf_table_structure_service import (
    ChatPdfTableStructureService,
)


class ChatPdfTableCellRefinementService(TableCellRefinementPort):
    _tables_cache: dict[str, list[dict[str, Any]]] = {}

    @classmethod
    def register_tables(cls, storage_path: str, tables: list[dict[str, Any]]) -> None:
        key = str(storage_path or "").strip()

        if key:
            cls._tables_cache[key] = list(tables)

    @classmethod
    def clear_cache(cls) -> None:
        cls._tables_cache.clear()

    def refine_cell(
        self,
        *,
        storage_path: str,
        table_id: str,
        row_index: int,
        col_index: int,
        fallback_text: str = "",
    ) -> TableCellRefinementResult:
        table = ChatPdfTableCellRefinementService._find_table(storage_path, table_id)
        cell_bbox = (
            ChatPdfTableStructureService.cell_bbox(
                table,
                row_index=row_index,
                col_index=col_index,
            )
            if table is not None
            else None
        )
        cached = ""

        if table is not None:
            cached = ChatPdfTableStructureService.cell_text(
                table,
                row_index=row_index,
                col_index=col_index,
            )

        ocr_result: dict[str, Any] = {}
        path = str(storage_path or "").strip()

        if path and cell_bbox:
            ocr_result = ChatPdfTableCellRefinementService._ocr_cell_bbox(
                path,
                bbox=cell_bbox,
                page_index=ChatPdfTableStructureService.page_index(table or {}),
            )

        text = str(ocr_result.get("text") or cached or fallback_text or "").strip()
        engines = list(ocr_result.get("engines") or [])

        if not text:
            return TableCellRefinementResult(text="", engines=[], engine="", bbox=cell_bbox)

        if not engines and cached:
            engines = ["structured_table"]

        return TableCellRefinementResult(
            text=text,
            bbox=cell_bbox,
            engines=engines,
            engine=str(
                ocr_result.get("engine")
                or (engines[0] if engines else ("structured_table" if cached else ""))
            ),
        )

    @classmethod
    def _ocr_cell_bbox(
        cls,
        storage_path: str,
        *,
        bbox: list[float],
        page_index: int,
    ) -> dict[str, Any]:
        try:
            import fitz
        except ImportError:
            return {"text": "", "engines": [], "engine": ""}

        padded = cls._apply_padding(bbox, ChatDocumentVisionContentService.table_structure_cell_padding())
        dpi_multiplier = max(
            ChatDocumentVisionContentService.table_structure_cell_dpi_multiplier(),
            float(ChatDrawingPatternsService.bom_row_refinement_rule("dpiMultiplier", 2.0) or 2.0),
        )

        from app.infrastructure.config.settings import Settings
        import os

        base_dpi = max(72, int(Settings.CHAT_DOCUMENT_VISION_DPI))
        zoom = (base_dpi / 72.0) * dpi_multiplier
        matrix = fitz.Matrix(zoom, zoom)
        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        tesseract_config = ChatDocumentVisionContentService.table_structure_cell_tesseract_config()

        try:
            document = fitz.open(storage_path)
        except Exception:
            return {"text": "", "engines": [], "engine": ""}

        try:
            if document.page_count <= 0:
                return {"text": "", "engines": [], "engine": ""}

            page = document[min(max(0, page_index), document.page_count - 1)]
        except Exception:
            document.close()
            return {"text": "", "engines": [], "engine": ""}

        try:
            from app.domain.services.chat_drawing_region_service import (
                ChatDrawingRegionService,
            )
            from app.domain.services.chat_pdf_region_ocr_engine_service import (
                ChatPdfRegionOcrEngineService,
            )

            image = ChatDrawingRegionService._render_region_image(
                page,
                bbox=padded,
                matrix=matrix,
            )

            if image is None:
                return {"text": "", "engines": [], "engine": ""}

            processed = ChatDrawingRegionService._preprocess_region_image(image)
            result = ChatPdfRegionOcrEngineService.recognize(
                processed,
                lang=lang,
                tesseract_config=tesseract_config,
                region=None,
            )
            text = cls._normalize_quantity_ocr(str(result.get("text") or ""))

            return {
                "text": text,
                "engines": list(result.get("engines") or []),
                "engine": str(result.get("engine") or ""),
            }
        except Exception:
            return {"text": "", "engines": [], "engine": ""}
        finally:
            document.close()

    @classmethod
    def _apply_padding(cls, bbox: list[float], padding: float) -> list[float]:
        x0, y0, x1, y1 = (float(value) for value in bbox)
        pad = max(0.0, float(padding))

        return [
            min(1.0, max(0.0, x0 + pad)),
            min(1.0, max(0.0, y0 + pad)),
            min(1.0, max(0.0, x1 - pad)),
            min(1.0, max(0.0, y1 - pad)),
        ]

    @classmethod
    def _normalize_quantity_ocr(cls, raw: str) -> str:
        text = str(raw or "").strip()

        if not text:
            return ""

        compact = re.sub(r"\s+", "", text)
        match = re.search(r"\d+(?:[.,]\d+)?", compact)

        if not match:
            return text

        token = match.group(0).replace(",", ".")

        if re.fullmatch(r"\d+(?:\.\d+)?", token):
            return token

        return text

    @classmethod
    def _find_table(cls, storage_path: str, table_id: str) -> dict[str, Any] | None:
        key = str(storage_path or "").strip()
        target = str(table_id or "").strip()
        tables = cls._tables_cache.get(key) or []

        for table in tables:
            if str(table.get("tableId") or "") == target:
                return table

        return None

    @classmethod
    def max_attempts(cls) -> int:
        return ChatDocumentVisionContentService.table_structure_cell_max_attempts()
