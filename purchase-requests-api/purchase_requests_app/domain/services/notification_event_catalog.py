from __future__ import annotations

from typing import Any

NOTIFICATION_EVENT_KEYS = frozenset(
    {
        "purchase_order_created",
        "purchase_receipt_recorded",
        "purchase_request_approved",
        "purchase_delivery_overdue",
    }
)

NOTIFICATION_EVENTS: list[dict[str, Any]] = [
    {
        "event_key": "purchase_order_created",
        "label": "Pedido de compra emitido",
        "description": "Quando um pedido de compra é vinculado à linha da solicitação.",
        "sort_order": 10,
    },
    {
        "event_key": "purchase_receipt_recorded",
        "label": "Recebimento registrado",
        "description": "Quando há entrada de nota fiscal vinculada ao pedido.",
        "sort_order": 20,
    },
    {
        "event_key": "purchase_request_approved",
        "label": "Solicitação aprovada",
        "description": "Quando a solicitação é liberada no fluxo de aprovação.",
        "sort_order": 30,
    },
    {
        "event_key": "purchase_delivery_overdue",
        "label": "Entrega atrasada",
        "description": "Quando o prazo de entrega vence sem recebimento completo.",
        "sort_order": 40,
    },
]


def list_notification_events() -> list[dict[str, Any]]:
    return sorted(NOTIFICATION_EVENTS, key=lambda item: item.get("sort_order", 0))


def is_valid_notification_event_key(event_key: str) -> bool:
    return event_key in NOTIFICATION_EVENT_KEYS
