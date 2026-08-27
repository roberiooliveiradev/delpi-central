from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from cipa_app.application.services.sign_invite_mail_engagement_service import (
    SignInviteMailEngagementService,
    invite_accepts_engagement_delivery,
)
from cipa_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_FAILED,
)


def test_invite_accepts_engagement_delivery_only_trace_pending_accepted():
    assert invite_accepts_engagement_delivery(
        {
            "mail_send_status": MAIL_SEND_ACCEPTED,
            "mail_delivery_status": MAIL_DELIVERY_TRACE_PENDING,
        }
    )
    assert not invite_accepts_engagement_delivery(
        {
            "mail_send_status": MAIL_SEND_ACCEPTED,
            "mail_delivery_status": MAIL_DELIVERY_DELIVERED,
        }
    )
    assert not invite_accepts_engagement_delivery(
        {
            "mail_send_status": MAIL_SEND_FAILED,
            "mail_delivery_status": MAIL_DELIVERY_TRACE_PENDING,
        }
    )
    assert not invite_accepts_engagement_delivery(None)


def test_confirm_delivered_if_pending_updates_repo():
    repo = MagicMock()
    repo.confirm_invite_mail_delivered_from_engagement.return_value = {
        "id": "inv1",
        "mail_delivery_status": MAIL_DELIVERY_DELIVERED,
    }
    service = SignInviteMailEngagementService(repo)

    assert service.confirm_delivered_if_pending("inv1") is True
    repo.confirm_invite_mail_delivered_from_engagement.assert_called_once()
    _, kwargs = repo.confirm_invite_mail_delivered_from_engagement.call_args
    assert kwargs["delivered_at"].tzinfo == timezone.utc


def test_confirm_delivered_if_pending_idempotent_when_not_pending():
    repo = MagicMock()
    repo.confirm_invite_mail_delivered_from_engagement.return_value = None
    service = SignInviteMailEngagementService(repo)

    assert service.confirm_delivered_if_pending("inv1") is False
    assert service.confirm_delivered_if_pending("") is False
    repo.confirm_invite_mail_delivered_from_engagement.assert_called_once_with(
        "inv1",
        delivered_at=repo.confirm_invite_mail_delivered_from_engagement.call_args.kwargs[
            "delivered_at"
        ],
    )


def test_confirm_delivered_if_pending_passes_timestamp():
    repo = MagicMock()
    fixed = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    repo.confirm_invite_mail_delivered_from_engagement.return_value = {"id": "inv1"}
    service = SignInviteMailEngagementService(repo)

    service.confirm_delivered_if_pending("inv1")
    delivered_at = repo.confirm_invite_mail_delivered_from_engagement.call_args.kwargs[
        "delivered_at"
    ]
    assert isinstance(delivered_at, datetime)
    assert delivered_at.tzinfo == timezone.utc
