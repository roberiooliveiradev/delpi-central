"""Enriquecimento de linhas específico de rotas tier A — fora do builder genérico (R19)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

LMP_ITEM_ALIASES: dict[str, tuple[str, ...]] = {
    "sale_number": ("saleNumber",),
    "listing_kind": ("listingKind",),
    "sale_description": ("saleDescription",),
    "status": ("engineering_status",),
}


def apply_field_aliases(
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


def normalize_lmp_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        apply_field_aliases(item, LMP_ITEM_ALIASES)
        for item in items
        if isinstance(item, dict)
    ]


def enrich_structure_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def enrich_stock_position_rows(
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
