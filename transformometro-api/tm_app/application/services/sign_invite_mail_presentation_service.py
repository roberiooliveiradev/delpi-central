"""Monta contrato last_invite_mail para get_detail."""

from __future__ import annotations

from typing import Any

from tm_app.application.services.mail_delivery_content_service import (
    MailDeliveryContentService,
)
from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def build_last_invite_mail(invite: dict[str, Any] | None) -> dict[str, Any] | None:
    if not invite:
        return None
    send_status = str(invite.get("mail_send_status") or "").strip()
    delivery_status = str(invite.get("mail_delivery_status") or "").strip()
    return {
        "invite_id": str(invite.get("id") or ""),
        "template_key": invite.get("mail_template_key"),
        "recipient": invite.get("mail_recipient"),
        "send_status": send_status or None,
        "delivery_status": delivery_status or None,
        "sent_at": _serialize_datetime(invite.get("mail_sent_at")),
        "delivered_at": _serialize_datetime(invite.get("mail_delivered_at")),
        "last_error": invite.get("mail_last_error"),
        "send_status_label": MailDeliveryContentService.send_status_label(send_status),
        "delivery_status_label": MailDeliveryContentService.delivery_status_label(
            delivery_status
        ),
        "badge_hint": MailDeliveryContentService.badge_hint(
            send_status=send_status,
            delivery_status=delivery_status,
        ),
    }


def enrich_signers_with_last_invite_mail(
    *,
    repo: MeetingMinuteRepository,
    minute_id: str,
    signers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signer_ids = [str(item.get("id") or "") for item in signers if item.get("id")]
    mail_by_signer = repo.get_latest_invite_mail_by_signer_ids(
        minute_id=minute_id,
        signer_ids=signer_ids,
    )
    enriched: list[dict[str, Any]] = []
    for signer in signers:
        signer_id = str(signer.get("id") or "")
        enriched.append(
            {
                **signer,
                "last_invite_mail": build_last_invite_mail(mail_by_signer.get(signer_id)),
            }
        )
    return enriched
