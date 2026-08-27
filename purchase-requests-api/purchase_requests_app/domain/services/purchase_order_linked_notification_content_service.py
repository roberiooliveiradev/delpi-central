"""Declarative texts for purchase-order-linked-to-SC portal notifications."""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "purchase_order_linked_notification.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


class PurchaseOrderLinkedNotificationContentService:
    @classmethod
    def raw(cls) -> dict[str, Any]:
        return dict(_load())

    @classmethod
    def empty_value(cls) -> str:
        return str(_load().get("emptyValue") or "—").strip() or "—"

    @classmethod
    def category(cls) -> str:
        return str(_load().get("category") or "purchase_requests").strip()

    @classmethod
    def source_app(cls) -> str:
        return str(_load().get("sourceApp") or "purchase-requests").strip()

    @classmethod
    def event_type(cls) -> str:
        return str(_load().get("eventType") or "purchase_order_created").strip()

    @classmethod
    def notification_type(cls) -> str:
        return str(_load().get("type") or "info").strip() or "info"

    @classmethod
    def action_label(cls) -> str:
        return str(_load().get("actionLabel") or "Abrir solicitação").strip()

    @classmethod
    def core_permanent_rejection_substrings(cls) -> tuple[str, ...]:
        raw = _load().get("corePermanentRejectionSubstrings") or []
        if not isinstance(raw, list):
            return ()
        return tuple(
            str(item).strip().lower()
            for item in raw
            if str(item).strip()
        )

    @classmethod
    def format_delivery_date(cls, raw: str | None) -> str:
        value = (raw or "").strip()
        if not value:
            return cls.empty_value()
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(value[:10] if fmt == "%Y-%m-%d" else value[:8], fmt).strftime(
                    "%d/%m/%Y"
                )
            except ValueError:
                continue
        return value

    @classmethod
    def format_title(cls, *, order_number: str, request_number: str) -> str:
        template = str(_load().get("titleTemplate") or "Pedido {order} vinculado à SC {request}")
        return template.format(
            order=(order_number or "").strip() or cls.empty_value(),
            request=(request_number or "").strip() or cls.empty_value(),
        )

    @classmethod
    def format_message(
        cls,
        *,
        product_code: str,
        product_description: str | None,
        supplier_name: str | None,
        expected_delivery_date: str | None,
    ) -> str:
        template = str(
            _load().get("messageTemplate")
            or "Produto {product_code} — {product_description}\n"
            "Fornecedor {supplier} · Entrega prevista {delivery_date}"
        )
        empty = cls.empty_value()
        return template.format(
            product_code=(product_code or "").strip() or empty,
            product_description=(product_description or "").strip() or empty,
            supplier=(supplier_name or "").strip() or empty,
            delivery_date=cls.format_delivery_date(expected_delivery_date),
        )

    @classmethod
    def build_deep_link_path(cls, *, branch: str, request_number: str) -> str:
        base = str(_load().get("deepLinkPath") or "/apps/purchase-requests").strip()
        query = urlencode(
            {
                "branch": (branch or "").strip(),
                "request_number": (request_number or "").strip(),
            }
        )
        return f"{base}?{query}" if query else base
