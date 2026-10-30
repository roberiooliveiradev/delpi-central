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
    ("start_date", "start_date_iso"),
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

# Visão "engineering" (Portal Engenharia / Ficha do Produto — spec doc 61):
# cadastro e dados de engenharia/logística, SEM campos comerciais, custo
# ou fiscais (sale_price, standard_cost, last_purchase_price, impostos).
PRODUCT_DETAIL_ENGINEERING_FIELDS = (
    # identification
    "code",
    "description",
    "type",
    "group_code",
    "subgroup",
    "previous_code",
    "active",
    "blocked",
    "customer_reference",
    "customer_reference_old",
    "contractual_product",
    "sales_class",
    # engineering / production
    "drawing_code",
    "unit",
    "secondary_unit",
    "conversion_factor",
    "conversion_type",
    "material_type",
    "production_line",
    "operation_decimal_type",
    "current_revision",
    "last_revision_date",
    "net_weight",
    # stock / logistics
    "default_warehouse",
    "package_quantity",
    "barcode",
    "customer_packaging",
    "make_or_buy",
    # purchase metadata (sem preço)
    "last_purchase_date",
    "lead_time_type",
    "requester_restriction",
    # quality / MRP
    "rohs_indicator",
    "traceability",
    "warranty_product",
    "mrp_considered",
    "suggestion_flag",
    "power_control",
    # Delpi controls
    "initial_consumption_date",
    "created_by",
    "updated_by",
    "delpi_category",
    "delpi_segment",
    "qtd_pi",
)

# Visão "engineering" do vínculo produto×fornecedor — sem last_price /
# last_price_date (dado comercial sensível, doc 63 §4).
PRODUCT_SUPPLIER_ENGINEERING_FIELDS = (
    "product_code",
    "product_description",
    "unit",
    "supplier_code",
    "supplier_store",
    "supplier_name",
    "supplier_part_number",
    "catalog_code",
    "barcode",
    "registered_lead_time_days",
    "real_avg_lead_time_days",
    "real_min_lead_time_days",
    "real_max_lead_time_days",
    "real_lead_time_sample_size",
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
    """Converte data Protheus/BR/ISO → ``YYYY-MM-DD`` (borda HTTP)."""
    from app.application.services.response_date_format_service import (
        ResponseDateFormatService,
    )

    return ResponseDateFormatService.format_date(value)


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
    """Primário vira ISO; companion ``*_iso`` permanece como alias (deprecado)."""
    for raw_field, iso_field in DATE_FIELD_PAIRS:
        raw_value = payload.get(raw_field)
        if legacy:
            payload.pop(iso_field, None)
            continue
        iso_value = protheus_date_to_iso(raw_value if isinstance(raw_value, str) else None)
        if iso_value:
            payload[raw_field] = iso_value
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
    if not isinstance(product, dict) or view == "full":
        return product

    allowed = (
        PRODUCT_DETAIL_SUMMARY_FIELDS
        if view == "summary"
        else PRODUCT_DETAIL_ENGINEERING_FIELDS
        if view == "engineering"
        else None
    )
    if allowed is None:
        return product

    return {field: product.get(field) for field in allowed if field in product}


def narrow_supplier_fields(
    supplier: dict[str, Any], *, view: str = "full"
) -> dict[str, Any]:
    if not isinstance(supplier, dict) or view != "engineering":
        return supplier
    return {
        field: supplier.get(field)
        for field in PRODUCT_SUPPLIER_ENGINEERING_FIELDS
        if field in supplier
    }


def narrow_paged_items(
    payload: dict[str, Any],
    narrow,
    *,
    view: str = "full",
) -> dict[str, Any]:
    """Aplica narrowing item a item em payload ``{items: [...]}``."""
    if view == "full" or not isinstance(payload, dict):
        return payload
    items = payload.get("items")
    if not isinstance(items, list):
        return payload
    return {
        **payload,
        "items": [narrow(item, view=view) for item in items],
    }
