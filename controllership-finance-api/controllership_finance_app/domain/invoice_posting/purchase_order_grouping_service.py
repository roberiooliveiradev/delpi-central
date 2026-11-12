"""Agrupa linhas SC7 abertas por pedido + data de entrega."""

from __future__ import annotations

from typing import Any


def _normalize_delivery_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    return raw or None


def _normalize_issue_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    return raw or None


def normalize_order_item(value: Any) -> str:
    return str(value or "").strip()


def aggregate_purchase_order_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Recalcula product_count / open_value / item_count a partir de um subset."""
    product_codes = {
        str(line.get("product_code") or "").strip()
        for line in items
        if str(line.get("product_code") or "").strip()
    }
    open_value = sum(float(line.get("open_value") or 0) for line in items)
    issue_dates = sorted(
        {
            d
            for d in (_normalize_issue_date(line.get("issue_date")) for line in items)
            if d
        }
    )
    return {
        "product_count": len(product_codes),
        "open_value": round(open_value, 2),
        "item_count": len(items),
        "issue_date": issue_dates[0] if issue_dates else None,
    }


def select_group_items_by_order_items(
    group: dict[str, Any],
    order_items: list[str] | None,
) -> list[dict[str, Any]]:
    """Filtra itens do grupo. Lista vazia/None = grupo inteiro."""
    items = list(group.get("items") or [])
    if not order_items:
        return items
    wanted = {
        normalize_order_item(raw)
        for raw in order_items
        if normalize_order_item(raw)
    }
    if not wanted:
        return items
    return [
        line
        for line in items
        if normalize_order_item(line.get("order_item")) in wanted
    ]


def linked_lines_from_items(items: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    """Snapshot leve das linhas vinculadas (order_item + product_code)."""
    out: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for line in items:
        order_item = normalize_order_item(line.get("order_item"))
        if not order_item or order_item in seen:
            continue
        seen.add(order_item)
        product = str(line.get("product_code") or "").strip() or None
        out.append({"order_item": order_item, "product_code": product})
    return out


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
        aggregates = aggregate_purchase_order_items(lines)
        groups.append(
            {
                "order_number": order_number,
                "delivery_date": delivery_date,
                "issue_date": aggregates["issue_date"],
                "product_count": aggregates["product_count"],
                "open_value": aggregates["open_value"],
                "item_count": aggregates["item_count"],
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


def linked_po_snapshot_from_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    number = str(row.get("order_number") or "").strip()
    if not number:
        return None
    raw_lines = row.get("lines")
    lines: list[dict[str, Any]] = []
    if isinstance(raw_lines, list):
        for line in raw_lines:
            order_item = normalize_order_item(
                line.get("order_item") if isinstance(line, dict) else line
            )
            if not order_item:
                continue
            product = None
            if isinstance(line, dict):
                product = str(line.get("product_code") or "").strip() or None
            lines.append({"order_item": order_item, "product_code": product})
    return {
        "order_number": number,
        "delivery_date": row.get("delivery_date"),
        "issue_date": row.get("issue_date"),
        "open_value": row.get("open_value"),
        "product_count": row.get("product_count"),
        "linked_at": row.get("linked_at"),
        "linked_by_user_id": row.get("linked_by_user_id"),
        "linked_by_name": row.get("linked_by_name"),
        "lines": lines,
    }


def linked_po_snapshots_from_rows(
    rows: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows or []:
        snap = linked_po_snapshot_from_row(row)
        if snap:
            out.append(snap)
    return out


def linked_po_snapshot_from_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Legado: primeiro vínculo da lista ou colunas singular V004."""
    linked_list = request.get("linked_purchase_orders")
    if isinstance(linked_list, list) and linked_list:
        return linked_po_snapshot_from_row(linked_list[0])
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
        "lines": [],
    }


def linked_po_snapshots_from_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    linked_list = request.get("linked_purchase_orders")
    if isinstance(linked_list, list):
        return linked_po_snapshots_from_rows(linked_list)
    single = linked_po_snapshot_from_request(request)
    return [single] if single else []


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


def format_linked_po_labels(snapshots: list[dict[str, Any]]) -> str:
    if not snapshots:
        return "(nenhum)"
    return ", ".join(
        format_linked_po_label(
            order_number=str(s.get("order_number") or ""),
            delivery_date=s.get("delivery_date"),
        )
        for s in snapshots
    )
