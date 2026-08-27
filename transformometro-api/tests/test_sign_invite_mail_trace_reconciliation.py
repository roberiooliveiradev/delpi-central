from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from tm_app.application.services.sign_invite_mail_trace_reconciliation_service import (
    SignInviteMailTraceReconciliationService,
    pick_best_trace_match,
    resolve_delivery_from_trace,
)
from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_BOUNCED,
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_UNKNOWN,
)


def test_resolve_delivery_from_trace_delivered_status():
    status, delivered_at = resolve_delivery_from_trace(
        trace={"status": "Delivered", "receivedDateTime": "2026-08-27T12:00:00Z"},
        details=[],
    )
    assert status == MAIL_DELIVERY_DELIVERED
    assert delivered_at is not None


def test_resolve_delivery_from_trace_bounced_from_details():
    status, _ = resolve_delivery_from_trace(
        trace={"status": "Pending"},
        details=[{"event": "Fail"}],
    )
    assert status == MAIL_DELIVERY_BOUNCED


def test_pick_best_trace_match_prefers_closest_received_time():
    sent_at = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    traces = [
        {
            "id": "far",
            "recipientAddress": "a@delpi.com.br",
            "receivedDateTime": "2026-08-27T11:00:00Z",
        },
        {
            "id": "near",
            "recipientAddress": "a@delpi.com.br",
            "receivedDateTime": "2026-08-27T12:02:00Z",
        },
    ]
    match = pick_best_trace_match(
        traces=traces,
        recipient="a@delpi.com.br",
        sent_at=sent_at,
    )
    assert match is not None
    assert match["id"] == "near"


def test_reconcile_invite_updates_delivered():
    repo = MagicMock()
    trace_client = MagicMock()
    sent_at = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    trace_client.list_message_traces.return_value = [
        {
            "id": "trace-1",
            "recipientAddress": "a@delpi.com.br",
            "status": "Delivered",
            "receivedDateTime": "2026-08-27T12:01:00Z",
        }
    ]
    trace_client.get_details_by_recipient.return_value = []

    service = SignInviteMailTraceReconciliationService(
        repo=repo,
        trace_client=trace_client,
        enabled=True,
    )
    updated = service.reconcile_invite(
        {
            "id": "inv-1",
            "mail_recipient": "a@delpi.com.br",
            "mail_sent_at": sent_at,
        }
    )

    assert updated is True
    repo.update_invite_mail_delivery_result.assert_called_once()
    kwargs = repo.update_invite_mail_delivery_result.call_args.kwargs
    assert kwargs["invite_id"] == "inv-1"
    assert kwargs["mail_delivery_status"] == MAIL_DELIVERY_DELIVERED
    assert kwargs["mail_trace_id"] == "trace-1"
