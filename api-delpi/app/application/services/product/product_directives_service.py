from __future__ import annotations

from collections import defaultdict

from app.application.services.product.product_playbook_service import summarize_structure
from app.domain.services.product.product_identifier_resolution_service import (
    ProductIdentifierResolutionService,
    ResolvedProductIdentifier,
)


def extract_raw_material_codes(structure_items: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    for item in structure_items:
        if item.get("component_type") != "MP":
            continue

        code = str(item.get("component_code") or "").strip()
        if not code or code in seen:
            continue

        seen.add(code)
        ordered.append(code)

    return ordered


def group_suppliers_by_product(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        code = str(row.get("product_code") or "").strip()
        if not code:
            continue

        grouped[code].append(
            {
                "supplier_code": row.get("supplier_code"),
                "supplier_store": row.get("supplier_store"),
                "supplier_name": row.get("supplier_name"),
                "supplier_part_number": row.get("supplier_part_number"),
                "catalog_code": row.get("catalog_code"),
                "barcode": row.get("barcode"),
                "registered_lead_time_days": row.get("registered_lead_time_days"),
                "last_price": row.get("last_price"),
                "last_price_date": row.get("last_price_date"),
            }
        )

    return dict(grouped)


def index_last_purchases_by_product(rows: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}

    for row in rows:
        code = str(row.get("product_code") or "").strip()
        if code:
            indexed[code] = row

    return indexed


def build_raw_material_entries(
    structure_items: list[dict],
    suppliers_by_code: dict[str, list[dict]],
    last_purchases_by_code: dict[str, dict],
) -> list[dict]:
    entries: list[dict] = []
    seen: set[str] = set()

    for item in structure_items:
        if item.get("component_type") != "MP":
            continue

        code = str(item.get("component_code") or "").strip()
        if not code or code in seen:
            continue

        seen.add(code)
        entries.append(
            {
                "raw_material_code": code,
                "description": item.get("component_description"),
                "unit": item.get("component_unit"),
                "group_code": item.get("component_group"),
                "level": item.get("level"),
                "parent_code": item.get("parent_code"),
                "quantity_per": item.get("quantity_per"),
                "accumulated_quantity": item.get("accumulated_quantity"),
                "exclusive_raw_material": item.get("exclusive_raw_material"),
                "path": item.get("path"),
                "suppliers": suppliers_by_code.get(code, []),
                "last_purchase": last_purchases_by_code.get(code),
            }
        )

    return entries


def summarize_directives(
    structure_items: list[dict],
    raw_materials: list[dict],
) -> dict:
    structure_summary = summarize_structure(structure_items)
    suppliers_total = sum(len(item.get("suppliers") or []) for item in raw_materials)
    with_last_purchase = sum(
        1 for item in raw_materials if item.get("last_purchase")
    )

    return {
        **structure_summary,
        "total_raw_material_entries": len(raw_materials),
        "total_supplier_links": suppliers_total,
        "raw_materials_with_last_purchase": with_last_purchase,
        "raw_materials_without_last_purchase": len(raw_materials) - with_last_purchase,
    }


def build_product_directives_payload(
    *,
    resolved: ResolvedProductIdentifier,
    structure_items: list[dict],
    suppliers_rows: list[dict],
    last_purchase_rows: list[dict],
) -> dict:
    suppliers_by_code = group_suppliers_by_product(suppliers_rows)
    last_purchases_by_code = index_last_purchases_by_product(last_purchase_rows)
    raw_materials = build_raw_material_entries(
        structure_items,
        suppliers_by_code,
        last_purchases_by_code,
    )

    return {
        "resolution": {
            "identifier": resolved.identifier,
            "identifier_type": resolved.identifier_type,
            "delpi_code": resolved.product_code,
            "customer_reference": resolved.customer_reference,
        },
        "product": {
            "product_code": resolved.product_code,
            "description": resolved.description,
            "product_type": resolved.product_type,
            "unit": resolved.unit,
            "group_code": resolved.group_code,
            "customer_reference": resolved.customer_reference,
        },
        "structure": {
            "items": structure_items,
            "summary": summarize_structure(structure_items),
        },
        "raw_materials": raw_materials,
        "summary": summarize_directives(structure_items, raw_materials),
    }


def resolve_product_identifier(
    identifier: str,
    *,
    fetch_by_code,
    fetch_by_customer_reference,
) -> ResolvedProductIdentifier | None:
    cleaned = ProductIdentifierResolutionService.normalize_identifier(identifier)

    if not cleaned:
        return None

    by_code = fetch_by_code(cleaned)
    by_reference = (
        None
        if ProductIdentifierResolutionService.looks_like_delpi_pa_code(cleaned)
        else fetch_by_customer_reference(cleaned)
    )

    return ProductIdentifierResolutionService.resolve(
        cleaned,
        by_code=by_code,
        by_customer_reference=by_reference,
    )
