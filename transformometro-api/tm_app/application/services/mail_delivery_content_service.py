"""Loader do catálogo PT-BR de status de entrega de e-mail de convites."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tm_app.domain.sign_invite_mail_status import (
    MAIL_DELIVERY_BOUNCED,
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_NOT_APPLICABLE,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_DELIVERY_UNKNOWN,
    MAIL_SEND_ACCEPTED,
    MAIL_SEND_FAILED,
    MAIL_SEND_PENDING,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
    MAIL_SEND_SKIPPED_MAIL_DISABLED,
    MAIL_SEND_SKIPPED_NO_EMAIL,
)

_CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "pt-BR" / "mail_delivery.json"
)

_ALL_SEND_STATUSES = (
    MAIL_SEND_PENDING,
    MAIL_SEND_SKIPPED_NO_EMAIL,
    MAIL_SEND_SKIPPED_MAIL_DISABLED,
    MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
    MAIL_SEND_FAILED,
    MAIL_SEND_ACCEPTED,
)

_ALL_DELIVERY_STATUSES = (
    MAIL_DELIVERY_NOT_APPLICABLE,
    MAIL_DELIVERY_TRACE_PENDING,
    MAIL_DELIVERY_DELIVERED,
    MAIL_DELIVERY_BOUNCED,
    MAIL_DELIVERY_UNKNOWN,
)


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload if isinstance(payload, dict) else {}


class MailDeliveryContentService:
    @staticmethod
    def send_status_label(status: str) -> str:
        labels = _content().get("sendStatusLabels") or {}
        key = str(status or "").strip()
        value = labels.get(key) if isinstance(labels, dict) else None
        return str(value or key or MAIL_SEND_PENDING)

    @staticmethod
    def delivery_status_label(status: str) -> str:
        labels = _content().get("deliveryStatusLabels") or {}
        key = str(status or "").strip()
        value = labels.get(key) if isinstance(labels, dict) else None
        return str(value or key or MAIL_DELIVERY_NOT_APPLICABLE)

    @staticmethod
    def badge_hint(*, send_status: str, delivery_status: str) -> str:
        hints = _content().get("badgeHints") or {}
        if not isinstance(hints, dict):
            return ""
        send = str(send_status or "").strip()
        delivery = str(delivery_status or "").strip()
        if send == MAIL_SEND_ACCEPTED and delivery == MAIL_DELIVERY_TRACE_PENDING:
            return str(hints.get("accepted_trace_pending") or "")
        if send == MAIL_SEND_ACCEPTED and delivery == MAIL_DELIVERY_DELIVERED:
            return str(hints.get("accepted_delivered") or "")
        if send in {
            MAIL_SEND_SKIPPED_NO_EMAIL,
            MAIL_SEND_SKIPPED_MAIL_DISABLED,
            MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED,
            MAIL_SEND_FAILED,
        }:
            return str(hints.get(send) or "")
        if delivery in {MAIL_DELIVERY_BOUNCED, MAIL_DELIVERY_UNKNOWN}:
            return str(hints.get(delivery) or "")
        return ""

    @staticmethod
    def all_send_statuses() -> tuple[str, ...]:
        return _ALL_SEND_STATUSES

    @staticmethod
    def all_delivery_statuses() -> tuple[str, ...]:
        return _ALL_DELIVERY_STATUSES
