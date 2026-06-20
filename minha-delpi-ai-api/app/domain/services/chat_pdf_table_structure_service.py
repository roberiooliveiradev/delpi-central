"""Estrutura tabular genérica a partir de texto OCR — chat base (sem semântica BOM)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatPdfTableStructureService:
    _ANCHOR_PATTERN: re.Pattern[str] | None = None

    @classmethod
    def extract_from_metadata(cls, metadata: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not cls.enabled():
            return []

        meta = metadata if isinstance(metadata, dict) else {}
        tables: list[dict[str, Any]] = []
        region_texts = meta.get("regionTexts")
        regions_meta = meta.get("regions") if isinstance(meta.get("regions"), dict) else {}

        if isinstance(region_texts, dict):
            for region_name, region_text in region_texts.items():
                text = str(region_text or "").strip()

                if not text:
                    continue

                region_info = regions_meta.get(region_name)
                source_bbox = None
                page_index = 0

                if isinstance(region_info, dict):
                    bbox = region_info.get("bbox")

                    if isinstance(bbox, list) and len(bbox) == 4:
                        source_bbox = [float(value) for value in bbox]

                parsed = cls.extract_from_region_text(
                    text,
                    table_id=f"region_{region_name}_p{page_index}",
                    source_region=str(region_name),
                    source_bbox=source_bbox,
                    page_index=page_index,
                )

                if parsed:
                    tables.append(parsed)

        existing = meta.get("structuredTables")

        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict) and item.get("tableId"):
                    tables.append(dict(item))

        return cls._dedupe_tables(tables)

    @classmethod
    def extract_from_region_text(
        cls,
        text: str,
        *,
        table_id: str,
        source_region: str,
        source_bbox: list[float] | None = None,
        page_index: int = 0,
    ) -> dict[str, Any] | None:
        normalized = str(text or "").strip()

        if not normalized:
            return None

        rows = cls._parse_rows(normalized)

        if len(rows) < 2:
            return None

        header = rows[0]
        body = rows[1 : cls.max_rows() + 1]
        columns = [
            {
                "index": index,
                "headerText": str(cell or "").strip(),
            }
            for index, cell in enumerate(header)
        ]
        structured_rows: list[dict[str, Any]] = []

        for row_index, cells in enumerate(body):
            structured_rows.append(
                {
                    "index": row_index,
                    "cells": [
                        {
                            "col": col_index,
                            "text": str(value or "").strip(),
                        }
                        for col_index, value in enumerate(cells)
                    ],
                }
            )

        table: dict[str, Any] = {
            "tableId": table_id,
            "sourceRegion": source_region,
            "pageIndex": int(page_index),
            "format": "structured",
            "columns": columns,
            "rows": structured_rows,
            "rowCount": len(structured_rows),
        }

        if isinstance(source_bbox, list) and len(source_bbox) == 4:
            table = cls.apply_cell_bboxes(table, source_bbox=source_bbox)

        return table

    @classmethod
    def apply_cell_bboxes(
        cls,
        table: dict[str, Any],
        *,
        source_bbox: list[float],
    ) -> dict[str, Any]:
        if len(source_bbox) != 4:
            return table

        columns = table.get("columns")

        if not isinstance(columns, list) or not columns:
            return table

        rows = table.get("rows")

        if not isinstance(rows, list):
            return table

        x0, y0, x1, y1 = (float(value) for value in source_bbox)
        col_count = len(columns)
        row_count = len(rows) + 1

        if col_count < 1 or row_count < 2:
            return table

        width = max(0.0, x1 - x0)
        height = max(0.0, y1 - y0)
        col_width = width / col_count
        row_height = height / row_count

        for column in columns:
            if not isinstance(column, dict):
                continue

            try:
                col_index = int(column.get("index"))
            except (TypeError, ValueError):
                continue

            column["bbox"] = [
                x0 + col_index * col_width,
                y0 + row_height,
                x0 + (col_index + 1) * col_width,
                y1,
            ]

        for row in rows:
            if not isinstance(row, dict):
                continue

            try:
                body_index = int(row.get("index"))
            except (TypeError, ValueError):
                continue

            for cell in row.get("cells") or []:
                if not isinstance(cell, dict):
                    continue

                try:
                    cell_col = int(cell.get("col"))
                except (TypeError, ValueError):
                    continue

                cell["bbox"] = [
                    x0 + cell_col * col_width,
                    y0 + (body_index + 1) * row_height,
                    x0 + (cell_col + 1) * col_width,
                    y0 + (body_index + 2) * row_height,
                ]

        table["tableBbox"] = [x0, y0, x1, y1]
        return table

    @classmethod
    def cell_bbox(
        cls,
        table: dict[str, Any],
        *,
        row_index: int,
        col_index: int,
    ) -> list[float] | None:
        rows = table.get("rows")

        if not isinstance(rows, list):
            return None

        for row in rows:
            if not isinstance(row, dict):
                continue

            try:
                current_index = int(row.get("index"))
            except (TypeError, ValueError):
                continue

            if current_index != int(row_index):
                continue

            for cell in row.get("cells") or []:
                if not isinstance(cell, dict):
                    continue

                try:
                    cell_col = int(cell.get("col"))
                except (TypeError, ValueError):
                    continue

                if cell_col != int(col_index):
                    continue

                bbox = cell.get("bbox")

                if isinstance(bbox, list) and len(bbox) == 4:
                    return [float(value) for value in bbox]

        return None

    @classmethod
    def cell_text(
        cls,
        table: dict[str, Any],
        *,
        row_index: int,
        col_index: int,
    ) -> str:
        rows = table.get("rows")

        if not isinstance(rows, list):
            return ""

        for row in rows:
            if not isinstance(row, dict):
                continue

            raw_index = row.get("index")

            try:
                current_index = int(raw_index)
            except (TypeError, ValueError):
                continue

            if current_index != int(row_index):
                continue

            for cell in row.get("cells") or []:
                if not isinstance(cell, dict):
                    continue

                try:
                    cell_col = int(cell.get("col"))
                except (TypeError, ValueError):
                    continue

                if cell_col == int(col_index):
                    return str(cell.get("text") or "").strip()

        return ""

    @classmethod
    def page_index(cls, table: dict[str, Any]) -> int:
        raw = table.get("pageIndex")

        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            pass

        table_id = str(table.get("tableId") or "")
        match = re.search(r"_p(\d+)$", table_id)

        if match:
            try:
                return max(0, int(match.group(1)))
            except ValueError:
                return 0

        return 0

    @classmethod
    def enabled(cls) -> bool:
        return bool(ChatDocumentVisionContentService.table_structure_enabled())

    @classmethod
    def max_rows(cls) -> int:
        return ChatDocumentVisionContentService.table_structure_max_rows()

    @classmethod
    def min_columns(cls) -> int:
        return ChatDocumentVisionContentService.table_structure_min_columns()

    @classmethod
    def is_noise_row(cls, cells: list[str] | dict[int, str]) -> bool:
        if isinstance(cells, dict):
            values = [str(value or "").strip() for value in cells.values() if str(value or "").strip()]
        else:
            values = [str(value or "").strip() for value in cells if str(value or "").strip()]

        if not values:
            return True

        joined = " | ".join(values)

        for pattern in ChatDocumentVisionContentService.table_structure_noise_row_patterns():
            if pattern.search(joined):
                return True

        if cls._row_has_anchor_cell(values):
            return False

        if all(len(value) <= 6 for value in values) and all(
            re.fullmatch(r"[DO0-9\s./|]+", value, re.IGNORECASE) for value in values
        ):
            return True

        if all(len(value) <= 2 for value in values):
            return True

        return False

    @classmethod
    def _parse_rows(cls, text: str) -> list[list[str]]:
        if "|" in text and cls._looks_like_tabular_header(text):
            parsed = cls._parse_delimited_rows(text, delimiter="|")

            if parsed:
                return cls._reanchor_table_rows(parsed)

        if "\t" in text:
            parsed = cls._parse_delimited_rows(text, delimiter="\t")

            if parsed:
                return cls._reanchor_table_rows(parsed)

        parsed = cls._parse_whitespace_rows(text)

        if parsed:
            return cls._reanchor_table_rows(parsed)

        return parsed

    @classmethod
    def _parse_delimited_rows(cls, text: str, *, delimiter: str) -> list[list[str]]:
        rows: list[list[str]] = []
        min_partial = ChatDocumentVisionContentService.table_structure_min_partial_row_columns()

        for line in text.splitlines():
            stripped = str(line or "").strip()

            if not stripped or stripped.replace(delimiter, "").strip() == "":
                continue

            cells = cls._split_delimited_cells(stripped, delimiter=delimiter)

            if len(cells) >= cls.min_columns():
                rows.append(cells)
                continue

            if len(cells) >= min_partial and cls._row_has_anchor_cell(cells):
                rows.append(cells)

        return rows

    @classmethod
    def _split_delimited_cells(cls, line: str, *, delimiter: str) -> list[str]:
        if delimiter == "|":
            cells = [cell.strip().strip("._") for cell in line.strip("|").split("|")]
        else:
            cells = [cell.strip().strip("._") for cell in line.split(delimiter)]

        return [cell for cell in cells if cell]

    @classmethod
    def _parse_whitespace_rows(cls, text: str) -> list[list[str]]:
        rows: list[list[str]] = []
        pattern = re.compile(r"\s{2,}")

        for line in text.splitlines():
            stripped = str(line or "").strip()

            if not stripped:
                continue

            cells = [cell.strip() for cell in pattern.split(stripped) if cell.strip()]

            if len(cells) >= cls.min_columns():
                rows.append(cells)

        return rows

    @classmethod
    def _reanchor_table_rows(cls, rows: list[list[str]]) -> list[list[str]]:
        if len(rows) < 2:
            return rows

        anchor_index = cls._first_anchor_row_index(rows)

        if anchor_index is None:
            filtered = [rows[0]] + [
                row for row in rows[1:] if not cls.is_noise_row(row)
            ]
            return filtered if len(filtered) >= 2 else rows

        header_candidates = rows[:anchor_index]

        if not header_candidates:
            header = rows[0]
            body = rows[anchor_index:]
        else:
            body = rows[anchor_index:]
            header = cls._pick_header_row(
                header_candidates,
                body_width=len(body[0]) if body else len(header_candidates[-1]),
            )
            body = rows[anchor_index:]

        filtered_body = [row for row in body if not cls.is_noise_row(row)]

        if not filtered_body:
            filtered_body = body

        normalized_body = [cls._normalize_body_row(row, header_width=len(header)) for row in filtered_body]

        return [header] + normalized_body

    @classmethod
    def _first_anchor_row_index(cls, rows: list[list[str]]) -> int | None:
        scan_limit = min(
            len(rows),
            ChatDocumentVisionContentService.table_structure_header_scan_max_lines(),
        )
        best_index: int | None = None
        best_score = float("-inf")

        for index in range(scan_limit):
            row = rows[index]

            if not cls._row_has_anchor_cell(row):
                continue

            score = cls._anchor_row_score(row)

            if score > best_score:
                best_score = score
                best_index = index

        return best_index

    @classmethod
    def _anchor_row_score(cls, cells: list[str]) -> float:
        width = len(cells)
        anchor_hits = sum(1 for cell in cells if cls._anchor_pattern().search(str(cell or "")))
        score = float(anchor_hits)

        if 4 <= width <= 6:
            score += 10.0
        elif width == 3:
            score += 4.0
        elif width > 7:
            score -= 6.0

        if anchor_hits == 1:
            score += 5.0
        elif anchor_hits > 1:
            score -= 4.0

        if cls._row_has_short_quantity_cell(cells):
            score += 3.0

        return score

    @classmethod
    def _row_has_short_quantity_cell(cls, cells: list[str]) -> bool:
        for cell in cells:
            text = str(cell or "").strip().replace(",", ".")

            if re.fullmatch(r"\d{1,4}(?:\.\d+)?", text):
                return True

        return False

    @classmethod
    def _pick_header_row(
        cls,
        candidates: list[list[str]],
        *,
        body_width: int,
    ) -> list[str]:
        if not candidates:
            return []

        min_hits = ChatDocumentVisionContentService.table_structure_header_min_marker_hits()
        marked = [
            row
            for row in candidates
            if cls._header_score(row) >= min_hits and not cls._row_has_anchor_cell(row)
        ]

        if marked:
            return max(marked, key=lambda row: (cls._header_score(row), len(row)))

        without_anchor = [row for row in candidates if not cls._row_has_anchor_cell(row)]

        if without_anchor:
            return max(
                without_anchor,
                key=lambda row: (cls._header_score(row), -abs(len(row) - body_width), len(row)),
            )

        return max(candidates, key=len)

    @classmethod
    def _header_score(cls, cells: list[str]) -> int:
        markers = ChatDocumentVisionContentService.table_structure_header_markers()
        min_hits = ChatDocumentVisionContentService.table_structure_header_min_marker_hits()
        joined = " ".join(str(cell or "") for cell in cells).upper()
        hits = sum(1 for marker in markers if marker in joined)

        if hits >= min_hits:
            return hits

        if cls._row_has_anchor_cell(cells):
            return 0

        return hits

    @classmethod
    def _row_has_anchor_cell(cls, cells: list[str]) -> bool:
        pattern = cls._anchor_pattern()

        for cell in cells:
            if pattern.search(str(cell or "")):
                return True

        return False

    @classmethod
    def _anchor_pattern(cls) -> re.Pattern[str]:
        if cls._ANCHOR_PATTERN is None:
            digits = ChatDocumentVisionContentService.table_structure_row_anchor_min_digits()
            cls._ANCHOR_PATTERN = re.compile(rf"\b\d{{{digits},}}\b")

        return cls._ANCHOR_PATTERN

    @classmethod
    def _normalize_body_row(cls, cells: list[str], *, header_width: int) -> list[str]:
        if header_width <= 0 or len(cells) >= header_width:
            return cells

        padded = list(cells)

        while len(padded) < header_width:
            padded.append("")

        return padded[:header_width]

    @classmethod
    def _dedupe_tables(cls, tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        best_by_id: dict[str, dict[str, Any]] = {}

        for table in tables:
            table_id = str(table.get("tableId") or "").strip()

            if not table_id:
                continue

            existing = best_by_id.get(table_id)

            if existing is None or cls._table_quality(table) >= cls._table_quality(existing):
                best_by_id[table_id] = table

        return list(best_by_id.values())

    @classmethod
    def _table_quality(cls, table: dict[str, Any]) -> tuple[int, int]:
        rows = table.get("rows")

        if not isinstance(rows, list):
            return (0, 0)

        row_count = len(rows)
        cell_count = sum(
            len(row.get("cells") or [])
            for row in rows
            if isinstance(row, dict)
        )

        return (row_count, cell_count)

    @classmethod
    def _looks_like_tabular_header(cls, text: str) -> bool:
        for line in str(text or "").splitlines()[:6]:
            if "|" not in line:
                continue

            cells = cls._split_delimited_cells(line, delimiter="|")

            if len(cells) >= cls.min_columns():
                return True

        return False
