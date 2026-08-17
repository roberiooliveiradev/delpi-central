"""Checklist de conferência — derivado dos dados já coletados, não marcado pelo usuário."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.services.invoice_issuance.constants import (
    CHECKLIST_KEYS,
    FREIGHT_MODES,
    INVOICE_TYPES,
)


def _as_decimal(raw: Any) -> Decimal | None:
    text = str(raw if raw is not None else "").strip()
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError):
        return None


def build_review_checklist(
    *,
    party_code: str | None,
    party_store: str | None,
    items: list[dict[str, Any]] | None,
    invoice_type: str | None,
    invoice_type_other: str | None,
    freight_mode: str | None,
    weight_kg: Any,
    volume_count: Any,
) -> dict[str, bool]:
    rows = items if isinstance(items, list) else []
    codes_ok = bool(rows) and all(str(row.get("product_code") or "").strip() for row in rows)
    qty_price_ok = False
    if rows:
        qty_price_ok = True
        for row in rows:
            quantity = _as_decimal(row.get("quantity"))
            unit_price = _as_decimal(row.get("unit_price"))
            if quantity is None or quantity <= 0 or unit_price is None or unit_price < 0:
                qty_price_ok = False
                break
    invoice = str(invoice_type or "").strip()
    other = str(invoice_type_other or "").strip()
    invoice_ok = invoice in INVOICE_TYPES and (invoice != "other" or bool(other))
    weight = _as_decimal(weight_kg)
    try:
        volumes = int(volume_count)
    except (TypeError, ValueError):
        volumes = 0
    flags = {
        "recipient": bool(str(party_code or "").strip() and str(party_store or "").strip()),
        "item_codes": codes_ok,
        "quantity_price": qty_price_ok,
        "stock_write_off": bool(rows),
        "invoice_type": invoice_ok,
        "freight_mode": str(freight_mode or "").strip() in FREIGHT_MODES,
        "weight_volumes": bool(weight is not None and weight > 0 and volumes > 0),
    }
    return {key: bool(flags[key]) for key in CHECKLIST_KEYS}
