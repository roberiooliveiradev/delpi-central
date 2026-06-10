"""Tabelas e prosa operacional — helpers canônicos reutilizados pelos presenters de rota."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationOperationalTableService:
    DEFAULT_LIST_LIMIT = 30

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
    def build_fixed_items_table(
        cls,
        host: ExternalActionResultPresenter,
        items: list[dict[str, Any]],
        *,
        table_id: str,
        title: str,
        role: str,
    ) -> dict | None:
        if not items:
            return None

        columns = host._fixed_columns(table_id)
        col_keys = [column["key"] for column in columns if column.get("key")]

        if not col_keys:
            return None

        rows = [
            {key: item.get(key) for key in col_keys}
            for item in items
            if isinstance(item, dict)
        ]

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
    def kv_rows_from_mapping(
        cls,
        host: ExternalActionResultPresenter,
        payload: dict[str, Any],
    ) -> list[dict[str, str]]:
        return [
            {
                "campo": host._column_labels.label_for(str(key)),
                "valor": host._format_field_value(str(key), value),
            }
            for key, value in payload.items()
        ]

    @classmethod
    def summary_kv_rows(
        cls,
        host: ExternalActionResultPresenter,
        summary: dict[str, Any],
        *,
        skip_keys: set[str] | None = None,
    ) -> list[dict[str, str]]:
        skipped = skip_keys or set()

        return [
            {
                "campo": host._column_labels.label_for(str(key)),
                "valor": host._format_field_value(str(key), value),
            }
            for key, value in summary.items()
            if str(key) not in skipped
        ]

    @classmethod
    def enrich_structure_rows(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            row = dict(item)
            raw = row.get("exclusive_raw_material")

            truthy = ChatPresentationVocabularyService.exclusive_raw_material_truthy()

            if isinstance(raw, bool):
                label = ChatPresentationVocabularyService.boolean_label(yes=raw)
            else:
                label = ChatPresentationVocabularyService.boolean_label(
                    yes=str(raw or "").strip().upper() in truthy,
                )

            row["exclusive_raw_material_label"] = label

            if not row.get("component_code") and row.get("product_code"):
                row["component_code"] = row.get("product_code")

            if not row.get("product_code") and row.get("component_code"):
                row["product_code"] = row.get("component_code")

            if not row.get("component_description") and row.get("description"):
                row["component_description"] = row.get("description")

            if not row.get("description") and row.get("component_description"):
                row["description"] = row.get("component_description")

            if not row.get("component_unit") and row.get("unit"):
                row["component_unit"] = row.get("unit")

            enriched.append(row)

        return enriched

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

    @classmethod
    def enrich_stock_position_rows(
        cls,
        items: list[dict[str, Any]],
        *,
        product_code: str = "",
        description: str = "",
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            row = dict(item)

            if product_code and not row.get("product_code"):
                row["product_code"] = product_code

            if description and not row.get("description"):
                row["description"] = description

            enriched.append(row)

        return enriched
