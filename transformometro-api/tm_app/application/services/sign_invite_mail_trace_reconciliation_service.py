"""Reconcilia entrega real de e-mail de convites via Microsoft Graph Message Trace."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from tm_app.application.services.tm_sign_pending_mail_service import build_graph_mail_client
from tm_app.config import settings
from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_BOUNCED,
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_DELIVERY_UNKNOWN,
)
from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)
from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
)
from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_message_trace_client import (
    MicrosoftGraphMessageTraceClient,
)

logger = logging.getLogger("transformometro.mail.trace")

_TRACE_WINDOW = timedelta(minutes=15)
_MAX_TRACE_AGE = timedelta(days=10)
_BOUNCED_TRACE_STATUSES = {"failed", "filteredasspam", "quarantined"}
_DELIVERED_TRACE_STATUSES = {"delivered"}
_DELIVERED_DETAIL_EVENTS = {"deliver", "delivered"}
_BOUNCED_DETAIL_EVENTS = {"fail", "failed", "expanded"}


def _parse_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _trace_id(row: dict[str, Any]) -> str:
    for key in ("id", "messageTraceId"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _trace_recipient(row: dict[str, Any]) -> str:
    return str(row.get("recipientAddress") or row.get("recipient") or "").strip().lower()


def resolve_delivery_from_trace(
    *,
    trace: dict[str, Any],
    details: list[dict[str, Any]],
) -> tuple[str, datetime | None]:
    status = str(trace.get("status") or "").strip().lower()
    if status in _DELIVERED_TRACE_STATUSES:
        return MAIL_DELIVERY_DELIVERED, _parse_datetime(trace.get("receivedDateTime"))
    if status in _BOUNCED_TRACE_STATUSES:
        return MAIL_DELIVERY_BOUNCED, None

    for event in details:
        event_type = str(event.get("event") or event.get("eventType") or "").strip().lower()
        event_time = _parse_datetime(event.get("date") or event.get("receivedDateTime"))
        if event_type in _DELIVERED_DETAIL_EVENTS:
            return MAIL_DELIVERY_DELIVERED, event_time
        if event_type in _BOUNCED_DETAIL_EVENTS:
            return MAIL_DELIVERY_BOUNCED, event_time

    if status:
        return MAIL_DELIVERY_UNKNOWN, None
    return MAIL_DELIVERY_UNKNOWN, None


def pick_best_trace_match(
    *,
    traces: list[dict[str, Any]],
    recipient: str,
    sent_at: datetime,
) -> dict[str, Any] | None:
    target = recipient.strip().lower()
    candidates: list[tuple[timedelta, dict[str, Any]]] = []
    for trace in traces:
        if _trace_recipient(trace) != target:
            continue
        received = _parse_datetime(trace.get("receivedDateTime"))
        if received is None:
            candidates.append((timedelta.max, trace))
            continue
        candidates.append((abs(received - sent_at), trace))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


class SignInviteMailTraceReconciliationService:
    def __init__(
        self,
        *,
        repo: MeetingMinuteRepository | None = None,
        trace_client: MicrosoftGraphMessageTraceClient | None = None,
        enabled: bool | None = None,
        batch_limit: int | None = None,
    ) -> None:
        self.repo = repo or MeetingMinuteRepository()
        if trace_client is not None:
            self.trace_client = trace_client
        else:
            mail_client = build_graph_mail_client()
            self.trace_client = MicrosoftGraphMessageTraceClient(
                get_access_token=mail_client.get_access_token,
                timeout_seconds=float(settings.TM_GRAPH_HTTP_TIMEOUT_SECONDS or "30"),
            )
        self.enabled = (
            settings.TM_SIGN_INVITE_MAIL_TRACE_ENABLED
            if enabled is None
            else enabled
        )
        self.batch_limit = (
            int(settings.TM_SIGN_INVITE_MAIL_TRACE_BATCH_LIMIT or "50")
            if batch_limit is None
            else batch_limit
        )

    def execute(self) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "processed": 0, "updated": 0}

        try:
            build_graph_mail_client().ensure_auth_configured()
        except GraphMailError:
            logger.warning("tm_mail_trace_skipped_graph_not_configured")
            return {"enabled": True, "processed": 0, "updated": 0, "graph_unconfigured": True}

        since = datetime.now(timezone.utc) - _MAX_TRACE_AGE
        invites = self.repo.list_invites_pending_trace(
            since=since,
            limit=self.batch_limit,
        )
        updated = 0
        for invite in invites:
            if self.reconcile_invite(invite):
                updated += 1
        return {"enabled": True, "processed": len(invites), "updated": updated}

    def reconcile_invite(self, invite: dict[str, Any]) -> bool:
        invite_id = str(invite.get("id") or "").strip()
        recipient = str(invite.get("mail_recipient") or "").strip()
        sent_at = _parse_datetime(invite.get("mail_sent_at"))
        if not invite_id or not recipient or sent_at is None:
            return False

        now = datetime.now(timezone.utc)
        if sent_at + _MAX_TRACE_AGE < now:
            self.repo.update_invite_mail_delivery_result(
                invite_id=invite_id,
                mail_delivery_status=MAIL_DELIVERY_UNKNOWN,
                mail_last_error="message trace window expired",
            )
            return True

        window_start = sent_at - _TRACE_WINDOW
        window_end = sent_at + _TRACE_WINDOW
        try:
            traces = self.trace_client.list_message_traces(
                start=window_start,
                end=window_end,
                recipient=recipient,
            )
        except GraphMailError as exc:
            logger.warning(
                "tm_mail_trace_query_failed invite=%s error=%s",
                invite_id,
                str(exc)[:200],
            )
            return False

        match = pick_best_trace_match(
            traces=traces,
            recipient=recipient,
            sent_at=sent_at,
        )
        if match is None:
            return False

        trace_key = _trace_id(match)
        details: list[dict[str, Any]] = []
        if trace_key:
            try:
                details = self.trace_client.get_details_by_recipient(trace_key)
            except GraphMailError as exc:
                logger.warning(
                    "tm_mail_trace_details_failed invite=%s trace=%s error=%s",
                    invite_id,
                    trace_key,
                    str(exc)[:200],
                )

        delivery_status, delivered_at = resolve_delivery_from_trace(
            trace=match,
            details=details,
        )
        if delivery_status == MAIL_DELIVERY_TRACE_PENDING:
            delivery_status = MAIL_DELIVERY_UNKNOWN

        self.repo.update_invite_mail_delivery_result(
            invite_id=invite_id,
            mail_delivery_status=delivery_status,
            mail_delivered_at=delivered_at,
            mail_trace_id=trace_key or None,
        )
        return True
