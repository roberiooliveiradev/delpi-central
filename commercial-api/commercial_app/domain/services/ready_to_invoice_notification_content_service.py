"""Content loader for ready-to-invoice notification settings."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "ready_to_invoice_notification.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


class ReadyToInvoiceNotificationContentService:
    """Declarative settings for ready-to-invoice detection / notify."""

    @classmethod
    def raw(cls) -> dict[str, Any]:
        return dict(_load())

    @classmethod
    def checkpoint_source_key(cls) -> str:
        value = str(_load().get("checkpointSourceKey") or "").strip()
        return value or "commercial.open_orders.ready_to_invoice"

    @classmethod
    def board_deep_link_path(cls) -> str:
        value = str(_load().get("boardDeepLinkPath") or "").strip()
        return value or "/apps/commercial/open-orders?view=board&stage=ready_to_invoice"

    @classmethod
    def event_type(cls) -> str:
        value = str(_load().get("eventType") or "").strip()
        return value or "commercial.order.ready_to_invoice"

    @classmethod
    def aggregate_type(cls) -> str:
        value = str(_load().get("aggregateType") or "").strip()
        return value or "open_order_line"

    @classmethod
    def billing_user_ids(cls) -> tuple[str, ...]:
        raw = _load().get("billingUserIds")
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def billing_permission_codes(cls) -> tuple[str, ...]:
        raw = _load().get("billingPermissionCodes")
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def notification_block(cls) -> dict[str, Any]:
        block = _load().get("notification")
        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def format_message(cls, *, pedido: str, linha: str, cliente: str) -> str:
        block = cls.notification_block()
        template = str(block.get("messageTemplate") or "").strip()
        if not template:
            template = (
                "A linha {pedido}/{linha} do cliente {cliente} "
                "entrou em Pronto para faturar."
            )
        return template.format(pedido=pedido, linha=linha, cliente=cliente)
