"""Pegging de ruptura de MP no conjunto — reusa o extrato cronológico."""

from __future__ import annotations

from typing import Any

from app.domain.services.supplies.safety_stock_classification_service import TOLERANCE
from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    enrich_open_purchase_orders,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    ORIGIN_COMMITMENT,
    build_stock_projection,
    enrich_open_commitments,
)

STATUS_SHORTAGE = "shortage"
STATUS_OK = "ok"
STATUS_NO_COMMITMENT = "no_commitment"

_SET_STATUS_RANK = {
    STATUS_SHORTAGE: 0,
    STATUS_NO_COMMITMENT: 1,
    STATUS_OK: 2,
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _group_by_product(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        code = _text(row.get("product_code"))
        if not code:
            continue
        grouped.setdefault(code, []).append(row)
    return grouped


def _first_shortage_for_set(
    timeline: list[dict[str, Any]],
    *,
    mother_order: str,
) -> dict[str, Any] | None:
    for row in timeline:
        if _text(row.get("origin")) != ORIGIN_COMMITMENT:
            continue
        if _text(row.get("finished_production_order")) != mother_order:
            continue
        running = float(row.get("running_balance") or 0)
        if running + TOLERANCE < 0:
            return row
    return None


def _has_commitment_for_set(timeline: list[dict[str, Any]], *, mother_order: str) -> bool:
    return any(
        _text(row.get("origin")) == ORIGIN_COMMITMENT
        and _text(row.get("finished_production_order")) == mother_order
        for row in timeline
    )


def _commitment_need_for_set(
    timeline: list[dict[str, Any]], *, mother_order: str
) -> tuple[float, str]:
    quantity = 0.0
    consuming = ""
    for row in timeline:
        if _text(row.get("origin")) != ORIGIN_COMMITMENT:
            continue
        if _text(row.get("finished_production_order")) != mother_order:
            continue
        quantity += float(row.get("outflow") or 0)
        if not consuming:
            consuming = _text(row.get("reference"))
    return quantity, consuming


def _set_status(material_statuses: list[str]) -> str:
    if any(status == STATUS_SHORTAGE for status in material_statuses):
        return STATUS_SHORTAGE
    if material_statuses and all(
        status == STATUS_NO_COMMITMENT for status in material_statuses
    ):
        return STATUS_NO_COMMITMENT
    if not material_statuses:
        return STATUS_NO_COMMITMENT
    return STATUS_OK


def _sort_sets(sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        sets,
        key=lambda item: (
            _SET_STATUS_RANK.get(_text(item.get("status")), 9),
            _text(item.get("planned_start_date")) or "9999-99-99",
            _text(item.get("production_order")),
        ),
    )


def build_raw_material_set_shortages(
    *,
    product: dict[str, Any],
    materials: list[dict[str, Any]],
    mother_orders: list[dict[str, Any]],
    purchase_orders: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta conjuntos do PA com semáforo por MP a partir do extrato."""
    orders_by_mp = _group_by_product(purchase_orders)
    commitments_by_mp = _group_by_product(commitments)
    projections: dict[str, dict[str, Any]] = {}
    material_payload: list[dict[str, Any]] = []

    for material in materials:
        code = _text(material.get("product_code"))
        if not code:
            continue
        unit_kwargs = {
            "primary_unit": material.get("unit"),
            "secondary_unit": material.get("secondary_unit"),
            "conversion_factor": material.get("conversion_factor"),
            "conversion_type": material.get("conversion_type"),
        }
        enriched_orders, _ = enrich_open_purchase_orders(
            orders=orders_by_mp.get(code, []),
            **unit_kwargs,
        )
        enriched_commitments, commitment_totals = enrich_open_commitments(
            commitments=commitments_by_mp.get(code, []),
            **unit_kwargs,
        )
        projection = build_stock_projection(
            available_stock=float(material.get("available_stock") or 0),
            safety_stock=float(material.get("safety_stock") or 0),
            enriched_orders=enriched_orders,
            enriched_commitments=enriched_commitments,
            commitment_totals=commitment_totals,
        )
        projections[code] = projection
        summary = projection.get("summary") or {}
        material_payload.append(
            {
                **material,
                "projection_status": summary.get("status"),
                "final_projected_balance": summary.get("final_projected_balance"),
                "first_shortage_date": summary.get("first_shortage_date"),
                "ledger": projection.get("items") or [],
            }
        )

    sets: list[dict[str, Any]] = []
    short_mps: set[str] = set()
    first_shortage_date: str | None = None

    for order in mother_orders:
        mother_order = _text(order.get("production_order"))
        set_materials: list[dict[str, Any]] = []
        for material in material_payload:
            code = _text(material.get("product_code"))
            timeline = material.get("ledger") or []
            shortage_row = _first_shortage_for_set(
                timeline, mother_order=mother_order
            )
            needed_quantity, consuming_from_need = _commitment_need_for_set(
                timeline, mother_order=mother_order
            )
            if needed_quantity <= 0:
                needed_quantity = float(material.get("structure_quantity") or 0) * float(
                    order.get("open_quantity") or 0
                )
            if shortage_row is not None:
                status = STATUS_SHORTAGE
                event_date = _text(shortage_row.get("event_date")) or None
                shortage_quantity = max(
                    0.0, -float(shortage_row.get("running_balance") or 0)
                )
                consuming_op = _text(shortage_row.get("reference")) or consuming_from_need
                short_mps.add(code)
                if event_date and (
                    first_shortage_date is None or event_date < first_shortage_date
                ):
                    first_shortage_date = event_date
            elif _has_commitment_for_set(timeline, mother_order=mother_order):
                status = STATUS_OK
                event_date = None
                shortage_quantity = 0.0
                consuming_op = consuming_from_need
            else:
                status = STATUS_NO_COMMITMENT
                event_date = None
                shortage_quantity = 0.0
                consuming_op = ""
            set_materials.append(
                {
                    "product_code": code,
                    "product_description": _text(material.get("product_description")),
                    "unit": _text(material.get("unit")),
                    "status": status,
                    "shortage_date": event_date,
                    "shortage_quantity": shortage_quantity,
                    "needed_quantity": needed_quantity,
                    "consuming_production_order": consuming_op,
                    "available_stock": float(material.get("available_stock") or 0),
                    "safety_stock": float(material.get("safety_stock") or 0),
                    "structure_quantity": float(
                        material.get("structure_quantity") or 0
                    ),
                }
            )
        status = _set_status([item["status"] for item in set_materials])
        sets.append(
            {
                **order,
                "status": status,
                "materials": set_materials,
                "short_material_count": sum(
                    1 for item in set_materials if item["status"] == STATUS_SHORTAGE
                ),
            }
        )

    ordered = _sort_sets(sets)
    return {
        "product": product,
        "materials": material_payload,
        "sets": ordered,
        "summary": {
            "open_set_count": len(ordered),
            "at_risk_set_count": sum(
                1 for item in ordered if item["status"] == STATUS_SHORTAGE
            ),
            "short_mp_count": len(short_mps),
            "first_shortage_date": first_shortage_date,
            "ok_set_count": sum(1 for item in ordered if item["status"] == STATUS_OK),
            "no_commitment_set_count": sum(
                1 for item in ordered if item["status"] == STATUS_NO_COMMITMENT
            ),
        },
    }
