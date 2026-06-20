"""Re-OCR de célula tabular — implementação chat base do TableCellRefinementPort."""

from __future__ import annotations

from typing import Any

from app.domain.ports.table_cell_refinement_port import (
    TableCellRefinementPort,
    TableCellRefinementResult,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
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
        text = str(fallback_text or "").strip()
        table = cls._find_table(storage_path, table_id)

        if table is not None:
            cached = ChatPdfTableStructureService.cell_text(
                table,
                row_index=row_index,
                col_index=col_index,
            )

            if cached:
                text = cached

        if not text:
            return TableCellRefinementResult(text="", engines=[], engine="")

        return TableCellRefinementResult(
            text=text,
            engines=["structured_table"],
            engine="structured_table",
        )

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
