"""Legacy apirest search/Ticket — exceção estreita para atores (técnico).

HLAPI RSQL não filtra/ordena `team` (G-06/G-26). Quando a listagem precisa de
`assignee_id` ou `sort=assigned`, o BFF usa Search clássico (mesma sessão
`GLPI_LEGACY_*` de H12/H10) só para descobrir ids; a hidratação e o ACL
continuam no Bearer OAuth via HLAPI `id=in=(…)`.

Não é caminho geral da listagem: sem assignee/sort-assigned → HLAPI puro.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

from helpdesk_app.domain.errors import GlpiValidation
from helpdesk_app.domain.models import TicketListQuery

# Field ids — GLPI 10/11 Ticket search options (override via env if drift).
_FIELD_ID = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_ID_FIELD", "2") or "2")
_FIELD_NAME = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_NAME_FIELD", "1") or "1")
_FIELD_STATUS = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_STATUS_FIELD", "5") or "5")
_FIELD_CATEGORY = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_CATEGORY_FIELD", "7") or "7")
_FIELD_URGENCY = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_URGENCY_FIELD", "10") or "10")
_FIELD_ASSIGN = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_ASSIGN_FIELD", "12") or "12")
_FIELD_DATE_OPEN = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_DATE_OPEN_FIELD", "15") or "15")
_FIELD_DATE_MOD = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_DATE_MOD_FIELD", "19") or "19")
_FIELD_DATE_SOLVE = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_DATE_SOLVE_FIELD", "17") or "17")
_FIELD_DATE_CLOSE = int(os.getenv("GLPI_LEGACY_TICKET_SEARCH_DATE_CLOSE_FIELD", "16") or "16")

_STATUS_GROUPS: dict[str, tuple[int, ...]] = {
    "open": (1, 10, 2, 3, 4),
    "in_progress": (2, 3),
    "pending": (4,),
    "approval": (10,),
    "solved": (5,),
    "closed": (6,),
}


@dataclass(frozen=True)
class LegacyTicketSearchResult:
    ticket_ids: tuple[int, ...]
    totalcount: int
    has_more: bool


def ticket_list_needs_legacy_actor_search(query: TicketListQuery) -> bool:
    if query.assignee_id is not None:
        return True
    primary = (query.client_sort or "updated_at:desc").split(",")[0].strip()
    field = primary.split(":", 1)[0].strip()
    return field == "assigned"


def build_legacy_ticket_search_path_from_parts(
    *,
    q: str = "",
    status: str = "",
    urgency_id: int | None = None,
    category_id: int | None = None,
    updated_from: str = "",
    updated_to: str = "",
    created_from: str = "",
    created_to: str = "",
    assignee_id: int | None = None,
    sort: str = "updated_at:desc",
    page: int = 1,
    page_size: int = 20,
) -> str:
    criteria: list[dict[str, str | int]] = []

    def add(field: int, searchtype: str, value: str | int, *, link: str = "AND") -> None:
        entry: dict[str, str | int] = {
            "field": int(field),
            "searchtype": searchtype,
            "value": value,
        }
        if criteria:
            entry["link"] = link
        criteria.append(entry)

    if assignee_id is not None:
        if int(assignee_id) < 1:
            raise GlpiValidation("assignee_id inválido.")
        add(_FIELD_ASSIGN, "equals", int(assignee_id))

    term = _clean_term(q)
    if term:
        add(_FIELD_NAME, "contains", term)

    status_ids = _status_ids(status)
    if len(status_ids) == 1:
        add(_FIELD_STATUS, "equals", status_ids[0])
    elif len(status_ids) > 1:
        for index, status_id in enumerate(status_ids):
            add(_FIELD_STATUS, "equals", int(status_id), link=("AND" if index == 0 else "OR"))

    if urgency_id is not None:
        add(_FIELD_URGENCY, "equals", int(urgency_id))
    if category_id is not None:
        add(_FIELD_CATEGORY, "equals", int(category_id))

    if created_from.strip():
        add(_FIELD_DATE_OPEN, "morethan", f"{created_from.strip()} 00:00:00")
    if created_to.strip():
        add(_FIELD_DATE_OPEN, "lessthan", f"{created_to.strip()} 23:59:59")
    if updated_from.strip():
        add(_FIELD_DATE_MOD, "morethan", f"{updated_from.strip()} 00:00:00")
    if updated_to.strip():
        add(_FIELD_DATE_MOD, "lessthan", f"{updated_to.strip()} 23:59:59")

    if not criteria:
        add(_FIELD_ID, "contains", "")

    safe_page = max(1, int(page))
    safe_size = max(1, min(50, int(page_size)))
    start = (safe_page - 1) * safe_size
    # Inclusive range with +1 row to detect has_more.
    end = start + safe_size

    sort_field, sort_order = _legacy_sort(sort)

    params: list[tuple[str, str]] = []
    for index, criterion in enumerate(criteria):
        for key, value in criterion.items():
            params.append((f"criteria[{index}][{key}]", str(value)))
    params.append(("forcedisplay[0]", str(_FIELD_ID)))
    params.append(("range", f"{start}-{end}"))
    params.append(("sort", str(sort_field)))
    params.append(("order", sort_order))

    return f"/apirest.php/search/Ticket?{urlencode(params)}"


def parse_legacy_ticket_search(
    payload: dict | list,
    *,
    page: int,
    page_size: int,
) -> LegacyTicketSearchResult:
    rows: list = []
    total = 0
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            rows = data
        total_raw = payload.get("totalcount", payload.get("count", 0))
        try:
            total = int(total_raw or 0)
        except (TypeError, ValueError):
            total = 0
    elif isinstance(payload, list):
        rows = payload
        total = len(rows)

    ids: list[int] = []
    for row in rows:
        ticket_id = _row_ticket_id(row)
        if ticket_id and ticket_id not in ids:
            ids.append(ticket_id)

    safe_page = max(1, int(page))
    safe_size = max(1, min(50, int(page_size)))
    has_more = len(ids) > safe_size
    page_ids = tuple(ids[:safe_size])
    if total <= 0:
        total = (safe_page - 1) * safe_size + len(ids)
    return LegacyTicketSearchResult(
        ticket_ids=page_ids,
        totalcount=total,
        has_more=has_more or ((safe_page - 1) * safe_size + len(page_ids)) < total,
    )


def _row_ticket_id(row) -> int | None:
    if isinstance(row, int):
        return row if row > 0 else None
    if not isinstance(row, dict):
        return None
    raw = row.get("2") or row.get("id") or row.get(_FIELD_ID) or row.get(str(_FIELD_ID))
    if isinstance(raw, dict):
        raw = raw.get("id") or raw.get("name")
    try:
        ticket_id = int(raw)
    except (TypeError, ValueError):
        return None
    return ticket_id if ticket_id > 0 else None


def _legacy_sort(sort: str) -> tuple[int, str]:
    primary = (sort or "updated_at:desc").split(",")[0].strip()
    field, _, direction = primary.partition(":")
    order = "ASC" if direction.strip().lower() == "asc" else "DESC"
    mapping = {
        "id": _FIELD_ID,
        "title": _FIELD_NAME,
        "status": _FIELD_STATUS,
        "category": _FIELD_CATEGORY,
        "urgency": _FIELD_URGENCY,
        "assigned": _FIELD_ASSIGN,
        "created_at": _FIELD_DATE_OPEN,
        "updated_at": _FIELD_DATE_MOD,
        "solved_at": _FIELD_DATE_SOLVE,
        "closed_at": _FIELD_DATE_CLOSE,
    }
    mapped = mapping.get(field.strip())
    if mapped is None:
        raise GlpiValidation("sort inválido.")
    return mapped, order


def _clean_term(value: str) -> str:
    cleaned = "".join(char for char in value if char.isalnum() or char in " -_")
    return " ".join(cleaned.split())[:80]


def _status_ids(value: str) -> tuple[int, ...]:
    token = value.strip().lower()
    if not token or token == "all":
        return ()
    if token in _STATUS_GROUPS:
        return _STATUS_GROUPS[token]
    try:
        status_id = int(token)
    except ValueError as exc:
        raise GlpiValidation("status inválido.") from exc
    if status_id not in {1, 2, 3, 4, 5, 6, 10}:
        raise GlpiValidation("status inválido.")
    return (status_id,)
