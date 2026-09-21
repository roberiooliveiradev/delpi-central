"""Tradução da HLAPI do GLPI 11.0.5 (API 2.2) para o contrato do BFF.

Categoria: GET /api.php/v2.2/Dropdowns/ITILCategory?filter=is_helpdesk_visible==true
Urgência: enum fixo do schema Ticket (1–5), não é dropdown.
Chamado: /api.php/v2.2/Assistance/Ticket
Acompanhamento: POST .../Timeline/Followup
"""

import html
import re
from dataclasses import replace

from helpdesk_app.domain.errors import GlpiNotFound, GlpiValidation
from helpdesk_app.domain.models import (
    Attachment,
    Category,
    PersonIdentity,
    TicketDetail,
    TicketListPage,
    TicketListQuery,
    TicketSummary,
    TimelineEntry,
    TokenSet,
    Urgency,
    same_person,
)

# Rótulos pt_BR do GLPI para o enum documentado no schema Ticket.
URGENCIES: tuple[Urgency, ...] = (
    Urgency(1, "Muito baixa"),
    Urgency(2, "Baixa"),
    Urgency(3, "Média"),
    Urgency(4, "Alta"),
    Urgency(5, "Muito alta"),
)
_URGENCY_NAMES = {item.id: item.name for item in URGENCIES}
# Chamados antigos gravaram UTF-8 lido como CP850. O sinal estável é o traço ├.
_CP850_MOJIBAKE = "\u251c"
_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STATUS_GROUPS = {
    "open": (1, 10, 2, 3, 4),
    "in_progress": (2, 3),
    "pending": (4,),
    "approval": (10,),
    "solved": (5,),
    "closed": (6,),
}
_SORT_FIELDS = {
    "id": "id",
    "title": "name",
    "status": "status.id",
    "category": "category.name",
    "urgency": "urgency",
    "updated_at": "date_mod",
    "created_at": "date_creation",
}
_MAX_PAGE_SIZE = 50
_DEFAULT_PAGE_SIZE = 20


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
        if not _helpdesk_visible(row):
            continue
        name = display_text(row.get("completename") or row.get("name"))
        if not name:
            continue
        categories.append(Category(id=int(row["id"]), name=name))
    return categories


def payload_row_count(payload: dict | list) -> int:
    return len(_results(payload))


def parse_ticket_list(payload: dict | list) -> list[TicketSummary]:
    return [
        _summary(row)
        for row in _results(payload)
        if isinstance(row, dict) and not _is_deleted(row)
    ]


def parse_ticket_page(payload: dict | list, query: TicketListQuery) -> TicketListPage:
    rows = parse_ticket_list(payload)
    has_more = len(rows) > query.page_size
    return TicketListPage(
        items=tuple(rows[: query.page_size]),
        page=query.page,
        page_size=query.page_size,
        has_more=has_more,
    )


