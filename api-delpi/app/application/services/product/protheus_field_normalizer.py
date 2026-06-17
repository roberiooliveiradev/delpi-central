"""Normalização de campos Protheus (SIM/NAO, datas YYYYMMDD) para consumo HTTP."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

PROTHEUS_YES_VALUES = frozenset({"SIM", "SIM_SC2"})
PROTHEUS_NO_VALUES = frozenset({"NAO", "NÃO"})

YES_NO_ITEM_FIELDS = (
    "exclusive_raw_material",
    "has_stock_for_one_pa",
    "production_started",
)

YES_NO_SUMMARY_FIELDS = (
    "pa_production_started",
    "pi_production_started",
)

DATE_FIELD_PAIRS = (
    ("reference_date", "reference_date_iso"),
    ("date_start", "date_start_iso"),
    ("date_end_exclusive", "date_end_exclusive_iso"),
)

PRODUCT_DETAIL_SUMMARY_FIELDS = (
    "code",
    "description",
    "type",
    "unit",
    "group_code",
    "active",
    "blocked",
    "default_warehouse",
    "sale_price",
    "standard_cost",
    "last_purchase_price",
    "ncm_ipi_position",
    "current_revision",
    "last_revision_date",
    "make_or_buy",
)


def protheus_yes_no_label(value: str | None) -> str | None:
    if value in PROTHEUS_YES_VALUES:
        return "Sim"
    if value in PROTHEUS_NO_VALUES:
        return "Não"
    return None


def parse_protheus_yes_no(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    if normalized in PROTHEUS_YES_VALUES:
        return True
    if normalized in PROTHEUS_NO_VALUES:
        return False
    return None


def is_protheus_yes(value: Any) -> bool:
    parsed = parse_protheus_yes_no(value)
    return parsed is True


def protheus_date_to_iso(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    digits = value.strip()
    if len(digits) != 8 or not digits.isdigit():
        return None
    try:
        return datetime.strptime(digits, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def _normalize_yes_no_field(item: dict[str, Any], field: str, *, legacy: bool) -> None:
    raw = item.get(field)
    if raw is None:
        return

    if legacy:
        item.pop(f"{field}_label", None)
        return

    if isinstance(raw, bool):
        item[f"{field}_label"] = "Sim" if raw else "Não"
        return

    if not isinstance(raw, str):
        return

    parsed = parse_protheus_yes_no(raw)
    if parsed is None:
        return

    item[field] = parsed
    item[f"{field}_label"] = protheus_yes_no_label(raw) or ("Sim" if parsed else "Não")


def _normalize_item_row(row: dict[str, Any], *, legacy: bool) -> dict[str, Any]:
    if not isinstance(row, dict):
        return row

    from app.domain.services.product.product_playbook_numeric_service import (
        ProductPlaybookNumericService,
    )

    normalized = ProductPlaybookNumericService.normalize_row_quantities(dict(row))
    for field in YES_NO_ITEM_FIELDS:
        _normalize_yes_no_field(normalized, field, legacy=legacy)
    return normalized


def _normalize_summary(summary: dict[str, Any], *, legacy: bool) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return summary

    from app.domain.services.product.product_playbook_numeric_service import (
        ProductPlaybookNumericService,
    )

    normalized = dict(summary)
    materials = normalized.get("materials")

    if isinstance(materials, list):
        normalized["materials"] = [
            ProductPlaybookNumericService.normalize_row_quantities(item)
            if isinstance(item, dict)
            else item
            for item in materials
        ]

    for field in YES_NO_SUMMARY_FIELDS:
        _normalize_yes_no_field(normalized, field, legacy=legacy)

    for field in (
        "max_pa_producible_from_stock_exact",
        "total_pa_reported_quantity",
        "total_pi_reported_quantity",
        "total_shipped_quantity",
        "total_inspection_loss_quantity",
    ):
        if field in normalized:
            normalized[field] = ProductPlaybookNumericService.format_quantity(
                normalized[field]
            )

    return normalized


def _normalize_dates(payload: dict[str, Any], *, legacy: bool) -> None:
    for raw_field, iso_field in DATE_FIELD_PAIRS:
        raw_value = payload.get(raw_field)
        if legacy:
            payload.pop(iso_field, None)
            continue
        if isinstance(raw_value, str):
            iso_value = protheus_date_to_iso(raw_value)
            if iso_value:
                payload[iso_field] = iso_value


def normalize_playbook_payload(data: dict[str, Any], *, legacy: bool = False) -> dict[str, Any]:
    payload = deepcopy(data)

    if isinstance(payload.get("items"), list):
        payload["items"] = [
            _normalize_item_row(item, legacy=legacy) for item in payload["items"]
        ]

    if isinstance(payload.get("summary"), dict):
        payload["summary"] = _normalize_summary(payload["summary"], legacy=legacy)

    for section_key in ("structure", "raw_material_stock", "production", "shipping"):
        section = payload.get(section_key)
        if not isinstance(section, dict):
            continue
        if isinstance(section.get("items"), list):
            section["items"] = [
                _normalize_item_row(item, legacy=legacy) for item in section["items"]
            ]
        if isinstance(section.get("summary"), dict):
            section["summary"] = _normalize_summary(section["summary"], legacy=legacy)

    _normalize_dates(payload, legacy=legacy)
    return payload


def normalize_stock_payload(data: dict[str, Any], *, legacy: bool = False) -> dict[str, Any]:
    payload = deepcopy(data)
    items = payload.get("items")

    if not isinstance(items, list):
        return payload

    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            normalized_items.append(item)
            continue
        row = dict(item)
        warehouse = row.get("warehouse")
        if not legacy and warehouse is not None and "location" not in row:
            row["location"] = warehouse
        normalized_items.append(row)

    payload["items"] = normalized_items
    return payload


def narrow_product_fields(product: dict[str, Any], *, view: str = "full") -> dict[str, Any]:
    if view != "summary" or not isinstance(product, dict):
        return product

    return {
        field: product.get(field)
        for field in PRODUCT_DETAIL_SUMMARY_FIELDS
        if field in product
    }
