"""Interpretação de tabelas genéricas como BOM DELPI — skill desenho."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingBomTableInterpretationService:
    _ROLES = ("position", "code", "quantity", "unit", "description")

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
            return cls._empty_column_map()

        resolved = cls._empty_column_map()

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

        if ChatDrawingPatternsService.bom_column_inference_enabled():
            for column in columns:
                if not isinstance(column, dict):
                    continue

                index = column.get("index")

                try:
                    col_index = int(index)
                except (TypeError, ValueError):
                    continue

                header = str(column.get("headerText") or "").strip()
                fuzzy_role = cls._fuzzy_match_header_role(header)

                if fuzzy_role and resolved.get(fuzzy_role) is None:
                    resolved[fuzzy_role] = col_index

            resolved = cls._infer_missing_columns(table, resolved)

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
            qty_source = "column"

            if qty_col is not None and not cls._header_matches_role(
                table,
                col_index=int(qty_col),
                role="quantity",
            ):
                qty_source = "column_inferred"

            if not quantity and qty_col is None:
                continue

            rows.append(
                {
                    "code": code,
                    "quantity": cls._normalize_quantity_text(quantity),
                    "description": (description or None),
                    "quantitySource": qty_source,
                    "quantityTrusted": bool(str(quantity or "").strip()),
                }
            )
            seen.add(code)

        return rows

    @classmethod
    def _infer_missing_columns(
        cls,
        table: dict[str, Any],
        resolved: dict[str, int | None],
    ) -> dict[str, int | None]:
        result = dict(resolved)
        col_indices = cls._table_column_indices(table)

        if not col_indices:
            return result

        body_rows = cls._body_cell_rows(table)

        if len(body_rows) < cls._min_body_rows_for_inference():
            return result

        profiles = cls._profile_columns(body_rows, col_indices)
        missing_roles = [role for role in cls._ROLES if result.get(role) is None]

        if not missing_roles:
            return result

        for role in missing_roles:
            candidate = cls._best_profile_column(profiles, role, assigned=set(result.values()))

            if candidate is not None:
                result[role] = candidate
                continue

            layout_col = cls._layout_default_column(
                role,
                column_count=len(col_indices),
                col_indices=col_indices,
                assigned=set(result.values()),
            )

            if layout_col is not None:
                result[role] = layout_col

        if result.get("code") is not None and result.get("quantity") is None:
            adjacent = cls._adjacent_quantity_column(
                code_col=int(result["code"]),
                profiles=profiles,
                assigned=set(result.values()),
            )

            if adjacent is not None:
                result["quantity"] = adjacent

        return result

    @classmethod
    def _profile_columns(
        cls,
        body_rows: list[dict[int, str]],
        col_indices: list[int],
    ) -> dict[int, dict[str, float]]:
        profiles: dict[int, dict[str, float]] = {}

        for col_index in col_indices:
            values = [row.get(col_index, "") for row in body_rows if row.get(col_index)]
            total = len(values)

            if total == 0:
                continue

            profiles[col_index] = {
                "position": cls._score_position_column(values, total),
                "code": cls._score_code_column(values, total),
                "quantity": cls._score_quantity_column(values, total),
                "unit": cls._score_unit_column(values, total),
                "description": cls._score_description_column(values, total),
            }

        return profiles

    @classmethod
    def _best_profile_column(
        cls,
        profiles: dict[int, dict[str, float]],
        role: str,
        *,
        assigned: set[int | None],
    ) -> int | None:
        min_score = float(
            ChatDrawingPatternsService.bom_column_inference_rule("minColumnMatchScore", 0.45)
        )
        best_index: int | None = None
        best_score = min_score

        for col_index, scores in profiles.items():
            if col_index in assigned:
                continue

            score = float(scores.get(role) or 0.0)

            if score > best_score:
                best_score = score
                best_index = col_index

        return best_index

    @classmethod
    def _layout_default_column(
        cls,
        role: str,
        *,
        column_count: int,
        col_indices: list[int],
        assigned: set[int | None],
    ) -> int | None:
        layout = ChatDrawingPatternsService.bom_column_default_layout(column_count)

        if not layout or role not in layout:
            return None

        role_index = layout.index(role)

        if role_index >= len(col_indices):
            return None

        candidate = col_indices[role_index]

        if candidate in assigned:
            return None

        return candidate

    @classmethod
    def _adjacent_quantity_column(
        cls,
        *,
        code_col: int,
        profiles: dict[int, dict[str, float]],
        assigned: set[int | None],
    ) -> int | None:
        min_score = float(
            ChatDrawingPatternsService.bom_column_inference_rule("minColumnMatchScore", 0.45)
        ) * 0.75
        candidates = [code_col - 1, code_col + 1, code_col - 2]
        best_index: int | None = None
        best_score = min_score

        for col_index in candidates:
            if col_index in assigned:
                continue

            scores = profiles.get(col_index)

            if not scores:
                continue

            score = float(scores.get("quantity") or 0.0)

            if score > best_score:
                best_score = score
                best_index = col_index

        return best_index

    @classmethod
    def _score_code_column(cls, values: list[str], total: int) -> float:
        hits = sum(
            1
            for value in values
            if ChatDrawingPatternsService.component_code().search(value)
        )

        return hits / total

    @classmethod
    def _score_quantity_column(cls, values: list[str], total: int) -> float:
        max_digits = int(
            ChatDrawingPatternsService.bom_column_inference_rule("quantityMaxDigits", 4)
        )
        hits = 0

        for value in values:
            text = str(value or "").strip()

            if not text:
                continue

            if text.upper() in {"PC", "UN", "UM", "MI", "MT", "KG", "M", "MM"}:
                continue

            upper = text.upper()

            if upper == "PI":
                hits += 1
                continue

            cleaned = text.replace(",", ".")

            if re.fullmatch(rf"\d{{1,{max_digits}}}(?:\.\d+)?", cleaned):
                hits += 1

        return hits / total

    @classmethod
    def _score_description_column(cls, values: list[str], total: int) -> float:
        hits = 0

        for value in values:
            text = str(value or "").strip()

            if len(text) < 8:
                continue

            if ChatDrawingPatternsService.component_code().search(text):
                continue

            if re.search(r"[A-Za-zÀ-ÿ]{3,}", text):
                hits += 1

        return hits / total

    @classmethod
    def _score_position_column(cls, values: list[str], total: int) -> float:
        hits = sum(1 for value in values if re.fullmatch(r"\d{1,3}", str(value or "").strip()))

        return hits / total

    @classmethod
    def _score_unit_column(cls, values: list[str], total: int) -> float:
        units = {token.upper() for token in ChatDrawingPatternsService.piece_count_units()}
        units.update({"UM", "UN", "UNID", "MI", "MT", "PC", "KG", "M", "MM"})

        hits = sum(1 for value in values if str(value or "").strip().upper() in units)

        return hits / total

    @classmethod
    def _header_matches_role(
        cls,
        table: dict[str, Any],
        *,
        col_index: int,
        role: str,
    ) -> bool:
        columns = table.get("columns")

        if not isinstance(columns, list):
            return False

        for column in columns:
            if not isinstance(column, dict):
                continue

            try:
                index = int(column.get("index"))
            except (TypeError, ValueError):
                continue

            if index != int(col_index):
                continue

            header = str(column.get("headerText") or "").strip()
            matched = cls._match_header_role(header)

            if matched == role:
                return True

            if ChatDrawingPatternsService.bom_column_inference_enabled():
                return cls._fuzzy_match_header_role(header) == role

            return False

        return False

    @classmethod
    def _body_cell_rows(cls, table: dict[str, Any]) -> list[dict[int, str]]:
        rows: list[dict[int, str]] = []

        for row in table.get("rows") or []:
            if not isinstance(row, dict):
                continue

            cells = {
                int(cell.get("col")): str(cell.get("text") or "").strip()
                for cell in (row.get("cells") or [])
                if isinstance(cell, dict) and str(cell.get("text") or "").strip()
            }

            if cells:
                rows.append(cells)

        return rows

    @classmethod
    def _table_column_indices(cls, table: dict[str, Any]) -> list[int]:
        indices: set[int] = set()
        columns = table.get("columns")

        if isinstance(columns, list):
            for column in columns:
                if not isinstance(column, dict):
                    continue

                try:
                    indices.add(int(column.get("index")))
                except (TypeError, ValueError):
                    continue

        for row in cls._body_cell_rows(table):
            indices.update(row.keys())

        return sorted(indices)

    @classmethod
    def _fuzzy_match_header_role(cls, header: str) -> str | None:
        normalized_header = cls._normalize_header_token(header)

        if not normalized_header:
            return None

        max_distance = int(
            ChatDrawingPatternsService.bom_column_inference_rule(
                "fuzzyHeaderMaxEditDistance",
                3,
            )
        )
        best_role: str | None = None
        best_distance = max_distance + 1

        for role in cls._ROLES:
            for term in ChatDrawingPatternsService.bom_column_header_terms(role):
                normalized_term = cls._normalize_header_token(term)

                if not normalized_term:
                    continue

                if normalized_term in normalized_header or normalized_header in normalized_term:
                    return role

                distance = cls._edit_distance(normalized_header, normalized_term)

                if distance <= max_distance and distance < best_distance:
                    best_distance = distance
                    best_role = role

        return best_role

    @classmethod
    def _normalize_header_token(cls, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", str(text or ""))
        stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
        cleaned = re.sub(r"[^A-Za-z0-9]+", "", stripped)

        return cleaned.upper()

    @classmethod
    def _edit_distance(cls, left: str, right: str) -> int:
        if left == right:
            return 0

        if not left:
            return len(right)

        if not right:
            return len(left)

        previous = list(range(len(right) + 1))

        for i, left_char in enumerate(left, start=1):
            current = [i]
            for j, right_char in enumerate(right, start=1):
                insert_cost = current[j - 1] + 1
                delete_cost = previous[j] + 1
                replace_cost = previous[j - 1] + (left_char != right_char)
                current.append(min(insert_cost, delete_cost, replace_cost))

            previous = current

        return previous[-1]

    @classmethod
    def _min_body_rows_for_inference(cls) -> int:
        try:
            return max(
                1,
                int(
                    ChatDrawingPatternsService.bom_column_inference_rule(
                        "minBodyRowsForInference",
                        2,
                    )
                ),
            )
        except (TypeError, ValueError):
            return 2

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

        for role in cls._ROLES:
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
            1
            for row in rows
            if str(row.get("quantitySource") or "") in {"column", "column_inferred"}
        )

    @classmethod
    def _empty_column_map(cls) -> dict[str, int | None]:
        return {
            "position": None,
            "code": None,
            "quantity": None,
            "unit": None,
            "description": None,
        }
