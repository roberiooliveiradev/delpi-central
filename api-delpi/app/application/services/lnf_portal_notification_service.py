"""Notificações in-app Lançamento de Notas Fiscais via Core API (sino do portal)."""

from __future__ import annotations

import html
import logging
from decimal import Decimal
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "lancamento-notas-fiscais"
_CATEGORY = "lancamento_notas_fiscais"
_APP_BASE = "/apps/lancamento-notas-fiscais"
_EVENT_BLOCK_ASSIGNED = "lnf_request_blocked_assigned"

BLOCK_REASON_LABELS: dict[str, str] = {
    "purchase_order": "Aguardando pedido de compra",
    "supplier_registration": "Aguardando cadastro de fornecedor",
    "information_correction": "Aguardando correção de informações",
    "other": "Outra pendência",
}

BRANCH_LABELS: dict[str, str] = {
    "01": "Filial 01 (SC)",
    "02": "Filial 02 (ES)",
}


def lnf_portal_notifications_enabled() -> bool:
    if not settings.LNF_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def block_reason_label(reason: str | None) -> str:
    key = str(reason or "").strip()
    return BLOCK_REASON_LABELS.get(key, key or "Pendência")


def branch_label(branch_code: str | None) -> str:
    code = str(branch_code or "").strip()
    return BRANCH_LABELS.get(code, f"Filial {code}" if code else "Filial")


def request_portal_route(*, branch_code: str | None, request_id: str) -> str:
    code = str(branch_code or "").strip()
    filial = "filial-02" if code == "02" else "filial-01"
    return f"{_APP_BASE}/{filial}?requestId={request_id}"


def block_assigned_dedupe_key(*, request_id: str, user_id: str) -> str:
    return f"lnf:block_assigned:{request_id}:{user_id}"


def should_notify_block_assignee(
    *,
    assignee_user_id: str | None,
    actor_user_id: str | None = None,
) -> bool:
    normalized = (assignee_user_id or "").strip()
    if not normalized or normalized == "unknown":
        return False
    actor = (actor_user_id or "").strip()
    if actor and actor == normalized:
        return False
    return True


def _format_document(document_number: str | None, series: str | None) -> str:
    digits = "".join(ch for ch in str(document_number or "") if ch.isdigit())
    display = digits.zfill(9) if digits else str(document_number or "—")
    serie = str(series or "").strip()
    return f"{display} / {serie}" if serie else display


def _format_amount(amount: Any) -> str:
    try:
        value = Decimal(str(amount))
    except Exception:
        return str(amount or "—")
    quantized = f"{value:.2f}"
    integer, _, fraction = quantized.partition(".")
    integer_fmt = f"{int(integer):,}".replace(",", ".")
    return f"R$ {integer_fmt},{fraction}"


def build_block_assigned_copy(
    *,
    actor_name: str | None,
    block_reason: str | None,
    block_description: str | None,
    document_number: str | None,
    series: str | None,
    supplier_name: str | None,
    branch_code: str | None,
    amount: Any = None,
    issue_date: str | None = None,
) -> tuple[str, str, str]:
    reason = block_reason_label(block_reason)
    description = (block_description or "").strip() or "Sem descrição"
    actor = (actor_name or "").strip() or "alguém"
    document = _format_document(document_number, series)
    supplier = (supplier_name or "").strip() or "—"
    branch = branch_label(branch_code)

    title = f"Pendência de NF atribuída a você — {reason}"

    detail_lines: list[tuple[str, str]] = [
        ("Pendência", reason),
        ("O que resolver", description),
        ("Nota", document),
        ("Fornecedor", supplier),
        ("Filial", branch),
    ]
    if amount is not None and str(amount).strip() != "":
        detail_lines.append(("Valor", _format_amount(amount)))
    issue = str(issue_date or "").strip()
    if issue:
        date_part = issue[:10]
        if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
            year, month, day = date_part.split("-")
            detail_lines.append(("Emissão", f"{day}/{month}/{year}"))
        else:
            detail_lines.append(("Emissão", issue))

    plain_details = "\n".join(f"{label}: {value}" for label, value in detail_lines)
    message = (
        f"{actor} registrou uma pendência e atribuiu a você a correção.\n\n"
        f"{plain_details}"
    )

    list_items = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(value)}</li>"
        for label, value in detail_lines
    )
    html_content = (
        f"<p><strong>{html.escape(actor)}</strong> registrou uma pendência "
        f"e atribuiu a você a correção:</p>"
        f'<span class="notification-note-bubble"><ul>{list_items}</ul></span>'
    )
    return title, message, html_content


def send_lnf_portal_notification(
    *,
    recipient_user_id: str,
    title: str,
    message: str,
    notification_type: str = "warning",
    action_label: str = "Abrir solicitação",
    action_target: str,
    dedupe_key: str,
    event_type: str,
    metadata: dict[str, Any] | None = None,
    html_content: str | None = None,
) -> bool:
    if not lnf_portal_notifications_enabled():
        return False

    if not recipient_user_id or recipient_user_id.strip() in {"", "unknown"}:
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
    payload: dict[str, Any] = {
        "userIds": [recipient_user_id.strip()],
        "title": title,
        "message": message,
        "type": notification_type,
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": action_label,
            "target": action_target,
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": event_type,
            "dedupeKey": dedupe_key,
            **(metadata or {}),
        },
    }
    if html_content and html_content.strip():
        payload["presentation"] = "html"
        payload["htmlContent"] = html_content.strip()

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                f"{base_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code in (200, 201, 202):
            return True
        body_preview = (response.text or "")[:500]
        logger.warning(
            "lnf_portal_notification_rejected status=%s event=%s user=%s body=%s",
            response.status_code,
            event_type,
            recipient_user_id,
            body_preview,
        )
    except Exception:
        logger.warning(
            "lnf_portal_notification_failed event=%s user=%s",
            event_type,
            recipient_user_id,
            exc_info=True,
        )
    return False


def notify_block_assignee(
    *,
    request: dict[str, Any],
    actor_user_id: str | None,
    actor_name: str | None,
) -> bool:
    recipient = str(request.get("assignee_user_id") or "").strip()
    if not should_notify_block_assignee(
        assignee_user_id=recipient,
        actor_user_id=actor_user_id,
    ):
        return False

    request_id = str(request.get("id") or "").strip()
    if not request_id:
        return False

    title, message, html_content = build_block_assigned_copy(
        actor_name=actor_name,
        block_reason=str(request.get("block_reason") or ""),
        block_description=str(request.get("block_description") or ""),
        document_number=str(request.get("document_number") or ""),
        series=str(request.get("series") or ""),
        supplier_name=str(request.get("supplier_name") or ""),
        branch_code=str(request.get("branch_code") or ""),
        amount=request.get("amount"),
        issue_date=str(request.get("issue_date") or ""),
    )

    return send_lnf_portal_notification(
        recipient_user_id=recipient,
        title=title,
        message=message,
        notification_type="warning",
        action_label="Abrir solicitação",
        action_target=request_portal_route(
            branch_code=str(request.get("branch_code") or ""),
            request_id=request_id,
        ),
        dedupe_key=block_assigned_dedupe_key(
            request_id=request_id,
            user_id=recipient,
        ),
        event_type=_EVENT_BLOCK_ASSIGNED,
        metadata={
            "requestId": request_id,
            "branchCode": str(request.get("branch_code") or ""),
            "blockReason": str(request.get("block_reason") or ""),
        },
        html_content=html_content,
    )
