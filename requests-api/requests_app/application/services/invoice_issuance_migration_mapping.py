"""Pure mapping helpers for invoice_issuance → my_requests data migration (E8)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

LEGACY_STATUS_TO_CANONICAL: dict[str, str] = {
    "pending": "submitted",
    "in_progress": "in_progress",
    "returned": "needs_information",
    "issued": "completed",
    "cancelled": "cancelled",
}

LEGACY_EVENT_TO_ACTION: dict[str, str] = {
    "created": "created",
    "started": "start",
    "returned": "return",
    "issued": "complete",
    "resubmitted": "resubmit",
    "cancelled": "cancel",
    "updated": "edit",
}

PAYLOAD_REQUEST_KEYS = (
    "party_type",
    "party_code",
    "party_store",
    "party_name",
    "tax_id",
    "invoice_type",
    "invoice_type_other",
    "freight_mode",
    "carrier_code",
    "carrier_name",
    "carrier_legal_name",
    "carrier_tax_id",
    "carrier_address",
    "carrier_phone",
    "weight_kg",
    "volume_count",
    "purchase_order_number",
    "observation",
    "checklist",
)


def map_legacy_status(status: str | None) -> str:
    raw = str(status or "").strip().lower()
    if raw not in LEGACY_STATUS_TO_CANONICAL:
        raise ValueError(f"Status legado desconhecido: {status!r}")
    return LEGACY_STATUS_TO_CANONICAL[raw]


def map_legacy_event_action(event_type: str | None) -> str:
    raw = str(event_type or "").strip().lower()
    if raw not in LEGACY_EVENT_TO_ACTION:
        raise ValueError(f"event_type legado desconhecido: {event_type!r}")
    return LEGACY_EVENT_TO_ACTION[raw]


def map_optional_legacy_status(status: str | None) -> str | None:
    if status is None or str(status).strip() == "":
        return None
    return map_legacy_status(status)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_item_payload(item: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "product_code": str(item.get("product_code") or "").strip(),
        "product_description": str(item.get("product_description") or "").strip(),
        "quantity": _jsonable(item.get("quantity")),
        "unit_price": _jsonable(item.get("unit_price")),
        "stock_write_off": bool(item.get("stock_write_off")),
        "line_number": int(item.get("line_number") or 0),
    }
    sales_order = item.get("sales_order")
    sales_order_item = item.get("sales_order_item")
    if sales_order is not None and str(sales_order).strip():
        out["sales_order"] = str(sales_order).strip()
    if sales_order_item is not None and str(sales_order_item).strip():
        out["sales_order_item"] = str(sales_order_item).strip()
    customer_order = item.get("customer_order_number")
    if customer_order is not None and str(customer_order).strip():
        out["customer_order_number"] = str(customer_order).strip()
    return out


def build_payload(
    row: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    legacy_id: str,
    migrated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build my_requests.requests.payload from a legacy request row + items."""
    when = migrated_at or datetime.now(timezone.utc)
    payload: dict[str, Any] = {}
    for key in PAYLOAD_REQUEST_KEYS:
        if key not in row:
            continue
        value = row.get(key)
        if value is None:
            continue
        if key == "checklist" and value == {}:
            payload[key] = value
            continue
        if isinstance(value, str) and not value.strip() and key not in {"observation"}:
            continue
        payload[key] = _jsonable(value)

    ordered = sorted(items, key=lambda it: int(it.get("line_number") or 0))
    payload["items"] = [build_item_payload(item) for item in ordered]
    payload["_migration"] = {
        "source": "invoice_issuance",
        "legacy_id": str(legacy_id),
        "migrated_at": when.astimezone(timezone.utc).isoformat(),
    }
    return payload


def build_history_row(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "from_status": map_optional_legacy_status(entry.get("from_status")),
        "to_status": map_legacy_status(entry.get("to_status") or entry.get("from_status")),
        "action": map_legacy_event_action(entry.get("event_type")),
        "actor_user_id": str(entry.get("actor_user_id") or "system"),
        "actor_name": str(entry.get("actor_name") or "system"),
        "justification": entry.get("justification"),
        "changes": entry.get("changes") if isinstance(entry.get("changes"), dict) else {},
        "created_at": entry.get("created_at"),
    }


def should_create_assignment(row: dict[str, Any]) -> bool:
    status = map_legacy_status(row.get("status"))
    assignee = str(row.get("assignee_user_id") or "").strip()
    return status == "in_progress" and bool(assignee)
