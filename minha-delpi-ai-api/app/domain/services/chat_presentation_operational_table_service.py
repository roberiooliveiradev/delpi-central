"""Tabelas e prosa operacional — helpers canônicos reutilizados pelos presenters de rota."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_column_label_context import ColumnLabelContext
from app.domain.services.chat_presentation_field_label_resolution_service import (
    ChatPresentationFieldLabelResolutionService,
)


class ChatPresentationOperationalTableService:
    DEFAULT_LIST_LIMIT = 30

    @classmethod
    def join_narrative_lines(cls, lines: list[str]) -> str:
        return "\n\n".join(line for line in lines if line)

    @classmethod
    def join_markdown_blocks(cls, parts: list[str | None]) -> str:
        blocks: list[str] = []
        current: list[str] = []

        for part in parts:
            if part is None:
                continue

            text = str(part).strip()

            if not text:
                if current:
                    blocks.append("\n".join(current))
                    current = []
                continue

            if text.startswith("**") and text.endswith("**") and current:
                blocks.append("\n".join(current))
                current = [text]
                continue

            current.append(text)

        if current:
            blocks.append("\n".join(current))

        return "\n\n".join(block for block in blocks if block).strip()

    @classmethod
    def build_items_table(
        cls,
        context: ColumnLabelContext,
        items: list[dict[str, Any]],
        *,
        title: str,
        role: str,
        path: str = "",
        profile_name: str | None = None,
    ) -> dict | None:
        dict_items = [item for item in items if isinstance(item, dict)]

        if not dict_items:
            return None

        columns = context.resolve_columns_for_items(
            dict_items,
            path=path,
            profile_name=profile_name,
        )
        col_keys = [column["key"] for column in columns if column.get("key")]

        if not col_keys:
            return None

        rows = []

        for item in dict_items:
            row = {key: item.get(key) for key in col_keys}

            if isinstance(item.get("_detailMeta"), dict):
                row["_detailMeta"] = dict(item["_detailMeta"])

            if item.get("row_emphasis"):
                row["row_emphasis"] = item["row_emphasis"]

            rows.append(row)

        if not rows:
            return None

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": rows,
            "role": role,
        }

    @classmethod
    def limit_items(
        cls,
        items: list[dict[str, Any]],
        *,
        limit: int | None = None,
        sort_key: str | None = None,
        reverse: bool = True,
    ) -> tuple[list[dict[str, Any]], int]:
        total = len(items)
        effective_limit = limit if limit is not None else cls.DEFAULT_LIST_LIMIT
        ordered = list(items)

        if sort_key:
            ordered.sort(
                key=lambda item: str(item.get(sort_key) or ""),
                reverse=reverse,
            )

        if total <= effective_limit:
            return ordered, total

        return ordered[:effective_limit], total

    @classmethod
    def _effective_label_path(cls, context: ColumnLabelContext, path: str) -> str:
        return path or getattr(context, "path", "") or ""

    @classmethod
    def kv_rows_from_mapping(
        cls,
        context: ColumnLabelContext,
        payload: dict[str, Any],
        *,
        path: str = "",
        profile_name: str | None = None,
    ) -> list[dict[str, str]]:
        return ChatPresentationFieldLabelResolutionService.build_kv_rows(
            payload,
            format_value=lambda key, value, schema_formats=None: context.format_field_value(
                key,
                value,
            ),
            path=cls._effective_label_path(context, path),
            profile_name=profile_name,
            schema_labels=context.schema_labels,
            schema_formats=context.schema_formats,
        )

    @classmethod
    def summary_kv_rows(
        cls,
        context: ColumnLabelContext,
        summary: dict[str, Any],
        *,
        path: str = "",
        profile_name: str | None = None,
        skip_keys: set[str] | None = None,
    ) -> list[dict[str, str]]:
        skipped = skip_keys or set()

        return ChatPresentationFieldLabelResolutionService.build_kv_rows(
            summary,
            format_value=lambda key, value, schema_formats=None: context.format_field_value(
                key,
                value,
            ),
            path=cls._effective_label_path(context, path),
            profile_name=profile_name,
            schema_labels=context.schema_labels,
            schema_formats=context.schema_formats,
            skip_keys=skipped,
        )

    @classmethod
    def parse_quantity(cls, value: object) -> float:
        if value is None or value == "":
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().replace(",", ".")

        try:
            return float(text)
        except ValueError:
            return 0.0

    @classmethod
    def has_nested_bom_items(cls, items: list[dict[str, Any]]) -> bool:
        for item in items:
            if not isinstance(item, dict):
                continue

            if str(item.get("parent_code") or "").strip():
                return True

            try:
                level = int(item.get("level") or 0)
            except (TypeError, ValueError):
                level = 0

            if level > 1:
                return True

        return len(items) > 1
