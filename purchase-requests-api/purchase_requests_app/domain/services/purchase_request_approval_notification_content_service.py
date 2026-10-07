"""Declarative texts for SC approval/rejection portal notifications."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "pt-BR"


@lru_cache(maxsize=2)
def _load(filename: str) -> dict[str, Any]:
    with (_CONTENT_DIR / filename).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


class _BaseRequestApprovalContent:
    _filename = ""

    @classmethod
    def _payload(cls) -> dict[str, Any]:
        return _load(cls._filename)

    @classmethod
    def raw(cls) -> dict[str, Any]:
        return dict(cls._payload())

    @classmethod
    def category(cls) -> str:
        return str(cls._payload().get("category") or "purchase_requests").strip()

    @classmethod
    def source_app(cls) -> str:
        return str(cls._payload().get("sourceApp") or "purchase-requests").strip()

    @classmethod
    def event_type(cls) -> str:
        return str(cls._payload().get("eventType") or "").strip()

    @classmethod
    def notification_type(cls) -> str:
        return str(cls._payload().get("type") or "info").strip() or "info"

    @classmethod
    def action_label(cls) -> str:
        return str(cls._payload().get("actionLabel") or "Ver solicitação").strip()

    @classmethod
    def core_permanent_rejection_substrings(cls) -> tuple[str, ...]:
        raw = cls._payload().get("corePermanentRejectionSubstrings") or []
        if not isinstance(raw, list):
            return ()
        return tuple(
            str(item).strip().lower() for item in raw if str(item).strip()
        )

    @classmethod
    def format_title(cls, *, request_number: str) -> str:
        template = str(cls._payload().get("titleTemplate") or "Solicitação {request}")
        return template.format(request=(request_number or "").strip() or "—")

    @classmethod
    def format_message(
        cls,
        *,
        request_number: str,
        approver_name: str | None,
    ) -> str:
        request = (request_number or "").strip() or "—"
        approver = (approver_name or "").strip()
        if approver:
            template = str(cls._payload().get("messageTemplate") or "")
            return template.format(request=request, approver=approver)
        template = str(
            cls._payload().get("messageTemplateNoApprover")
            or cls._payload().get("messageTemplate")
            or ""
        )
        return template.format(request=request, approver=approver)

    @classmethod
    def build_deep_link_path(cls, *, branch: str, request_number: str) -> str:
        base = str(cls._payload().get("deepLinkPath") or "/apps/purchase-requests").strip()
        query = urlencode(
            {
                "branch": (branch or "").strip(),
                "request_number": (request_number or "").strip(),
            }
        )
        return f"{base}?{query}" if query else base


class PurchaseRequestApprovedNotificationContentService(_BaseRequestApprovalContent):
    _filename = "purchase_request_approved_notification.json"


class PurchaseRequestRejectedNotificationContentService(_BaseRequestApprovalContent):
    _filename = "purchase_request_rejected_notification.json"
