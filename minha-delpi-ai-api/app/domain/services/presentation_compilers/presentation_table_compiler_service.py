"""Compila spec.table + fields/sort/formats → tablePresentation (visual-only hidden columns)."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.presentation_format_mapping_service import (
    PresentationFormatMappingService,
)


class PresentationTableCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        for table in cls._collect_tables(metadata):
            cls._compile_table(
                table,
                spec=spec,
                labels=labels,
                formats=formats,
            )

    @classmethod
    def _collect_tables(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        for key in ("tablePresentation", "presentation"):
            value = metadata.get(key)
            if isinstance(value, dict) and value.get("type") == "table":
                tables.append(value)
        multi = metadata.get("tablePresentations")
        if isinstance(multi, list):
            tables.extend(item for item in multi if isinstance(item, dict))
        return tables

    @classmethod
    def _compile_table(
        cls,
        table: dict[str, Any],
        *,
        spec: PresentationSpec,
        labels: dict[str, str],
        formats: dict[str, str],
    ) -> None:
        columns = table.get("columns")
        if not isinstance(columns, list):
            return

        preferred = list(spec.fields) if spec.fields else None
        hidden = set(spec.table.hidden_fields) if spec.table else set()

        normalized: list[dict[str, Any]] = []
        export_columns: list[dict[str, Any]] = []

        for column in columns:
            if not isinstance(column, dict):
                continue
            key = str(column.get("key") or "").strip()
            if not key:
                continue
            if preferred and key not in preferred:
                continue

            label = labels.get(key) or str(column.get("label") or key)
            entry = dict(column)
            entry["key"] = key
            entry["label"] = label
            if formats.get(key) and not entry.get("dataType"):
                mapped = PresentationFormatMappingService.to_mfe_data_type(formats[key])
                if mapped:
                    entry["dataType"] = mapped

            export_columns.append(dict(entry))
            if key not in hidden:
                normalized.append(entry)

        if preferred:
            order = {field_key: index for index, field_key in enumerate(preferred)}
            normalized.sort(key=lambda item: order.get(str(item.get("key")), 10_000))
            export_columns.sort(key=lambda item: order.get(str(item.get("key")), 10_000))

        if normalized:
            table["columns"] = normalized
        if export_columns:
            table["exportColumns"] = export_columns

        rows = table.get("rows")
        if isinstance(rows, list) and spec.sort_field:
            table["rows"] = cls._sort_rows(
                rows,
                field=spec.sort_field,
                direction=spec.sort_direction or "desc",
            )

        if spec.table:
            config = dict(table.get("config") or {})
            if spec.table.density:
                config["density"] = spec.table.density
            if spec.table.role:
                config["role"] = spec.table.role
            if spec.table.title:
                table["title"] = spec.table.title
            if hidden:
                config["hiddenFields"] = sorted(hidden)
                config["exportSourceUnchanged"] = True
            config["bindingProvenance"] = "COMPILED"
            table["config"] = config

    @classmethod
    def _sort_rows(
        cls,
        rows: list[Any],
        *,
        field: str,
        direction: str,
    ) -> list[dict[str, Any]]:
        typed = [row for row in rows if isinstance(row, dict)]
        if not typed:
            return typed

        reverse = str(direction or "desc").strip().lower() != "asc"

        def sort_key(row: dict[str, Any]) -> tuple[int, Any]:
            value = row.get(field)
            if value is None:
                return (1, "")
            if isinstance(value, (int, float)):
                return (0, value)
            try:
                return (0, float(value))
            except (TypeError, ValueError):
                return (0, str(value).casefold())

        return sorted(typed, key=sort_key, reverse=reverse)
