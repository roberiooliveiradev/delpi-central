"""Agrupa linhas SC7 abertas por pedido + data de entrega."""

from __future__ import annotations

from typing import Any


def _normalize_delivery_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    return raw or None


def _normalize_issue_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    return raw or None


def group_open_purchase_order_lines(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Consolida itens abertos em grupos (order_number + delivery_date)."""
    buckets: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for raw in items:
        order_number = str(raw.get("order_number") or "").strip()
        if not order_number:
            continue
        delivery = _normalize_delivery_date(raw.get("expected_delivery_date"))
        key = (order_number, delivery)
        buckets.setdefault(key, []).append(raw)

    groups: list[dict[str, Any]] = []
    for (order_number, delivery_date), lines in buckets.items():
        product_codes = {
            str(line.get("product_code") or "").strip()
            for line in lines
            if str(line.get("product_code") or "").strip()
        }
        open_value = sum(float(line.get("open_value") or 0) for line in lines)
        issue_dates = sorted(
            {
                d
                for d in (_normalize_issue_date(line.get("issue_date")) for line in lines)
                if d
            }
        )
        groups.append(
            {
                "order_number": order_number,
                "delivery_date": delivery_date,
                "issue_date": issue_dates[0] if issue_dates else None,
                "product_count": len(product_codes),
                "open_value": round(open_value, 2),
                "item_count": len(lines),
                "items": lines,
            }
        )

    groups.sort(
        key=lambda g: (
            1 if not g.get("delivery_date") else 0,
            str(g.get("delivery_date") or ""),
            str(g.get("order_number") or ""),
        )
    )
    return groups


def find_purchase_order_group(
    groups: list[dict[str, Any]],
    *,
    order_number: str,
    delivery_date: str | None,
) -> dict[str, Any] | None:
    wanted_order = str(order_number or "").strip()
    wanted_delivery = _normalize_delivery_date(delivery_date)
    for group in groups:
        if str(group.get("order_number") or "").strip() != wanted_order:
            continue
        if _normalize_delivery_date(group.get("delivery_date")) != wanted_delivery:
            continue
        return group
    return None


def linked_po_snapshot_from_request(request: dict[str, Any]) -> dict[str, Any] | None:
    number = str(request.get("linked_po_number") or "").strip()
    if not number:
        return None
    return {
        "order_number": number,
        "delivery_date": request.get("linked_po_delivery_date"),
        "issue_date": request.get("linked_po_issue_date"),
        "open_value": request.get("linked_po_open_value"),
        "product_count": request.get("linked_po_product_count"),
        "linked_at": request.get("linked_po_linked_at"),
        "linked_by_user_id": request.get("linked_po_linked_by_user_id"),
        "linked_by_name": request.get("linked_po_linked_by_name"),
    }


def format_linked_po_label(
    *,
    order_number: str,
    delivery_date: str | None,
) -> str:
    number = str(order_number or "").strip() or "—"
    delivery = _normalize_delivery_date(delivery_date)
    if not delivery:
        return f"PC {number} · sem data de entrega"
    # ISO YYYY-MM-DD → DD/MM/YYYY quando possível
    if len(delivery) == 10 and delivery[4] == "-" and delivery[7] == "-":
        year, month, day = delivery.split("-")
        return f"PC {number} · entrega {day}/{month}/{year}"
    return f"PC {number} · entrega {delivery}"
