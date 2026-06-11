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

    LMP_ITEM_ALIASES: dict[str, tuple[str, ...]] = {
        "sale_number": ("saleNumber",),
        "listing_kind": ("listingKind",),
        "sale_description": ("saleDescription",),
        "status": ("engineering_status",),
    }

    @classmethod
    def apply_field_aliases(
        cls,
        item: dict[str, Any],
        aliases: dict[str, tuple[str, ...]],
    ) -> dict[str, Any]:
        row = dict(item)

        for canonical, alternate_keys in aliases.items():
            if row.get(canonical) not in (None, ""):
                continue

            for alt in alternate_keys:
                value = row.get(alt)

                if value not in (None, ""):
                    row[canonical] = value
                    break

        return row

    @classmethod
    def normalize_lmp_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            cls.apply_field_aliases(item, cls.LMP_ITEM_ALIASES)
            for item in items
            if isinstance(item, dict)
        ]

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
    def build_items_table(
        cls,
        host: ExternalActionResultPresenter,
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

        columns = host._column_labels.resolve_columns_for_items(
            dict_items,
            path=path,
            profile_name=profile_name,
            schema_labels=host._active_schema_labels,
        )
        col_keys = [column["key"] for column in columns if column.get("key")]

        if not col_keys:
            return None

        rows = []

        for item in dict_items:
            row = {key: item.get(key) for key in col_keys}

            if isinstance(item.get("_detailMeta"), dict):
                row["_detailMeta"] = dict(item["_detailMeta"])

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
    def kv_rows_from_mapping(
        cls,
        host: ExternalActionResultPresenter,
        payload: dict[str, Any],
        *,
        path: str = "",
        profile_name: str | None = None,
    ) -> list[dict[str, str]]:
        from app.domain.services.chat_presentation_field_label_resolution_service import (
            ChatPresentationFieldLabelResolutionService,
        )

        return ChatPresentationFieldLabelResolutionService.build_kv_rows(
            payload,
            format_value=lambda key, value, schema_formats=None: host._format_field_value(
                key,
                value,
            ),
            path=path,
            profile_name=profile_name,
            schema_labels=host._active_schema_labels,
            schema_formats=host._active_schema_formats,
        )

    @classmethod
    def summary_kv_rows(
        cls,
        host: ExternalActionResultPresenter,
        summary: dict[str, Any],
        *,
        path: str = "",
        profile_name: str | None = None,
        skip_keys: set[str] | None = None,
    ) -> list[dict[str, str]]:
        from app.domain.services.chat_presentation_field_label_resolution_service import (
            ChatPresentationFieldLabelResolutionService,
        )

        skipped = skip_keys or set()

        return ChatPresentationFieldLabelResolutionService.build_kv_rows(
            summary,
            format_value=lambda key, value, schema_formats=None: host._format_field_value(
                key,
                value,
            ),
            path=path,
            profile_name=profile_name,
            schema_labels=host._active_schema_labels,
            schema_formats=host._active_schema_formats,
            skip_keys=skipped,
        )

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
