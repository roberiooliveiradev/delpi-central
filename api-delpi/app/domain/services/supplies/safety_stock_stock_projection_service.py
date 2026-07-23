"""Projeção cronológica de saldo: físico + pedidos SC7 − empenhos SD4."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.services.supplies.safety_stock_classification_service import (
    AVAILABLE_BALANCE_WAREHOUSES,
    TOLERANCE,
)
from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    is_coverage_eligible_warehouse,
)
from app.domain.services.supplies.safety_stock_unit_conversion_service import (
    convert_quantity_to_primary_unit,
)

ORIGIN_INITIAL = "initial_balance"
ORIGIN_COMMITMENT = "commitment"
ORIGIN_PURCHASE = "purchase_order"

DATE_STATUS_TODAY = "today"
DATE_STATUS_SCHEDULED = "scheduled"
DATE_STATUS_OVERDUE = "overdue"
DATE_STATUS_UNSCHEDULED = "unscheduled"

PROJECTION_SUFFICIENT = "sufficient"
PROJECTION_TEMPORARY_SHORTAGE = "temporary_shortage"
PROJECTION_DEFICIT = "projected_deficit"

FINISHED_PRODUCTION_ORDER_SUFFIX = "01001"


def finished_production_order_from_component_op(production_order: str) -> str | None:
    """OP do produto acabado: 6 primeiros caracteres da OP do empenho + 01001."""
    op = str(production_order or "").strip()
    if len(op) < 6:
        return None
    return f"{op[:6]}{FINISHED_PRODUCTION_ORDER_SUFFIX}"


def format_commitment_ledger_reference(
    *,
    production_order: str,
    finished_product_code: str | None = None,
) -> str:
    """Referência do extrato: apenas a OP do empenho (PA fica em coluna própria)."""
    del finished_product_code  # mantido na assinatura por compatibilidade de chamada
    op = str(production_order or "").strip()
    return op or "Empenho"


_ORIGIN_SORT = {
    ORIGIN_INITIAL: 0,
    ORIGIN_COMMITMENT: 1,
    ORIGIN_PURCHASE: 2,
}


def _parse_iso_date(value: str | None) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 8 and raw.isdigit():
            return date(int(raw[0:4]), int(raw[4:6]), int(raw[6:8]))
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _today() -> date:
    return datetime.now().date()


def enrich_open_commitments(
    *,
    commitments: list[dict[str, Any]],
    primary_unit: str | None,
    secondary_unit: str | None,
    conversion_factor: float | int | str | None,
    conversion_type: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normaliza empenhos e soma saldo elegível (armazéns 01/98/99 + UM compatível)."""
    enriched: list[dict[str, Any]] = []
    eligible_total = 0.0
    incompatible_count = 0
    next_commitment_date: str | None = None
    warnings: list[str] = []
    today = _today()

    for raw in commitments:
        warehouse = str(raw.get("warehouse") or "").strip()
        unit = str(raw.get("unit") or "").strip()
        open_qty = float(raw.get("open_quantity") or 0)
        conversion = convert_quantity_to_primary_unit(
            quantity=open_qty,
            source_unit=unit,
            primary_unit=primary_unit,
            secondary_unit=secondary_unit,
            conversion_factor=conversion_factor,
            conversion_type=conversion_type,
        )
        warehouse_eligible = is_coverage_eligible_warehouse(warehouse)
        converted = conversion.quantity if conversion.compatible else None
        projection_eligible = bool(
            warehouse_eligible and conversion.compatible and (converted or 0) > TOLERANCE
        )

        if conversion.compatible and converted is not None and warehouse_eligible:
            eligible_total += converted
        elif not conversion.compatible:
            incompatible_count += 1

        commitment_date = str(raw.get("commitment_date") or "").strip() or None
        parsed = _parse_iso_date(commitment_date)
        if parsed is None:
            date_status = DATE_STATUS_UNSCHEDULED
            iso_date = None
        else:
            iso_date = parsed.isoformat()
            date_status = DATE_STATUS_OVERDUE if parsed < today else DATE_STATUS_SCHEDULED
            if projection_eligible and (
                next_commitment_date is None or iso_date < next_commitment_date
            ):
                next_commitment_date = iso_date

        enriched.append(
            {
                **raw,
                "warehouse": warehouse,
                "unit": unit,
                "open_quantity": open_qty,
                "open_quantity_primary_unit": converted,
                "unit_compatible": conversion.compatible,
                "unit_conversion_reason": conversion.reason,
                "warehouse_eligible": warehouse_eligible,
                "projection_eligible": projection_eligible,
                "commitment_date": iso_date,
                "date_status": date_status,
                "date_semantics": "production_order_start_date",
            }
        )

    if incompatible_count:
        warnings.append(
            "Alguns empenhos usam unidade incompatível com o cadastro do produto "
            "e não entram na projeção de saldo."
        )

    return enriched, {
        "eligible_open_quantity": eligible_total,
        "next_commitment_date": next_commitment_date,
        "incompatible_unit_commitment_count": incompatible_count,
        "eligible_warehouses": list(AVAILABLE_BALANCE_WAREHOUSES),
        "warnings": warnings,
    }


