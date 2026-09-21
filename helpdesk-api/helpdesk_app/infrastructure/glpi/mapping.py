"""Tradução da HLAPI do GLPI 11.0.5 (API 2.2) para o contrato do BFF.

Categoria: GET /api.php/v2.2/Dropdowns/ITILCategory
Urgência: enum fixo do schema Ticket (1–5), não é dropdown.
Chamado: /api.php/v2.2/Assistance/Ticket
Acompanhamento: POST .../Timeline/Followup
"""

from helpdesk_app.domain.errors import GlpiValidation
from helpdesk_app.domain.models import Category, TicketDetail, TicketSummary, TimelineEntry, TokenSet, Urgency

# Rótulos pt_BR do GLPI para o enum documentado no schema Ticket.
URGENCIES: tuple[Urgency, ...] = (
    Urgency(1, "Muito baixa"),
    Urgency(2, "Baixa"),
    Urgency(3, "Média"),
    Urgency(4, "Alta"),
    Urgency(5, "Muito alta"),
)
_URGENCY_NAMES = {item.id: item.name for item in URGENCIES}


def parse_token_set(payload: dict) -> TokenSet:
    access = str(payload.get("access_token") or "")
    refresh = str(payload.get("refresh_token") or "")
    if not access:
        raise GlpiValidation("O GLPI não devolveu access token.")
    expires_in = int(payload.get("expires_in") or 3600)
    return TokenSet(access_token=access, refresh_token=refresh, expires_in=expires_in)


def parse_categories(payload: dict | list) -> list[Category]:
    rows = _results(payload)
    categories: list[Category] = []
    for row in rows:
        if not isinstance(row, dict) or "id" not in row:
            continue
        name = str(row.get("completename") or row.get("name") or "").strip()
        if not name:
            continue
        categories.append(Category(id=int(row["id"]), name=name))
    return categories


def parse_ticket_list(payload: dict | list) -> list[TicketSummary]:
    return [_summary(row) for row in _results(payload) if isinstance(row, dict)]


def parse_ticket_detail(payload: dict, timeline_payload: dict | list) -> TicketDetail:
    summary = _summary(payload)
    description = _text(payload.get("content"))
    timeline = tuple(
        entry
        for entry in (_timeline_entry(row) for row in _results(timeline_payload))
        if entry is not None
    )
    return TicketDetail(
        id=summary.id,
        title=summary.title,
        status=summary.status,
        category=summary.category,
        urgency=summary.urgency,
        updated_at=summary.updated_at,
        description=description,
        timeline=timeline,
    )


def parse_created_id(payload: dict) -> int:
    raw = payload.get("id")
    if isinstance(raw, dict):
        raw = raw.get("id")
    if raw is None:
        raise GlpiValidation("O GLPI não devolveu o id criado.")
    return int(raw)


def create_ticket_body(*, title: str, description: str, category_id: int, urgency_id: int) -> dict:
    if urgency_id not in _URGENCY_NAMES:
        raise GlpiValidation("urgency_id inválido.")
    return {
        "name": title,
        "content": description,
        "urgency": urgency_id,
        "category": {"id": category_id},
    }


def _summary(row: dict) -> TicketSummary:
    return TicketSummary(
        id=int(row.get("id") or 0),
        title=str(row.get("name") or ""),
        status=_status_name(row.get("status")),
        category=_named(row.get("category")),
        urgency=_urgency_name(row.get("urgency")),
        updated_at=str(row.get("date_mod") or row.get("date_creation") or ""),
    )


def _timeline_entry(row: dict) -> TimelineEntry | None:
    if not isinstance(row, dict):
        return None
    kind = str(row.get("type") or row.get("itemtype") or "")
    if kind not in {"Followup", "ITILFollowup"}:
        return None
    user = row.get("user") or row.get("users_id") or {}
    author = ""
    if isinstance(user, dict):
        author = str(user.get("name") or user.get("completename") or "")
    return TimelineEntry(
        id=int(row.get("id") or 0),
        kind="followup",
        content=_text(row.get("content")),
        created_at=str(row.get("date_creation") or row.get("date") or ""),
        author_display_name=author,
    )


def _results(payload: dict | list) -> list:
    if isinstance(payload, list):
        return payload
    results = payload.get("results")
    if isinstance(results, list):
        return results
    return []


def _named(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("completename") or "")
    return ""


def _status_name(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("id") or "")
    if value is None:
        return ""
    return str(value)


def _urgency_name(value) -> str:
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return _URGENCY_NAMES.get(int(value), str(value or ""))
    except (TypeError, ValueError):
        return ""


def _text(value) -> str:
    if value is None:
        return ""
    return str(value)
