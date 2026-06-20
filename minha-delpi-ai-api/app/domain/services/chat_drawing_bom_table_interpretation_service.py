"""Interpretação de tabelas genéricas como BOM DELPI — skill desenho."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingBomTableInterpretationService:
    @classmethod
    def bom_rows_from_tables(
        cls,
        tables: list[dict[str, Any]],
        *,
        product_code: str | None = None,
    ) -> list[dict[str, Any]]:
        exclude = ChatProductQueryIntentService.normalize_product_code(product_code or "")
        best_rows: list[dict[str, Any]] = []
        best_score = -1

        for table in tables:
            if not isinstance(table, dict):
                continue

            rows = cls._rows_from_table(table, exclude=exclude)
            score = cls._score_rows(rows)

            if score > best_score:
                best_score = score
                best_rows = rows

        return best_rows

    @classmethod
    def bom_rows_from_metadata(
        cls,
        metadata: dict[str, Any] | None,
        *,
        product_code: str | None = None,
    ) -> list[dict[str, Any]]:
        meta = metadata if isinstance(metadata, dict) else {}
        tables: list[dict[str, Any]] = []

        structured = meta.get("structuredTables")

        if isinstance(structured, list):
            tables.extend(item for item in structured if isinstance(item, dict))

        document_vision = meta.get("documentVision")

        if isinstance(document_vision, dict):
            vision_tables = document_vision.get("tables")

            if isinstance(vision_tables, list):
                for item in vision_tables:
                    normalized = cls._normalize_legacy_table(item)

                    if normalized:
                        tables.append(normalized)

        return cls.bom_rows_from_tables(tables, product_code=product_code)

    @classmethod
    def resolve_column_indices(cls, table: dict[str, Any]) -> dict[str, int | None]:
        columns = table.get("columns")

        if not isinstance(columns, list):
            return {
                "position": None,
                "code": None,
                "quantity": None,
                "unit": None,
                "description": None,
            }

        resolved: dict[str, int | None] = {
            "position": None,
            "code": None,
            "quantity": None,
            "unit": None,
            "description": None,
        }

        for column in columns:
            if not isinstance(column, dict):
                continue

            index = column.get("index")

            try:
                col_index = int(index)
            except (TypeError, ValueError):
                continue

            header = str(column.get("headerText") or "").strip()
            role = cls._match_header_role(header)

            if role and resolved.get(role) is None:
                resolved[role] = col_index

        return resolved

    @classmethod
    def _rows_from_table(
        cls,
        table: dict[str, Any],
        *,
        exclude: str,
    ) -> list[dict[str, Any]]:
        columns = cls.resolve_column_indices(table)
        code_col = columns.get("code")
        qty_col = columns.get("quantity")
        desc_col = columns.get("description")

        if code_col is None:
            return []

        rows: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in table.get("rows") or []:
            if not isinstance(row, dict):
                continue

            cells = {
                int(cell.get("col")): str(cell.get("text") or "").strip()
                for cell in (row.get("cells") or [])
                if isinstance(cell, dict) and str(cell.get("text") or "").strip()
            }
            code_raw = cells.get(int(code_col), "")
            match = ChatDrawingPatternsService.component_code().search(code_raw)

            if not match:
                continue

            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if not code or code == exclude or code in seen:
                continue

            quantity = cells.get(int(qty_col), "") if qty_col is not None else ""
            description = cells.get(int(desc_col), "") if desc_col is not None else ""

            if not quantity and qty_col is None:
                continue

            rows.append(
                {
                    "code": code,
                    "quantity": cls._normalize_quantity_text(quantity),
                    "description": (description or None),
                    "quantitySource": "column",
                    "quantityTrusted": bool(str(quantity or "").strip()),
                }
            )
            seen.add(code)

        return rows

    @classmethod
    def _normalize_legacy_table(cls, table: dict[str, Any]) -> dict[str, Any] | None:
        if table.get("tableId") and isinstance(table.get("rows"), list):
            first_row = (table.get("rows") or [None])[0]

            if isinstance(first_row, dict) and isinstance(first_row.get("cells"), list):
                return table

        columns_raw = table.get("columns")
        rows_raw = table.get("rows")

        if not isinstance(columns_raw, list) or not isinstance(rows_raw, list):
            return None

        columns = [
            {
                "index": index,
                "headerText": str(value or "").strip(),
            }
            for index, value in enumerate(columns_raw)
        ]
        structured_rows: list[dict[str, Any]] = []

        for row_index, row in enumerate(rows_raw):
            if isinstance(row, dict) and isinstance(row.get("cells"), list):
                structured_rows.append(row)
                continue

            if not isinstance(row, list):
                continue

            structured_rows.append(
                {
                    "index": row_index,
                    "cells": [
                        {"col": col_index, "text": str(value or "").strip()}
                        for col_index, value in enumerate(row)
                    ],
                }
            )

        if len(structured_rows) < 1:
            return None

        return {
            "tableId": str(table.get("tableId") or "legacy_table"),
            "sourceRegion": str(table.get("sourceRegion") or "text"),
            "format": str(table.get("format") or "legacy"),
            "columns": columns,
            "rows": structured_rows,
            "rowCount": len(structured_rows),
        }

    @classmethod
    def _match_header_role(cls, header: str) -> str | None:
        normalized = re.sub(r"\s+", " ", str(header or "").strip()).upper()

        if not normalized:
            return None

        for role in ("position", "code", "quantity", "unit", "description"):
            terms = ChatDrawingPatternsService.bom_column_header_terms(role)

            for term in terms:
                token = str(term or "").strip().upper()

                if token and token in normalized:
                    return role

        return None

    @classmethod
    def _normalize_quantity_text(cls, raw: str) -> str | None:
        text = str(raw or "").strip()

        if not text:
            return None

        upper = text.upper()

        if upper in {"PI", "PC", "UN"}:
            return "1"

        cleaned = text.replace(",", ".").strip()

        if re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
            return cleaned

        return text

    @classmethod
    def _score_rows(cls, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return -1

        return len(rows) * 10 + sum(
            1 for row in rows if str(row.get("quantitySource") or "") == "column"
        )