def build_ticket_list_query(
    *,
    q: str = "",
    status: str = "",
    urgency_id: int | None = None,
    category_id: int | None = None,
    updated_from: str = "",
    updated_to: str = "",
    sort: str = "updated_at:desc",
    page: int = 1,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> TicketListQuery:
    clauses: list[str] = ["is_deleted==false"]
    term = _search_term(q)
    if term:
        clauses.append(f"name=like=*{term}*")
    status_ids = _status_ids(status)
    if status_ids:
        joined = ",".join(str(item) for item in status_ids)
        clauses.append(f"status.id=in=({joined})" if len(status_ids) > 1 else f"status.id=={status_ids[0]}")
    if urgency_id is not None:
        if urgency_id not in _URGENCY_NAMES:
            raise GlpiValidation("urgency_id inválido.")
        clauses.append(f"urgency=={urgency_id}")
    if category_id is not None:
        if category_id < 1:
            raise GlpiValidation("category_id inválido.")
        clauses.append(f"category.id=={category_id}")
    start_day = _day(updated_from, "updated_from")
    end_day = _day(updated_to, "updated_to")
    if start_day:
        clauses.append(f"date_mod=ge={start_day}T00:00:00")
    if end_day:
        clauses.append(f"date_mod=le={end_day}T23:59:59")
    safe_page = max(1, page)
    safe_size = min(_MAX_PAGE_SIZE, max(1, page_size))
    return TicketListQuery(
        filter=";".join(clauses),
        start=(safe_page - 1) * safe_size,
        limit=safe_size + 1,
        sort=_sort_clause(sort),
        page=safe_page,
        page_size=safe_size,
    )


def parse_ticket_detail(payload: dict, timeline_payload: dict | list) -> TicketDetail:
    if _is_deleted(payload):
        raise GlpiNotFound("Chamado não encontrado.")
    summary = _summary(payload)
    description = _text(payload.get("content"))
    rows = [row for row in _results(timeline_payload) if isinstance(row, dict)]
    timeline = tuple(entry for entry in (_timeline_entry(row) for row in rows) if entry is not None)
    attachments = tuple(item for item in (_attachment(row) for row in rows) if item is not None)
    return TicketDetail(
        id=summary.id,
        title=summary.title,
        status=summary.status,
        category=summary.category,
        urgency=summary.urgency,
        updated_at=summary.updated_at,
        description=description,
        timeline=timeline,
        attachments=attachments,
        created_at=summary.created_at,
        requester_display_name=_requester_name(payload),
        assigned_display_name=summary.assigned_display_name,
        requester_identity=_requester_identity(payload),
        status_id=summary.status_id,
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
        title=display_text(row.get("name")),
        status=_status_name(row.get("status")),
        category=_named(row.get("category")),
        urgency=_urgency_name(row.get("urgency")),
        updated_at=str(row.get("date_mod") or row.get("date_creation") or ""),
        created_at=str(row.get("date_creation") or ""),
        assigned_display_name=_team_name(row, "assigned"),
        status_id=_status_id(row.get("status")),
    )


def _timeline_entry(row: dict) -> TimelineEntry | None:
    kind, payload = _timeline_payload(row)
    if kind not in {"Followup", "ITILFollowup"}:
        return None
    row = payload
    if _is_private(row):
        return None
    user = row.get("user") or row.get("users_id") or {}
    if isinstance(user, int):
        user = {"id": user}
    author = _person_name(user) if isinstance(user, dict) else ""
    return TimelineEntry(
        id=int(row.get("id") or 0),
        kind="followup",
        content=_text(row.get("content")),
        created_at=str(row.get("date_creation") or row.get("date") or ""),
        author_display_name=author,
        author_identity=_person_identity(user if isinstance(user, dict) else {}),
    )


def attachment_filename(value: str) -> str:
    name = value.replace("\\", "/").split("/")[-1]
    cleaned = "".join(char for char in name if char not in "\r\n\"")
    cleaned = cleaned.strip().lstrip(".")
    return (cleaned or "anexo")[:180]


def _attachment(row: dict) -> Attachment | None:
    kind, payload = _timeline_payload(row)
    if kind not in {"Document", "Document_Item"}:
        return None
    document_id = payload.get("documents_id") or payload.get("document_id")
    if isinstance(document_id, dict):
        document_id = document_id.get("id")
    if document_id in (None, ""):
        return None
    return Attachment(
        document_id=int(document_id),
        filename=display_text(payload.get("filename") or payload.get("name")),
        mime=str(payload.get("mime") or ""),
    )


def _timeline_payload(row: dict) -> tuple[str, dict]:
    nested = row.get("item")
    if isinstance(nested, dict):
        return str(row.get("type") or row.get("itemtype") or ""), nested
    return str(row.get("type") or row.get("itemtype") or ""), row


def _results(payload: dict | list) -> list:
    if isinstance(payload, list):
        return payload
    results = payload.get("results")
    if isinstance(results, list):
        return results
    return []


def apply_viewer_identity(detail: TicketDetail, viewer: PersonIdentity) -> TicketDetail:
    return replace(
        detail,
        requester_mine=same_person(detail.requester_identity, viewer),
        timeline=tuple(
            replace(entry, mine=same_person(entry.author_identity, viewer)) for entry in detail.timeline
        ),
    )


def parse_viewer_identity(session: dict, viewer_email: str = "") -> PersonIdentity:
    return PersonIdentity(user_id=_person_id({"id": session.get("user_id")}), emails=_emails(viewer_email))


def _requester_name(row: dict) -> str:
    named = _team_name(row, "requester")
    if named:
        return named
    recipient = row.get("user_recipient")
    if isinstance(recipient, dict):
        return _person_name(recipient)
    return ""


def _requester_identity(row: dict) -> PersonIdentity:
    team = row.get("team") or []
    if isinstance(team, list):
        for member in team:
            if isinstance(member, dict) and str(member.get("role") or "") == "requester":
                return _person_identity(member)
    recipient = row.get("user_recipient")
    if isinstance(recipient, dict):
        return _person_identity(recipient)
    return PersonIdentity()


def _person_identity(value: dict) -> PersonIdentity:
    return PersonIdentity(user_id=_person_id(value), emails=_emails(value))


def _person_id(value: dict) -> int | None:
    for key in ("id", "users_id"):
        raw = value.get(key)
        if isinstance(raw, dict):
            raw = raw.get("id")
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return None


def _emails(value: dict | str) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(_email(value))
    elif isinstance(value, dict):
        found.append(_email(value.get("email")))
        emails = value.get("emails")
        if isinstance(emails, list):
            for item in emails:
                if isinstance(item, str):
                    found.append(_email(item))
                elif isinstance(item, dict):
                    found.append(_email(item.get("email")))
    return tuple(item for item in dict.fromkeys(found) if item)


def _email(value) -> str:
    text = str(value or "").strip().lower()
    return text if "@" in text else ""


def _team_name(row: dict, role: str) -> str:
    team = row.get("team") or []
    if not isinstance(team, list):
        return ""
    for member in team:
        if not isinstance(member, dict):
            continue
        if str(member.get("role") or "") != role:
            continue
        return _person_name(member)
    return ""


def _person_name(value: dict) -> str:
    first = display_text(value.get("firstname"))
    last = display_text(value.get("realname"))
    joined = " ".join(part for part in (first, last) if part)
    labeled = display_text(
        value.get("display_name") or value.get("completename") or value.get("name")
    )
    return _fuller_person_name(joined, labeled)


def _fuller_person_name(*names: str) -> str:
    return max((name for name in names if name), key=lambda name: (len(name.split()), len(name)), default="")


def _search_term(value: str) -> str:
    cleaned = "".join(char for char in value if char.isalnum() or char in " -_")
    return _WHITESPACE.sub(" ", cleaned).strip()[:80]


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


def _day(value: str, field: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if not _DATE_ONLY.match(text):
        raise GlpiValidation(f"{field} inválido.")
    return text


def _sort_clause(value: str) -> str:
    raw = (value or "updated_at:desc").strip()
    field, _, direction = raw.partition(":")
    mapped = _SORT_FIELDS.get(field)
    if mapped is None:
        raise GlpiValidation("sort inválido.")
    order = direction.strip().lower() or "desc"
    if order not in {"asc", "desc"}:
        raise GlpiValidation("sort inválido.")
    return f"{mapped}:{order}"


def _helpdesk_visible(row: dict) -> bool:
    if "is_helpdesk_visible" not in row and "is_helpdeskvisible" not in row:
        return True
    value = row.get("is_helpdesk_visible")
    if value is None:
        value = row.get("is_helpdeskvisible")
    return value is True or value == 1 or value == "1"


def _is_deleted(row: dict) -> bool:
    value = row.get("is_deleted")
    return value is True or value == 1 or value == "1"


def _is_private(row: dict) -> bool:
    value = row.get("is_private")
    return value is True or value == 1 or value == "1"


def _named(value) -> str:
    if isinstance(value, dict):
        return display_text(value.get("name") or value.get("completename"))
    return ""


def _status_id(value) -> int | None:
    raw = value.get("id") if isinstance(value, dict) else value
    try:
        status_id = int(raw)
    except (TypeError, ValueError):
        return None
    if status_id not in {1, 2, 3, 4, 5, 6, 10}:
        return None
    return status_id


def _status_name(value) -> str:
    if isinstance(value, dict):
        named = value.get("name")
        if named:
            return display_text(named)
        return display_text(value.get("id"))
    if value is None:
        return ""
    return display_text(value)


def _urgency_name(value) -> str:
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return _URGENCY_NAMES.get(int(value), str(value or ""))
    except (TypeError, ValueError):
        return ""


def display_text(value) -> str:
    """Texto visível: repara o CP850 legado e remove o HTML que o GLPI grava no conteúdo."""
    if value is None:
        return ""
    text = _repair_cp850_mojibake(str(value))
    text = _HTML_TAG.sub(" ", text)
    text = html.unescape(text)
    return _WHITESPACE.sub(" ", text).strip()


def _text(value) -> str:
    return display_text(value)


def _repair_cp850_mojibake(text: str) -> str:
    if _CP850_MOJIBAKE not in text:
        return text
    try:
        repaired = text.encode("cp850").decode("utf-8")
    except UnicodeError:
        return text
    if _CP850_MOJIBAKE in repaired:
        return text
    return repaired
