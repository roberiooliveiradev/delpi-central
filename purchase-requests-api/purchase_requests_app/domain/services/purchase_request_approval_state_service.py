"""Aggregate per-item approval-state rows (SC1) into one state per request.

C1_APROV vive por item (C1_ITEM) na SC1. A notificação, porém, é por
Solicitação de Compra — o usuário deve receber um único aviso quando a SC
muda de estado, não um por item.

Regra de agregação (conservadora):
- qualquer item ``rejected``  → SC ``rejected``
- todos os itens ``approved`` → SC ``approved``
- qualquer item ``blocked``   → SC ``blocked``
- demais combinações          → SC ``unknown``
"""

from __future__ import annotations

from typing import Any, Iterable

from purchase_requests_app.domain.services.purchase_request_domain_service import (
    map_approval_status,
)

NOTIFIABLE_STATUSES = frozenset({"approved", "rejected"})

_EVENT_BY_STATUS = {
    "approved": "purchase_request_approved",
    "rejected": "purchase_request_rejected",
}


def event_key_for_status(status: str) -> str | None:
    return _EVENT_BY_STATUS.get((status or "").strip())


def is_notifiable_status(status: str) -> bool:
    return (status or "").strip() in NOTIFIABLE_STATUSES


def aggregate_request_approval_states(
    items: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in items or []:
        branch = str(item.get("branch") or "").strip()
        request_number = str(item.get("request_number") or "").strip()
        if not branch or not request_number:
            continue
        grouped.setdefault((branch, request_number), []).append(item)

    states: list[dict[str, Any]] = []
    for (branch, request_number), rows in grouped.items():
        statuses = [
            str(
                row.get("approval_status")
                or map_approval_status(row.get("approval_raw"))
            ).strip()
            for row in rows
        ]
        if any(status == "rejected" for status in statuses):
            status = "rejected"
        elif statuses and all(value == "approved" for value in statuses):
            status = "approved"
        elif any(value == "blocked" for value in statuses):
            status = "blocked"
        else:
            status = "unknown"

        requester = next(
            (
                str(row.get("requester_protheus_user_id") or "").strip()
                for row in rows
                if str(row.get("requester_protheus_user_id") or "").strip()
            ),
            None,
        )
        approver = next(
            (
                str(row.get("approver_name") or "").strip()
                for row in rows
                if str(row.get("approver_name") or "").strip()
            ),
            None,
        )
        states.append(
            {
                "branch": branch,
                "request_number": request_number,
                "approval_status": status,
                "requester_protheus_user_id": requester,
                "approver_name": approver,
            }
        )
    return states