def _event_sort_key(event: dict[str, Any]) -> tuple:
    """Ordem: saldo inicial → vencidos → futuros → sem data; saídas antes de entradas."""
    raw_bucket = event.get("_bucket")
    bucket = 9 if raw_bucket is None else int(raw_bucket)
    sort_date = str(event.get("_sort_date") or "9999-99-99")
    movement = float(event.get("movement") or 0)
    # Saídas (negativo) antes de entradas (positivo) no mesmo dia.
    movement_rank = 0 if movement < 0 else 1 if movement > 0 else 2
    origin_rank = _ORIGIN_SORT.get(str(event.get("origin") or ""), 9)
    reference = str(event.get("reference") or "")
    return (bucket, sort_date, movement_rank, origin_rank, reference)


def build_stock_projection(
    *,
    available_stock: float,
    safety_stock: float,
    enriched_orders: list[dict[str, Any]],
    enriched_commitments: list[dict[str, Any]],
    commitment_totals: dict[str, Any] | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """Monta extrato cronológico consolidado (01+98+99) e métricas de projeção."""
    today = as_of_date or _today()
    today_iso = today.isoformat()
    initial = float(available_stock or 0)
    estseg = max(float(safety_stock or 0), 0.0)
    warnings: list[str] = list((commitment_totals or {}).get("warnings") or [])

    events: list[dict[str, Any]] = [
        {
            "event_date": today_iso,
            "date_status": DATE_STATUS_TODAY,
            "date_semantics": "as_of_today",
            "origin": ORIGIN_INITIAL,
            "origin_label": "Saldo inicial",
            "reference": "Saldo disponível (01+98+99)",
            "warehouse": "",
            "movement": initial,
            # Saldo inicial não é movimento: aparece só na coluna de saldo.
            "inflow": 0.0,
            "outflow": 0.0,
            "unit_compatible": True,
            "projection_eligible": True,
            "_bucket": 0,
            "_sort_date": today_iso,
        }
    ]

    for order in enriched_orders:
        if not order.get("coverage_eligible"):
            continue
        qty = float(order.get("open_quantity_primary_unit") or 0)
        if qty <= TOLERANCE:
            continue
        raw_date = order.get("expected_delivery_date")
        parsed = _parse_iso_date(str(raw_date) if raw_date else None)
        if parsed is None:
            bucket = 3
            sort_date = "9999-99-99"
            iso_date = None
            date_status = DATE_STATUS_UNSCHEDULED
        elif parsed < today:
            bucket = 1
            sort_date = parsed.isoformat()
            iso_date = parsed.isoformat()
            date_status = DATE_STATUS_OVERDUE
        else:
            bucket = 2
            sort_date = parsed.isoformat()
            iso_date = parsed.isoformat()
            date_status = DATE_STATUS_SCHEDULED

        order_number = str(order.get("order_number") or "").strip()
        order_item = str(order.get("order_item") or "").strip()
        supplier = str(order.get("supplier_name") or "").strip()
        reference = f"{order_number}/{order_item}".strip("/")
        if supplier:
            reference = f"{reference} - {supplier}" if reference else supplier
        events.append(
            {
                "event_date": iso_date,
                "date_status": date_status,
                "date_semantics": "expected_delivery_date",
                "origin": ORIGIN_PURCHASE,
                "origin_label": "Pedido de compra",
                "reference": reference or order_number or "Pedido",
                "warehouse": str(order.get("warehouse") or "").strip(),
                "movement": qty,
                "inflow": qty,
                "outflow": 0.0,
                "unit_compatible": bool(order.get("unit_compatible")),
                "projection_eligible": True,
                "_bucket": bucket,
                "_sort_date": sort_date,
            }
        )

    for commitment in enriched_commitments:
        if not commitment.get("projection_eligible"):
            continue
        qty = float(commitment.get("open_quantity_primary_unit") or 0)
        if qty <= TOLERANCE:
            continue
        raw_date = commitment.get("commitment_date")
        parsed = _parse_iso_date(str(raw_date) if raw_date else None)
        if parsed is None:
            bucket = 3
            sort_date = "9999-99-99"
            iso_date = None
            date_status = DATE_STATUS_UNSCHEDULED
        elif parsed < today:
            bucket = 1
            sort_date = parsed.isoformat()
            iso_date = parsed.isoformat()
            date_status = DATE_STATUS_OVERDUE
        else:
            bucket = 2
            sort_date = parsed.isoformat()
            iso_date = parsed.isoformat()
            date_status = DATE_STATUS_SCHEDULED

        op = str(commitment.get("production_order") or "").strip()
        finished_code = str(commitment.get("finished_product_code") or "").strip()
        finished_op = str(commitment.get("finished_production_order") or "").strip()
        if not finished_op:
            finished_op = finished_production_order_from_component_op(op) or ""
        events.append(
            {
                "event_date": iso_date,
                "date_status": date_status,
                "date_semantics": "production_order_start_date",
                "origin": ORIGIN_COMMITMENT,
                "origin_label": "Empenho",
                "reference": format_commitment_ledger_reference(
                    production_order=op,
                    finished_product_code=finished_code,
                ),
                "finished_production_order": finished_op,
                "finished_product_code": finished_code,
                "finished_order_observation": str(
                    commitment.get("finished_order_observation") or ""
                ).strip(),
                "warehouse": str(commitment.get("warehouse") or "").strip(),
                "movement": -qty,
                "inflow": 0.0,
                "outflow": qty,
                "unit_compatible": bool(commitment.get("unit_compatible")),
                "projection_eligible": True,
                "_bucket": bucket,
                "_sort_date": sort_date,
            }
        )

    events.sort(key=_event_sort_key)

    timeline: list[dict[str, Any]] = []
    running = 0.0
    minimum = initial
    first_shortage_date: str | None = None
    purchase_total = 0.0
    commitment_total = 0.0

    for index, event in enumerate(events):
        movement = float(event["movement"])
        if event["origin"] == ORIGIN_INITIAL:
            running = movement
        else:
            running += movement
            if event["origin"] == ORIGIN_PURCHASE:
                purchase_total += movement
            elif event["origin"] == ORIGIN_COMMITMENT:
                commitment_total += abs(movement)

        if running < minimum:
            minimum = running

        # Ruptura = primeiro saldo projetado negativo (sem descontar ESTSEG).
        if first_shortage_date is None and running + TOLERANCE < 0:
            first_shortage_date = event.get("event_date") or today_iso

        row = {
            "sequence": index + 1,
            "event_date": event.get("event_date"),
            "date_status": event["date_status"],
            "date_semantics": event["date_semantics"],
            "origin": event["origin"],
            "origin_label": event["origin_label"],
            "reference": event["reference"],
            "finished_production_order": str(
                event.get("finished_production_order") or ""
            ).strip()
            or None,
            "finished_product_code": str(
                event.get("finished_product_code") or ""
            ).strip()
            or None,
            "finished_order_observation": str(
                event.get("finished_order_observation") or ""
            ).strip()
            or None,
            "warehouse": event.get("warehouse") or "",
            "movement": movement,
            "inflow": float(event.get("inflow") or 0),
            "outflow": float(event.get("outflow") or 0),
            "running_balance": running,
            "unit_compatible": bool(event.get("unit_compatible")),
            "projection_eligible": bool(event.get("projection_eligible")),
        }
        timeline.append(row)

    final_balance = running
    final_after_safety = final_balance - estseg
    remaining = max(estseg - final_balance, 0.0) if estseg > TOLERANCE else 0.0

    if estseg <= TOLERANCE:
        status = PROJECTION_SUFFICIENT
    elif final_balance + TOLERANCE < estseg:
        status = PROJECTION_DEFICIT
    elif minimum + TOLERANCE < estseg:
        status = PROJECTION_TEMPORARY_SHORTAGE
    else:
        status = PROJECTION_SUFFICIENT

    if any(row.get("date_status") == DATE_STATUS_UNSCHEDULED for row in timeline[1:]):
        warnings.append(
            "Há movimentos sem data válida; eles aparecem no fim do extrato e "
            "não possuem previsão confiável."
        )

    summary = {
        "as_of_date": today_iso,
        "initial_balance": initial,
        "safety_stock": estseg,
        "eligible_purchase_quantity": purchase_total,
        "eligible_commitment_quantity": commitment_total,
        "final_projected_balance": final_balance,
        "final_balance_after_safety": final_after_safety,
        "minimum_projected_balance": minimum,
        "first_shortage_date": first_shortage_date,
        "projected_remaining_to_buy": remaining,
        "status": status,
        "eligible_warehouses": list(AVAILABLE_BALANCE_WAREHOUSES),
        "warnings": warnings,
    }

    return {
        "items": timeline,
        "total": len(timeline),
        "summary": summary,
    }


def build_collection_block(
    items: list[dict[str, Any]],
    *,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        "items": items,
        "total": len(items),
    }
    if summary is not None:
        block["summary"] = summary
    return block
