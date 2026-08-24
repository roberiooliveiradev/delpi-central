"""Agrupamento por data prevista — bloco hoje+atrasadas e demais dias."""

from __future__ import annotations

from datetime import date
from typing import Any

from production_control_app.application.services.delivery_map_settings import (
    delivery_map_setting_str,
)


def _parse_iso_date(value: str | None) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _format_section_label(section_key: str, due_date: date | None, *, today: date) -> str:
    if section_key == delivery_map_setting_str("overdueSectionKey", "overdue_and_today"):
        return delivery_map_setting_str("overdueSectionLabel", "Hoje + atrasadas")
    if due_date is None:
        return "Sem data prevista"
    return due_date.strftime("%d/%m/%Y")


def build_delivery_map_row(
    order: dict[str, Any],
    override: dict[str, Any] | None,
) -> dict[str, Any]:
    produced_qty = float(order.get("produced_qty") or 0)
    ovr = override if isinstance(override, dict) else {}
    return {
        "production_order": order.get("production_order"),
        "product_code": order.get("product_code"),
        "product_description": order.get("product_description"),
        "due_date": order.get("due_date"),
        "planned_qty": order.get("planned_qty"),
        "produced_qty": order.get("produced_qty"),
        "pending_qty": order.get("pending_qty"),
        "observation": order.get("observation"),
        "days_late": order.get("days_late"),
        "is_delayed": order.get("is_delayed"),
        "mp_ok": bool(ovr.get("mp_ok")),
        "work_center": str(ovr.get("work_center") or "").strip(),
        "is_reported": produced_qty > 0,
    }


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("due_date") or "9999-99-99"),
        str(row.get("production_order") or ""),
    )


def group_delivery_map_sections(
    orders: list[dict[str, Any]],
    overrides: dict[str, dict[str, Any]],
    *,
    today: date,
    search: str = "",
) -> list[dict[str, Any]]:
    needle = search.strip().casefold()
    rows: list[dict[str, Any]] = []
    for order in orders:
        if not isinstance(order, dict):
            continue
        production_order = str(order.get("production_order") or "").strip()
        row = build_delivery_map_row(order, overrides.get(production_order))
        if needle:
            haystack = " ".join(
                filter(
                    None,
                    [
                        production_order,
                        str(row.get("product_code") or ""),
                        str(row.get("product_description") or ""),
                        str(row.get("observation") or ""),
                        str(row.get("work_center") or ""),
                    ],
                )
            ).casefold()
            if needle not in haystack:
                continue
        rows.append(row)

    rows.sort(key=_row_sort_key)

    overdue_key = delivery_map_setting_str("overdueSectionKey", "overdue_and_today")
    buckets: dict[str, list[dict[str, Any]]] = {}
    bucket_dates: dict[str, date | None] = {}

    for row in rows:
        due = _parse_iso_date(str(row.get("due_date") or ""))
        if due is not None and due <= today:
            key = overdue_key
            bucket_dates[key] = None
        elif due is not None:
            key = due.isoformat()
            bucket_dates[key] = due
        else:
            key = "no_due_date"
            bucket_dates[key] = None
        buckets.setdefault(key, []).append(row)

    def section_order(key: str) -> tuple[int, str]:
        if key == overdue_key:
            return (0, "")
        if key == "no_due_date":
            return (2, key)
        return (1, key)

    sections: list[dict[str, Any]] = []
    for key in sorted(buckets.keys(), key=section_order):
        section_rows = buckets[key]
        due = bucket_dates.get(key)
        sections.append(
            {
                "section_key": key,
                "label": _format_section_label(key, due, today=today),
                "due_date": due.isoformat() if due else None,
                "row_count": len(section_rows),
                "rows": section_rows,
            }
        )
    return sections
