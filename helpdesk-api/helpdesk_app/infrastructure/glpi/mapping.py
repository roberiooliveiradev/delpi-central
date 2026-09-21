"""Tradução da HLAPI do GLPI 11.0.5 (API 2.2) para o contrato do BFF.

Categoria: GET /api.php/v2.2/Dropdowns/ITILCategory
Urgência: enum fixo do schema Ticket (1–5), não é dropdown.
Chamado: /api.php/v2.2/Assistance/Ticket
Acompanhamento: POST .../Timeline/Followup
"""

import html
import re

from helpdesk_app.domain.errors import GlpiValidation
from helpdesk_app.domain.models import (
    Attachment,
    Category,
    TicketDetail,
    TicketSummary,
    TimelineEntry,
    TokenSet,
    Urgency,
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
        name = display_text(row.get("completename") or row.get("name"))
        if not name:
            continue
        categories.append(Category(id=int(row["id"]), name=name))
    return categories


def parse_ticket_list(payload: dict | list) -> list[TicketSummary]:
    return [_summary(row) for row in _results(payload) if isinstance(row, dict)]


def parse_ticket_detail(payload: dict, timeline_payload: dict | list) -> TicketDetail:
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
    )


def _timeline_entry(row: dict) -> TimelineEntry | None:
    kind, payload = _timeline_payload(row)
    if kind not in {"Followup", "ITILFollowup"}:
        return None
    row = payload
    user = row.get("user") or row.get("users_id") or {}
    author = ""
    if isinstance(user, dict):
        author = display_text(user.get("name") or user.get("completename"))
    return TimelineEntry(
        id=int(row.get("id") or 0),
        kind="followup",
        content=_text(row.get("content")),
        created_at=str(row.get("date_creation") or row.get("date") or ""),
        author_display_name=author,
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


def _named(value) -> str:
    if isinstance(value, dict):
        return display_text(value.get("name") or value.get("completename"))
    return ""


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
