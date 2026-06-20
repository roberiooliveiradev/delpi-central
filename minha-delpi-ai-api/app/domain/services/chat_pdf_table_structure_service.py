"""Estrutura tabular genérica a partir de texto OCR — chat base (sem semântica BOM)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


class ChatPdfTableStructureService:
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
    def _parse_rows(cls, text: str) -> list[list[str]]:
        if "|" in text and cls._looks_like_tabular_header(text):
            return cls._parse_delimited_rows(text, delimiter="|")

        if "\t" in text:
            parsed = cls._parse_delimited_rows(text, delimiter="\t")

            if parsed:
                return parsed

        return cls._parse_whitespace_rows(text)

    @classmethod
    def _parse_delimited_rows(cls, text: str, *, delimiter: str) -> list[list[str]]:
        rows: list[list[str]] = []

        for line in text.splitlines():
            stripped = str(line or "").strip()

            if not stripped or stripped.replace(delimiter, "").strip() == "":
                continue

            if delimiter == "|":
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            else:
                cells = [cell.strip() for cell in stripped.split(delimiter)]

            cells = [cell for cell in cells if cell]

            if len(cells) >= cls.min_columns():
                rows.append(cells)

        return rows

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
    def _dedupe_tables(cls, tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        resolved: list[dict[str, Any]] = []

        for table in tables:
            table_id = str(table.get("tableId") or "").strip()

            if not table_id or table_id in seen:
                continue

            seen.add(table_id)
            resolved.append(table)

        return resolved

    @classmethod
    def _looks_like_tabular_header(cls, text: str) -> bool:
        for line in str(text or "").splitlines()[:6]:
            if "|" not in line:
                continue

            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]

            if len(cells) >= cls.min_columns():
                return True

        return False
