"""Confirma entrega de convite quando o signatário abre o magic link ou assina."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from cipa_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_SEND_ACCEPTED,
)


class SignInviteMailEngagementRepository(Protocol):
    def confirm_invite_mail_delivered_from_engagement(
        self,
        invite_id: str,
        *,
        delivered_at: datetime,
    ) -> dict[str, Any] | None: ...


class SignInviteMailEngagementService:
    def __init__(self, repo: SignInviteMailEngagementRepository) -> None:
        self.repo = repo

    def confirm_delivered_if_pending(self, invite_id: str) -> bool:
        normalized = str(invite_id or "").strip()
        if not normalized:
            return False
        row = self.repo.confirm_invite_mail_delivered_from_engagement(
            normalized,
            delivered_at=datetime.now(timezone.utc),
        )
        return row is not None


def invite_accepts_engagement_delivery(invite: dict[str, Any] | None) -> bool:
    if not invite:
        return False
    return (
        str(invite.get("mail_send_status") or "") == MAIL_SEND_ACCEPTED
        and str(invite.get("mail_delivery_status") or "") == MAIL_DELIVERY_TRACE_PENDING
    )


__all__ = [
    "SignInviteMailEngagementService",
    "invite_accepts_engagement_delivery",
    "MAIL_DELIVERY_DELIVERED",
]
