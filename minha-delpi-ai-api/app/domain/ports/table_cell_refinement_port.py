"""Port genérico — re-OCR de célula tabular (chat base, sem semântica de desenho)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypedDict


class TableCellRefinementResult(TypedDict, total=False):
    text: str
    bbox: list[float]
    engines: list[str]
    engine: str


class TableCellRefinementPort(ABC):
    @abstractmethod
    def refine_cell(
        self,
        *,
        storage_path: str,
        table_id: str,
        row_index: int,
        col_index: int,
        fallback_text: str = "",
    ) -> TableCellRefinementResult:
        raise NotImplementedError
