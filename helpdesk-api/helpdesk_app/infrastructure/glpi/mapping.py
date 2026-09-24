"""Tradução da HLAPI do GLPI 11.0.5 (API 2.2) para o contrato do BFF.

Categoria: GET /api.php/v2.2/Dropdowns/ITILCategory?filter=is_helpdesk_visible==true
Urgência: enum fixo do schema Ticket (1–5), não é dropdown.
Chamado: /api.php/v2.2/Assistance/Ticket
Acompanhamento: POST .../Timeline/Followup
Solução (leitura): Timeline type Solution / ITILSolution → kind=solution
"""

import html
import re
import unicodedata
from dataclasses import replace

from helpdesk_app.application.services.message_html_sanitizer import sanitize_message_html
from helpdesk_app.domain.errors import GlpiNotFound, GlpiValidation
from helpdesk_app.domain.models import (
    Attachment,
    CatalogUser,
    Category,
    PersonIdentity,
    TicketDetail,
    TicketListPage,
    TicketListQuery,
    TicketSummary,
    TicketValidation,
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
    "solved_at": "date_solve",
    "closed_at": "date_close",
    # `assigned` is not an HLAPI RSQL column — handled via legacy Search exception.
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
    created_from: str = "",
    created_to: str = "",
    assignee_id: int | None = None,
    sort: str = "updated_at:desc",
    page: int = 1,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> TicketListQuery:
    if assignee_id is not None and int(assignee_id) < 1:
        raise GlpiValidation("assignee_id inválido.")
    clauses: list[str] = ["is_deleted==false"]
    term = _search_term(q)
    if term:
        clauses.append(f"(name=like=*{term}*,content=like=*{term}*)")
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
    created_start = _day(created_from, "created_from")
    created_end = _day(created_to, "created_to")
    if created_start:
        clauses.append(f"date_creation=ge={created_start}T00:00:00")
    if created_end:
        clauses.append(f"date_creation=le={created_end}T23:59:59")
    safe_page = max(1, page)
    safe_size = min(_MAX_PAGE_SIZE, max(1, page_size))
    client_sort = (sort or "updated_at:desc").strip() or "updated_at:desc"
    hlapi_sort = _sort_clause(_hlapi_sort_token(client_sort))
    return TicketListQuery(
        filter=";".join(clauses),
        start=(safe_page - 1) * safe_size,
        limit=safe_size + 1,
        sort=hlapi_sort,
        page=safe_page,
        page_size=safe_size,
        assignee_id=int(assignee_id) if assignee_id is not None else None,
        client_sort=client_sort,
        q=term,
        status=(status or "").strip(),
        urgency_id=urgency_id,
        category_id=category_id,
        updated_from=(updated_from or "").strip(),
        updated_to=(updated_to or "").strip(),
        created_from=(created_from or "").strip(),
        created_to=(created_to or "").strip(),
    )


def _hlapi_sort_token(client_sort: str) -> str:
    """Drop `assigned` levels (HLAPI cannot sort team); keep remaining or default."""
    levels: list[str] = []
    for chunk in (client_sort or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        field = chunk.split(":", 1)[0].strip()
        if field == "assigned":
            continue
        levels.append(chunk)
    return ",".join(levels) if levels else "updated_at:desc"


def parse_ticket_detail(payload: dict, timeline_payload: dict | list) -> TicketDetail:
    if _is_deleted(payload):
        raise GlpiNotFound("Chamado não encontrado.")
    summary = _summary(payload)
    rows = [row for row in _results(timeline_payload) if isinstance(row, dict)]
    attachments = tuple(item for item in (_attachment(row) for row in rows) if item is not None)
    allowed_docs = {item.document_id for item in attachments}
    description_html = sanitize_message_html(
        _repair_cp850_mojibake(str(payload.get("content") or "")),
        ticket_id=summary.id,
        allowed_document_ids=allowed_docs,
    )
    description = _text(description_html) if description_html else _text(payload.get("content"))
    timeline = tuple(
        entry
        for entry in (_timeline_entry(row, ticket_id=summary.id, allowed_document_ids=allowed_docs) for row in rows)
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
        description_html=description_html,
        timeline=timeline,
        attachments=attachments,
        created_at=summary.created_at,
        requester_display_name=summary.requester_display_name,
        assigned_display_name=summary.assigned_display_name,
        assigned_user_id=_team_user_id(payload, "assigned"),
        requester_identity=_requester_identity(payload),
        status_id=summary.status_id,
        can_followup=ticket_allows_followup(summary.status_id),
        observers_display_name=_observer_names(payload),
        solved_at=summary.solved_at,
        closed_at=summary.closed_at,
        sla_ttr=summary.sla_ttr,
        sla_tto=summary.sla_tto,
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


def team_member_observer_body(user_id: int) -> dict:
    """HD-011: only type/role/id — never requester or entity."""
    if user_id <= 0:
        raise GlpiValidation("observer_id inválido.")
    return {"type": "User", "role": "observer", "id": int(user_id)}


def team_member_assigned_body(user_id: int) -> dict:
    """HD-011: only type/role/id — never requester or entity."""
    if user_id <= 0:
        raise GlpiValidation("assignee_id inválido.")
    return {"type": "User", "role": "assigned", "id": int(user_id)}


def normalize_assignee_id(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        user_id = int(raw)
    except (TypeError, ValueError) as exc:
        raise GlpiValidation("assignee_id inválido.") from exc
    if user_id <= 0:
        raise GlpiValidation("assignee_id inválido.")
    return user_id


# Contas padrão / serviço do GLPI — não são técnicos atribuíveis na Minha DELPI.
_SYSTEM_USERNAMES = frozenset(
    {
        "glpi",
        "post-only",
        "tech",
        "normal",
        "minha-delpi-upload",
    }
)


def _fold_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value or "")
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def search_term_variants(q: str) -> tuple[str, ...]:
    """Case + accent variants so «robério» também acha «Roberio» e vice-versa."""
    term = _search_term(str(q or "").strip())
    if not term:
        return ()
    variants: list[str] = []
    for base in (term, _fold_accents(term)):
        if not base:
            continue
        for candidate in (base, base.lower(), base.upper(), base.capitalize(), base.title()):
            if candidate and candidate not in variants:
                variants.append(candidate)
    return tuple(variants)


def build_user_search_filter(q: str = "") -> str:
    """RSQL for Administration/User — always keyed by id in the response (G-A4).

    HLAPI User **não** filtra por `email` / `name` (Unknown property → 400).
    Busca em username/firstname/realname com variantes de caixa (MySQL like
    case-sensitive nesta collação: «michael» ≠ «Michael»).
    """
    term = _search_term(str(q or "").strip())
    base = "is_active==true"
    if not term:
        return base
    if term.isdigit():
        return f"{base};id=={int(term)}"
    # E-mail: usa só o local-part nos campos de nome (email não é propriedade RSQL).
    search = term.split("@", 1)[0] if "@" in term else term
    variants = search_term_variants(search)
    parts: list[str] = []
    for variant in variants:
        parts.extend(
            [
                f"username=like=*{variant}*",
                f"realname=like=*{variant}*",
                f"firstname=like=*{variant}*",
            ]
        )
    return f"{base};({','.join(parts)})"


def build_user_email_filter(email: str) -> str:
    """Legacy helper — HLAPI User rejects `email` filters; prefer client-side match."""
    normalized = _email(email)
    if not normalized:
        raise GlpiValidation("email inválido.")
    local = normalized.split("@", 1)[0]
    return build_user_search_filter(local)


def is_usable_catalog_label(name: str) -> bool:
    cleaned = display_text(name)
    if not cleaned:
        return False
    lowered = cleaned.casefold()
    if lowered in _SYSTEM_USERNAMES:
        return False
    if "plugin" in lowered and "glpi" in lowered:
        return False
    if cleaned in {"0", "0 0"} or cleaned.isdigit():
        return False
    return True


def is_system_username(username: str) -> bool:
    return display_text(username).casefold() in _SYSTEM_USERNAMES


def parse_catalog_users(payload: dict | list) -> list[CatalogUser]:
    users: list[CatalogUser] = []
    for row in _results(payload):
        if not isinstance(row, dict):
            continue
        if _is_deleted(row):
            continue
        raw_id = row.get("id")
        try:
            user_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if user_id <= 0:
            continue
        username = display_text(row.get("username") or row.get("name"))
        if is_system_username(username):
            continue
        emails = _emails(row)
        email = emails[0] if emails else ""
        name = _person_name(row) or username
        if not is_usable_catalog_label(name):
            if email and is_usable_catalog_label(username):
                name = username
            else:
                continue
        if not is_usable_catalog_label(name):
            continue
        users.append(CatalogUser(id=user_id, display_name=name, email=email))
    return users


def filter_assignable_catalog_users(users: list[CatalogUser] | tuple[CatalogUser, ...]) -> list[CatalogUser]:
    """Post-filter for in-memory / FakeGlpi catalogs (no username field)."""
    out: list[CatalogUser] = []
    for user in users:
        label = display_text(getattr(user, "display_name", ""))
        if not is_usable_catalog_label(label):
            continue
        email = _email(getattr(user, "email", "") or "")
        out.append(
            CatalogUser(
                id=int(user.id),
                display_name=label,
                email=email,
                directory_user_id=str(getattr(user, "directory_user_id", "") or ""),
                has_photo=bool(getattr(user, "has_photo", False)),
            )
        )
    return out


def parse_profile_user_ids(payload: dict | list) -> set[int]:
    """Extract users_id from Profile_User / Profile→User relation payloads (HLAPI or apirest)."""
    ids: set[int] = set()
    rows: list = []
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            rows = payload["data"]
        elif isinstance(payload.get("results"), list):
            rows = payload["results"]
        elif isinstance(payload.get("items"), list):
            rows = payload["items"]
        else:
            rows = [payload]
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = (
            row.get("users_id")
            or row.get("user_id")
            or row.get("id")
            or row.get("2")  # search forcedisplay users_id
        )
        if isinstance(raw, dict):
            raw = raw.get("id") or raw.get("users_id")
        try:
            user_id = int(raw)
        except (TypeError, ValueError):
            continue
        if user_id > 0:
            ids.add(user_id)
    return ids


def normalize_observer_ids(raw) -> tuple[int, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        raise GlpiValidation("observer_ids inválido.")
    if len(raw) > 10:
        raise GlpiValidation("observer_ids excede o limite.")
    seen: set[int] = set()
    ordered: list[int] = []
    for item in raw:
        try:
            user_id = int(item)
        except (TypeError, ValueError) as exc:
            raise GlpiValidation("observer_id inválido.") from exc
        if user_id <= 0:
            raise GlpiValidation("observer_id inválido.")
        if user_id in seen:
            continue
        seen.add(user_id)
        ordered.append(user_id)
    return tuple(ordered)


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
        requester_display_name=_requester_name(row),
        status_id=_status_id(row.get("status")),
        solved_at=_optional_instant(row.get("date_solve")),
        closed_at=_optional_instant(row.get("date_close")),
        sla_ttr=_named(row.get("sla_ttr")),
        sla_tto=_named(row.get("sla_tto")),
        assigned_user_id=_team_user_id(row, "assigned"),
    )


def _optional_instant(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return ""
    return text


def _timeline_entry(
    row: dict,
    *,
    ticket_id: int,
    allowed_document_ids: set[int],
) -> TimelineEntry | None:
    kind, payload = _timeline_payload(row)
    entry_kind = _timeline_kind(kind)
    if entry_kind is None:
        return None
    row = payload
    if _is_private(row):
        return None
    user = row.get("user") or row.get("users_id") or {}
    if isinstance(user, int):
        user = {"id": user}
    author = _person_name(user) if isinstance(user, dict) else ""
    content_html = sanitize_message_html(
        _repair_cp850_mojibake(str(row.get("content") or "")),
        ticket_id=ticket_id,
        allowed_document_ids=allowed_document_ids,
    )
    content = _text(content_html) if content_html else _text(row.get("content"))
    return TimelineEntry(
        id=int(row.get("id") or 0),
        kind=entry_kind,
        content=content,
        content_html=content_html,
        created_at=str(row.get("date_creation") or row.get("date") or ""),
        author_display_name=author,
        author_identity=_person_identity(user if isinstance(user, dict) else {}),
    )


def _timeline_kind(raw: str) -> str | None:
    """Map HLAPI Timeline types exposed in Helpdesk conversation.

    Validation stays on ``validations[]`` (not inline timeline). Task is included so
    technician workspace can verify create-task postconditions.
    """
    if raw in {"Followup", "ITILFollowup"}:
        return "followup"
    if raw in {"Solution", "ITILSolution"}:
        return "solution"
    if raw in {"Task", "TicketTask", "ITILTask"}:
        return "task"
    return None


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
    # HLAPI Timeline type Document often exposes the document's own id as `id`
    # (no documents_id). Prefer documents_id when present (Document_Item).
    if document_id in (None, "") and kind == "Document":
        document_id = payload.get("id")
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


VALIDATION_WAITING = 2
VALIDATION_ACCEPTED = 3
VALIDATION_REFUSED = 4


def parse_ticket_validations(payload: dict | list) -> tuple[TicketValidation, ...]:
    rows = _results(payload)
    items: list[TicketValidation] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind, body = _timeline_payload(row)
        kind_l = str(kind or "").lower()
        if kind_l and kind_l not in {"validation", "ticketvalidation", "itilvalidation"}:
            continue
        if not kind_l and body.get("requested_approver_id") is None and body.get("status") is None:
            continue
        raw_id = body.get("id")
        if isinstance(raw_id, dict):
            raw_id = raw_id.get("id")
        try:
            validation_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if validation_id <= 0:
            continue
        try:
            status = int(body.get("status"))
        except (TypeError, ValueError):
            continue
        approver = body.get("requested_approver_id")
        if isinstance(approver, dict):
            approver = approver.get("id")
        if approver in (None, ""):
            target = body.get("items_id_target")
            if isinstance(target, dict):
                target = target.get("id")
            approver = target
        try:
            approver_id = int(approver) if approver not in (None, "") else None
        except (TypeError, ValueError):
            approver_id = None
        items.append(
            TicketValidation(
                id=validation_id,
                status=status,
                submission_comment=display_text(
                    body.get("submission_comment") or body.get("comment_submission")
                ),
                approval_comment=display_text(
                    body.get("approval_comment") or body.get("comment_validation")
                ),
                requested_approver_id=approver_id if approver_id and approver_id > 0 else None,
            )
        )
    return tuple(items)


def apply_validation_viewer(
    validations: tuple[TicketValidation, ...],
    viewer: PersonIdentity,
) -> tuple[TicketValidation, ...]:
    viewer_id = viewer.user_id
    return tuple(
        replace(
            item,
            mine_to_decide=bool(
                viewer_id
                and item.requested_approver_id == viewer_id
                and item.status == VALIDATION_WAITING
            ),
        )
        for item in validations
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


def _team_user_id(row: dict, role: str) -> int | None:
    team = row.get("team") or []
    if not isinstance(team, list):
        return None
    for member in team:
        if not isinstance(member, dict):
            continue
        if str(member.get("role") or "") != role:
            continue
        raw = member.get("id")
        try:
            user_id = int(raw)
        except (TypeError, ValueError):
            continue
        if user_id > 0:
            return user_id
    return None


def _observer_names(row: dict) -> str:
    team = row.get("team") or []
    if not isinstance(team, list):
        return ""
    names: list[str] = []
    for member in team:
        if not isinstance(member, dict):
            continue
        if str(member.get("role") or "") != "observer":
            continue
        name = _person_name(member)
        if name:
            names.append(name)
    return ", ".join(names)


def ticket_allows_followup(status_id: int | None) -> bool:
    """14-H1: Colaborador still posts follow-up on solved (5); closed (6) is 403."""
    return status_id != 6


def ticket_allows_technician_ops(status_id: int | None) -> bool:
    """Technician Solution/Task/Validation creates: blocked only when ticket is closed."""
    return status_id != 6


def timeline_has_solution(timeline: tuple) -> bool:
    return any(getattr(entry, "kind", None) == "solution" for entry in (timeline or ()))


def timeline_has_entry(timeline: tuple, *, kind: str, entry_id: int) -> bool:
    return any(
        getattr(entry, "kind", None) == kind and int(getattr(entry, "id", 0) or 0) == int(entry_id)
        for entry in (timeline or ())
    )


def solicitante_cycle_flags(
    *,
    requester_mine: bool,
    status_id: int | None,
    satisfaction_submitted: bool,
    legacy_enabled: bool,
) -> tuple[bool, bool, bool]:
    """Backend-first H10 capabilities (legacy apirest). Returns accept, reject, submit_satisfaction."""
    if not legacy_enabled or not requester_mine:
        return False, False, False
    can_decide = status_id == 5
    can_sat = status_id == 6 and not satisfaction_submitted
    return can_decide, can_decide, can_sat


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
    chunks = [chunk.strip() for chunk in (value or "updated_at:desc").split(",") if chunk.strip()]
    if not chunks:
        chunks = ["updated_at:desc"]
    if len(chunks) > 3:
        raise GlpiValidation("sort inválido.")
    parts: list[str] = []
    seen: set[str] = set()
    for raw in chunks:
        field, _, direction = raw.partition(":")
        mapped = _SORT_FIELDS.get(field.strip())
        if mapped is None:
            raise GlpiValidation("sort inválido.")
        if mapped in seen:
            raise GlpiValidation("sort inválido.")
        order = direction.strip().lower() or "desc"
        if order not in {"asc", "desc"}:
            raise GlpiValidation("sort inválido.")
        seen.add(mapped)
        parts.append(f"{mapped}:{order}")
    return ",".join(parts)


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
