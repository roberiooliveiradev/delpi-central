"""Agrega indicadores consolidados de chamados GLPI para o TV Dashboard.

Semântica dos indicadores (mapeamento efetivo dos status GLPI via helpdesk-api):

- ``open``: tickets com status GLPI ``new`` (status_id 1).
- ``in_progress``: tickets em atendimento — ``processing assigned``/``processing
  planned`` (status_id 2 e 3), espelhando o grupo ``in_progress`` do BFF.
- ``pending``: tickets aguardando ação/resposta — ``waiting`` (status_id 4) e
  ``waiting approval`` (status_id 10).
- ``resolved``: tickets com status ``solved`` (status_id 5) cuja ``solved_at``
  recai no período solicitado (sem período, todos). Tickets ``closed`` (6) NÃO
  contam — fechamento é um ciclo posterior à resolução e mantemos a distinção
  exigida pelo indicador.
- ``overdue``: tickets ainda não finalizados (status 1, 2, 3, 4 ou 10) que o
  GLPI classifica com ``sla_ttr_exceeded`` verdadeiro (campo de busca nativo
  ``sla_ttr_is_late``). Resolvidos (5) e fechados (6) não entram, mesmo quando o
  GLPI marca o TTR como excedido. Este use case não compara prazos. Se um ticket
  não finalizado não trouxer o booleano, ``overdue`` fica ``null``. A ausência
  do booleano em resolvido ou fechado não invalida o indicador.
- ``pending_overdue``: união de ``pending`` e desse ``overdue`` em aberto (sem
  dupla contagem). Fica ``null`` junto com ``overdue`` quando faltar a
  classificação GLPI de algum chamado não finalizado.
- ``total_created_in_period``: tickets distintos cuja ``created_at`` recai no
  período solicitado (datas inclusivas, mesma semântica de ``resolved``; sem
  período, todos os tickets autorizados). Cada chamado conta uma única vez
  (deduplicado por ``id``) — nunca é soma de agrupamentos.

A visibilidade dos tickets é decidida pela helpdesk-api com a sessão GLPI do
usuário autenticado; este use case apenas agrega o que o BFF retorna.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Protocol

from app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGatewayError,
)

_STATUS_NEW = 1
_STATUS_PROCESSING_ASSIGNED = 2
_STATUS_PROCESSING_PLANNED = 3
_STATUS_WAITING = 4
_STATUS_SOLVED = 5
_STATUS_CLOSED = 6
_STATUS_WAITING_APPROVAL = 10

_IN_PROGRESS_IDS = frozenset({_STATUS_PROCESSING_ASSIGNED, _STATUS_PROCESSING_PLANNED})
_PENDING_IDS = frozenset({_STATUS_WAITING, _STATUS_WAITING_APPROVAL})
_UNFINISHED_IDS = frozenset({_STATUS_NEW}) | _IN_PROGRESS_IDS | _PENDING_IDS
_STATUS_MAPPING_DOC = {
    "open": "GLPI status_id 1 (new)",
    "in_progress": "GLPI status_id 2, 3 (processing assigned/planned)",
    "pending": "GLPI status_id 4, 10 (waiting, waiting approval)",
    "resolved": "GLPI status_id 5 (solved) filtered by solved_at in the requested period; closed (status_id 6) is not counted as resolved",
    "overdue": "unfinished status (1, 2, 3, 4, 10) with GLPI sla_ttr_is_late transported as sla_ttr_exceeded; solved (5) and closed (6) are excluded; null only when an unfinished ticket lacks that classification",
    "pending_overdue": "union of pending and that unfinished GLPI-classified overdue set (each ticket counted once); null when overdue is unavailable",
}

_PAGE_SIZE = 50
_MAX_PAGES = 200


class HelpdeskTicketsPageReader(Protocol):
    def list_tickets(
        self,
        *,
        authorization: str,
        page: int,
        page_size: int,
        assignee_id: int | None = None,
        category_id: int | None = None,
        urgency_id: int | None = None,
        service_authorization: str | None = None,
    ) -> dict[str, Any]: ...


class GetHelpdeskDashboardSummaryUseCase:
    def __init__(
        self,
        *,
        gateway: HelpdeskTicketsPageReader,
        now_provider=lambda: datetime.now(timezone.utc),
    ) -> None:
        self._gateway = gateway
        self._now_provider = now_provider

    def execute(
        self,
        *,
        authorization: str,
        start_date: date | None,
        end_date: date | None,
        assignee_id: int | None,
        category_id: int | None,
        urgency_id: int | None,
        scope: str | None,
        service_authorization: str | None = None,
    ) -> dict[str, Any]:
        tickets, partial = self._collect_all_pages(
            authorization=authorization,
            assignee_id=assignee_id,
            category_id=category_id,
            urgency_id=urgency_id,
            service_authorization=service_authorization,
        )

        now = self._now_provider()
        counts = {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "pending": 0,
            "overdue": 0,
            "total_created_in_period": 0,
        }
        created_seen: set[Any] = set()
        for ticket in tickets:
            if not isinstance(ticket, dict):
                continue
            status_id = _status_id(ticket)
            if status_id == _STATUS_NEW:
                counts["open"] += 1
            elif status_id in _IN_PROGRESS_IDS:
                counts["in_progress"] += 1
            elif status_id in _PENDING_IDS:
                counts["pending"] += 1
            elif status_id == _STATUS_SOLVED and _solved_in_range(ticket, start_date, end_date):
                counts["resolved"] += 1
            if _created_in_range(ticket, start_date, end_date):
                created_seen.add(_dedup_key(ticket))
        counts["total_created_in_period"] = len(created_seen)
        sla_known = _open_sla_classification_complete(tickets)
        if sla_known:
            counts["overdue"] = _count_open_overdue(tickets)
            counts["pending_overdue"] = _count_pending_overdue(tickets)
        else:
            counts["overdue"] = None
            counts["pending_overdue"] = None

        filters: dict[str, Any] = {}
        if start_date is not None:
            filters["start_date"] = start_date.isoformat()
        if end_date is not None:
            filters["end_date"] = end_date.isoformat()
        if assignee_id is not None:
            filters["assignee_id"] = assignee_id
        if category_id is not None:
            filters["category_id"] = category_id
        if urgency_id is not None:
            filters["urgency_id"] = urgency_id

        return {
            "data": counts,
            "meta": {
                "source": "glpi",
                "calculated_at": now.isoformat(),
                "filters": filters,
                "status_mapping": _STATUS_MAPPING_DOC,
                "scope": scope or "authorized",
                "partial": partial,
                "tickets_evaluated": len(tickets),
                "unavailable_indicators": (
                    [] if sla_known else ["overdue", "pending_overdue"]
                ),
            },
        }

    def _collect_all_pages(
        self,
        *,
        authorization: str,
        assignee_id: int | None,
        category_id: int | None,
        urgency_id: int | None,
        service_authorization: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        tickets: list[dict[str, Any]] = []
        for page in range(1, _MAX_PAGES + 1):
            payload = self._gateway.list_tickets(
                authorization=authorization,
                page=page,
                page_size=_PAGE_SIZE,
                assignee_id=assignee_id,
                category_id=category_id,
                urgency_id=urgency_id,
                service_authorization=service_authorization,
            )
            items = _extract_items(payload)
            tickets.extend(items)
            # A filtered page can be shorter than the GLPI page and still have
            # more raw rows. Stop only when the source says the scan is done.
            if isinstance(payload.get("has_more"), bool):
                if not payload["has_more"]:
                    return tickets, False
                continue
            if len(items) < _PAGE_SIZE or not _has_more(payload):
                return tickets, False
        return tickets, True


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items")
    if isinstance(items, list):
        return items
    if isinstance(payload.get("tickets"), list):
        return payload["tickets"]
    return []


def _has_more(payload: dict[str, Any]) -> bool:
    pagination = payload.get("pagination")
    if isinstance(pagination, dict):
        total = pagination.get("total")
        page = pagination.get("page")
        page_size = pagination.get("page_size") or pagination.get("pageSize")
        if all(isinstance(v, int) for v in (total, page, page_size)):
            return page * page_size < total
        if isinstance(pagination.get("has_more"), bool):
            return pagination["has_more"]
    if isinstance(payload.get("has_more"), bool):
        return payload["has_more"]
    return True


def _status_id(ticket: dict[str, Any]) -> int | None:
    raw = ticket.get("status_id")
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw.strip())
    return None


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _solved_in_range(
    ticket: dict[str, Any],
    start_date: date | None,
    end_date: date | None,
) -> bool:
    return _date_field_in_range(
        ticket.get("solved_at"), start_date, end_date
    )


def _created_in_range(
    ticket: dict[str, Any],
    start_date: date | None,
    end_date: date | None,
) -> bool:
    return _date_field_in_range(
        ticket.get("created_at"), start_date, end_date
    )


def _date_field_in_range(
    value: Any,
    start_date: date | None,
    end_date: date | None,
) -> bool:
    if start_date is None and end_date is None:
        return True
    parsed = _parse_dt(value)
    if parsed is None:
        return False
    parsed_date = parsed.date()
    if start_date is not None and parsed_date < start_date:
        return False
    if end_date is not None and parsed_date > end_date:
        return False
    return True


def _dedup_key(ticket: dict[str, Any]) -> Any:
    ticket_id = ticket.get("id")
    if isinstance(ticket_id, bool):
        return ("_obj", id(ticket))
    if isinstance(ticket_id, (int, str)):
        return ticket_id
    return ("_obj", id(ticket))


def _open_sla_classification_complete(tickets: list[Any]) -> bool:
    for ticket in tickets:
        if not isinstance(ticket, dict):
            return False
        if _status_id(ticket) not in _UNFINISHED_IDS:
            continue
        if not isinstance(ticket.get("sla_ttr_exceeded"), bool):
            return False
    return True


def _count_open_overdue(tickets: list[Any]) -> int:
    total = 0
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        if _status_id(ticket) in _UNFINISHED_IDS and ticket.get("sla_ttr_exceeded") is True:
            total += 1
    return total


def _count_pending_overdue(tickets: list[Any]) -> int:
    total = 0
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        status_id = _status_id(ticket)
        if status_id in _PENDING_IDS or (
            status_id in _UNFINISHED_IDS and ticket.get("sla_ttr_exceeded") is True
        ):
            total += 1
    return total


def build_get_helpdesk_dashboard_summary_use_case() -> GetHelpdeskDashboardSummaryUseCase:
    from app.infrastructure.gateways.helpdesk_bff_gateway import (
        build_helpdesk_bff_gateway,
    )

    return GetHelpdeskDashboardSummaryUseCase(gateway=build_helpdesk_bff_gateway())


__all__ = [
    "GetHelpdeskDashboardSummaryUseCase",
    "HelpdeskBffGatewayError",
    "build_get_helpdesk_dashboard_summary_use_case",
]
