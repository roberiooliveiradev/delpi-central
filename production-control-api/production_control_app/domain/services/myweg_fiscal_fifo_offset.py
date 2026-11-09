"""Conciliação operacional provisória de NF Protheus com necessidades MyWEG.

Calculada integralmente a cada snapshot, sem persistir/alterar a coleta WEG.
O recibo fiscal não prova que a WEG reconheceu a baixa.
A alocação FIFO é feita por item fiscal único e produto DELPI confirmado;
o mesmo item não pode baixar duas linhas nem duas vezes a mesma coleta.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from production_control_app.domain.services.myweg_demand_projection import (
    MyWegDemandProjectionLine,
)

_ZERO = Decimal("0")
_THOUSAND = Decimal("1000")
_ONE = Decimal("1")
_TZ = ZoneInfo("America/Sao_Paulo")
_CUSTOMER = "000001"
_STORE = "09"
_BRANCH = "02"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(_text(value)[:10])
    except ValueError:
        return None


def _quantity(value: Any) -> Decimal | None:
    try:
        value_dec = Decimal(str(value))
        if value_dec.is_finite() and value_dec > _ZERO and value_dec % _ONE == _ZERO:
            return value_dec
    except (InvalidOperation, ValueError, TypeError):
        pass
    return None


def _batch_cutoff(batch: Mapping[str, Any]) -> tuple[date | None, bool]:
    """Mesmo dia: falta hora fiscal. Só presume emissão pós-coleta quando
    a coleta conhecida foi feita até 06:00 em São Paulo. Fora disso bloqueia
    abatimento automático para evitar reduzir necessidade já atualizada.
    """
    day = _date(batch.get("collection_date"))
    raw = _text(batch.get("collected_at"))
    try:
        instant = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            return day, False
        local = instant.astimezone(_TZ)
        return day or local.date(), bool(
            (day is None or local.date() == day) and local.hour < 6
        )
    except ValueError:
        return day, False


def reconcile_latest_myweg_fifo(
    projected: Sequence[MyWegDemandProjectionLine],
    fiscal_items: Sequence[Mapping[str, Any]],
    *,
    batch: Mapping[str, Any],
    today: date,
) -> dict[str, Any]:
    """FIFO operacional, somente leitura, independente da quantidade do PV.

    Retorna linhas copiadas (imutáveis na origem), alocações por record_id,
    e produtos cujo sinal de 'criar OP' é inconclusivo.
    """
    collection_day, early_snapshot = _batch_cutoff(batch)
    products = {
        line.product_code for line in projected if line.coverage_eligible and line.product_code
    }
    if collection_day is None or collection_day > today:
        return {
            "lines": list(projected),
            "allocations": {},
            "pending_products": products,
            "meta": {
                "status": "snapshot_date_unverified",
                "batch_id": _text(batch.get("id")),
                "collection_date": None if collection_day is None else collection_day.isoformat(),
                "applied_un": "0",
                "applied_item_count": 0,
                "pending_products": sorted(products),
            },
        }

    verified: dict[str, list[dict[str, Any]]] = {}
    invalid_products: set[str] = set()
    uncertain_products: set[str] = set()
    seen: dict[tuple[str, str, str, str], tuple[str, str]] = {}

    for row in fiscal_items:
        if not isinstance(row, Mapping):
            continue
        product = _text(row.get("product_code"))
        if product not in products:
            continue
        if (
            _text(row.get("branch")) != _BRANCH
            or _text(row.get("customer_code")) != _CUSTOMER
            or _text(row.get("customer_store")) != _STORE
        ):
            invalid_products.add(product)
            continue
        document = _text(row.get("invoice_number"))
        series = _text(row.get("invoice_series"))
        item = _text(row.get("item"))
        issued = _date(row.get("issue_date"))
        if not document or not series or not item or issued is None:
            invalid_products.add(product)
            continue
        if issued < collection_day or issued > today:
            continue
        fiscal_key = (_BRANCH, document, series, item)
        quantity_raw = _text(row.get("quantity_un"))
        if not row.get("comparable") or row.get("is_return") or _text(row.get("situation")) == "return":
            invalid_products.add(product)
            continue
        quantity_un = _quantity(quantity_raw)
        if quantity_un is None:
            invalid_products.add(product)
            continue
        identity = (product, quantity_raw)
        if fiscal_key in seen:
            if seen[fiscal_key] != identity:
                invalid_products.add(product)
                invalid_products.add(seen[fiscal_key][0])
            continue
        seen[fiscal_key] = identity

        if issued == collection_day and not early_snapshot:
            # D2_EMISSAO não tem horário de emissão: a mesma data da coleta
            # é ambígua para uma coleta tardia. Não abater silenciosamente.
            uncertain_products.add(product)
            continue
        verified.setdefault(product, []).append({
            "key": "|".join(fiscal_key),
            "date": issued.isoformat(),
            "document": document,
            "series": series,
            "item": item,
            "remaining_un": quantity_un,
        })

    pending_products = invalid_products | uncertain_products
    allocations: dict[str, dict[str, Any]] = {}
    adjusted: dict[str, MyWegDemandProjectionLine] = {}
    applied_total = _ZERO
    applied_item_keys: set[str] = set()
    product_report: list[dict[str, Any]] = []

    for product in sorted(verified):
        if product in pending_products:
            continue
        events = sorted(
            verified[product],
            key=lambda event: (event["date"], event["document"], event["series"], event["item"]),
        )
        demands = sorted(
            (
                line for line in projected
                if line.coverage_eligible and line.product_code == product
            ),
            key=lambda line: (line.due_date, line.record_id),
        )
        credited = _ZERO
        for line in demands:
            available = line.open_quantity
            refs: list[dict[str, str]] = []
            for event in events:
                if available <= _ZERO:
                    break
                qty = min(available, event["remaining_un"])
                if qty <= _ZERO:
                    continue
                event["remaining_un"] -= qty
                available -= qty
                credited += qty
                applied_total += qty
                applied_item_keys.add(event["key"])
                refs.append({
                    "fiscal_key": event["key"],
                    "invoice": event["document"],
                    "series": event["series"],
                    "item": event["item"],
                    "quantity_un": str(qty),
                })
            applied = line.open_quantity - available
            if applied > _ZERO:
                adjusted[line.record_id] = replace(
                    line,
                    open_quantity=available,
                    quantity_mi=available / _THOUSAND,
                )
                allocations[line.record_id] = {
                    "raw_quantity_un": str(line.open_quantity),
                    "applied_quantity_un": str(applied),
                    "effective_quantity_un": str(available),
                    "status": "provisional_invoice_offset",
                    "invoices": refs,
                }
        product_report.append({
            "product_code": product,
            "applied_un": str(credited),
            "unapplied_fiscal_un": str(sum(
                (event["remaining_un"] for event in events), _ZERO
            )),
            "invoice_count": len(events),
        })

    result_lines = [
        adjusted.get(line.record_id, line) for line in projected
    ]
    return {
        "lines": result_lines,
        "allocations": allocations,
        "pending_products": pending_products,
        "meta": {
            "status": (
                "partial" if pending_products else
                "provisional" if applied_total > _ZERO else "no_recent_invoices"
            ),
            "policy": "provisional_invoice_offset_fifo_oldest_due_date",
            "recognition_status": "weg_acknowledgment_not_proven",
            "batch_id": _text(batch.get("id")),
            "collection_date": collection_day.isoformat(),
            "same_day_early_snapshot": early_snapshot,
            "applied_un": str(applied_total),
            "applied_item_count": len(applied_item_keys),
            "adjusted_record_count": len(allocations),
            "pending_products": sorted(pending_products),
            "products": product_report,
        },
    }
