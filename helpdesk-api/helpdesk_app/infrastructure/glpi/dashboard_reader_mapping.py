"""Map a legacy Ticket page onto the summary fields, dropping rows outside the allowlist."""

from __future__ import annotations

import re

_RANGE = re.compile(r"(\d+)-(\d+)/(\d+)")


def map_dashboard_reader_page(
    payload,
    *,
    content_range: str,
    entity_ids: tuple[int, ...],
    group_ids: tuple[int, ...],
    page_size: int,
) -> tuple[list[dict], bool]:
    rows = _rows(payload)
    allowed_entities = set(entity_ids)
    allowed_groups = set(group_ids)
    kept: list[dict] = []
    seen_ids: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        entity_id = _entity_id(row)
        if entity_id not in allowed_entities:
            continue
        if allowed_groups and not (_group_ids(row) & allowed_groups):
            continue
        ticket_id = row.get("id")
        if not isinstance(ticket_id, int) or ticket_id in seen_ids:
            continue
        seen_ids.add(ticket_id)
        kept.append(
            {
                "id": ticket_id,
                "title": _text(row.get("name")),
                "status": "",
                "category": _named(row.get("itilcategories_id")),
                "urgency": _named(row.get("urgency")),
                "updated_at": _text(row.get("date_mod")),
                "created_at": _text(row.get("date")),
                "status_id": row.get("status") if isinstance(row.get("status"), int) else None,
                "solved_at": _text(row.get("solvedate")),
                "closed_at": _text(row.get("closedate")),
                "sla_ttr": _text(row.get("time_to_resolve")),
                "sla_tto": _text(row.get("time_to_own")),
                "entity": _named(row.get("entities_id")) or str(entity_id),
            }
        )
    return kept, _has_more(content_range, raw_count=len(rows), page_size=page_size)


def _rows(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("id"), int):
        return [payload]
    return []


def _entity_id(row: dict) -> int | None:
    value = row.get("entities_id")
    if isinstance(value, int):
        return value
    if isinstance(value, dict) and isinstance(value.get("id"), int):
        return value["id"]
    return None


def _group_ids(row: dict) -> set[int]:
    found: set[int] = set()
    for key in ("groups_id", "groups_id_assign", "_groups_id_assign"):
        value = row.get(key)
        if isinstance(value, int):
            found.add(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, int):
                    found.add(item)
                elif isinstance(item, dict) and isinstance(item.get("id"), int):
                    found.add(item["id"])
    return found


def _named(value) -> str:
    if isinstance(value, dict):
        name = value.get("name")
        return name.strip() if isinstance(name, str) else ""
    return ""


def _text(value) -> str:
    if isinstance(value, str):
        return value
    return ""


def parse_sla_ttr_exceeded(payload, ticket_ids: tuple[int, ...]) -> dict[int, bool]:
    """Map GLPI search field 82 (sla_ttr_is_late) onto ticket ids. No deadline math."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return {}
    found: dict[int, bool] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        raw_id = row.get("2", row.get(2))
        try:
            ticket_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        flag = _glpi_bool(row.get("82", row.get(82)))
        if flag is not None and ticket_id in ticket_ids:
            found[ticket_id] = flag
    return found


def _glpi_bool(value) -> bool | None:
    if value is True or value in (1, "1"):
        return True
    if value is False or value in (0, "0"):
        return False
    return None


def _has_more(content_range: str, *, raw_count: int, page_size: int) -> bool:
    match = _RANGE.search(content_range or "")
    if match:
        end = int(match.group(2))
        total = int(match.group(3))
        return end + 1 < total
    return raw_count >= page_size
