"""Extração heurística de tabelas em texto OCR/markdown — Onda 13 (contrato `tables[]`)."""

from __future__ import annotations

import re
from typing import Any

_PIPE_ROW_RE = re.compile(r"^\|?.+\|.+\|?\s*$")
_PIPE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")


class ChatDocumentVisionTablesService:
    @classmethod
    def extract_tables(cls, text: str, *, max_tables: int = 3, max_rows: int = 40) -> list[dict[str, Any]]:
        normalized = str(text or "").strip()

        if not normalized:
            return []

        tables: list[dict[str, Any]] = []
        markdown_tables = cls._extract_markdown_tables(normalized, max_tables=max_tables, max_rows=max_rows)

        tables.extend(markdown_tables)

        if len(tables) < max_tables:
            tables.extend(
                cls._extract_tsv_blocks(
                    normalized,
                    max_tables=max_tables - len(tables),
                    max_rows=max_rows,
                )
            )

        return tables[:max_tables]

    @classmethod
    def _extract_markdown_tables(
        cls,
        text: str,
        *,
        max_tables: int,
        max_rows: int,
    ) -> list[dict[str, Any]]:
        lines = text.splitlines()
        tables: list[dict[str, Any]] = []
        index = 0

        while index < len(lines) and len(tables) < max_tables:
            line = lines[index].strip()

            if not _PIPE_ROW_RE.match(line):
                index += 1
                continue

            block: list[str] = []

            while index < len(lines) and _PIPE_ROW_RE.match(lines[index].strip()):
                block.append(lines[index].strip())
                index += 1

            parsed = cls._parse_markdown_block(block, max_rows=max_rows)

            if parsed:
                tables.append(parsed)

        return tables

    @classmethod
    def _parse_markdown_block(cls, block: list[str], *, max_rows: int) -> dict[str, Any] | None:
        rows: list[list[str]] = []

        for line in block:
            if _PIPE_SEP_RE.match(line):
                continue

            cells = [cell.strip() for cell in line.strip("|").split("|")]
            cells = [cell for cell in cells if cell]

            if cells:
                rows.append(cells)

        if len(rows) < 2:
            return None

        header = rows[0]
        body = rows[1 : max_rows + 1]

        return {
            "format": "markdown",
            "columns": header,
            "rows": body,
            "rowCount": len(body),
        }

    @classmethod
    def _extract_tsv_blocks(
        cls,
        text: str,
        *,
        max_tables: int,
        max_rows: int,
    ) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        block: list[str] = []

        for line in text.splitlines():
            if "\t" in line and line.count("\t") >= 1:
                block.append(line)

                continue

            if len(block) >= 2:
                parsed = cls._parse_tsv_block(block, max_rows=max_rows)

                if parsed:
                    tables.append(parsed)

                    if len(tables) >= max_tables:
                        return tables

            block = []

        if len(block) >= 2:
            parsed = cls._parse_tsv_block(block, max_rows=max_rows)

            if parsed:
                tables.append(parsed)

        return tables[:max_tables]

    @classmethod
    def _parse_tsv_block(cls, block: list[str], *, max_rows: int) -> dict[str, Any] | None:
        rows = [
            [cell.strip() for cell in line.split("\t") if cell.strip()]
            for line in block
            if line.strip()
        ]
        rows = [row for row in rows if len(row) >= 2]

        if len(rows) < 2:
            return None

        return {
            "format": "tsv",
            "columns": rows[0],
            "rows": rows[1 : max_rows + 1],
            "rowCount": len(rows) - 1,
        }
