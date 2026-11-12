"""Fan-out de eventos leves da Engineering API — ENG-REALTIME-01.

Adapter ``RealtimePublisher`` → hub WebSocket. Traduz o contrato neutro
``RealtimeEvent`` em rooms e envelope ``engineering.resource.changed``.

Rooms:
- ``user:{sub}`` — destinatários explícitos (solicitante/atribuído);
- ``queue:{domain}`` — fila do domínio (ex.: analistas PRC);
- ``res:{domain}:{resourceId}`` — assinatura de caso aberto.
"""

from __future__ import annotations

import logging
from typing import Any

from engineering_app.application.ports.realtime import RealtimeEvent
from engineering_app.application.services.engineering_realtime_hub import (
    engineering_realtime_hub,
)
from engineering_app.config import settings

logger = logging.getLogger(__name__)

EVENT_TYPE_CHANGED = "engineering.resource.changed"


def user_room(user_id: str) -> str:
    return f"user:{str(user_id or '').strip()}"


def queue_room(domain: str) -> str:
    return f"queue:{str(domain or '').strip()}"


def resource_room(domain: str, resource_id: str) -> str:
    return f"res:{str(domain or '').strip()}:{str(resource_id or '').strip()}"


def realtime_enabled() -> bool:
    return bool(settings.ENG_REALTIME_ENABLED)


def event_payload(event: RealtimeEvent) -> dict[str, Any]:
    """Envelope leve — IDs/versão/motivo apenas (nunca ficha, fornecedor,
    documento, token ou conteúdo técnico)."""
    return {
        "type": EVENT_TYPE_CHANGED,
        "domain": event.domain,
        "resourceType": event.resource_type,
        "resourceId": event.resource_id,
        "reason": event.reason,
        "version": event.version,
        "status": event.status,
        "eventId": event.event_id,
        "occurredAt": event.occurred_at,
        "actorUserId": event.actor_user_id,
        "actorClientId": event.actor_client_id,
    }


def event_rooms(event: RealtimeEvent) -> list[str]:
    rooms: list[str] = []
    seen: set[str] = set()

    def add(key: str | None) -> None:
        item = str(key or "").strip()
        if not item or item in seen:
            return
        seen.add(item)
        rooms.append(item)

    add(resource_room(event.domain, event.resource_id))
    for uid in event.recipient_user_ids:
        add(user_room(uid))
    if event.queue_impact:
        add(queue_room(event.domain))
    return rooms


class EngineeringRealtimeNotifier:
    """Publisher pós-commit — best-effort, nunca falha a mutação."""

    def publish(self, event: RealtimeEvent) -> None:
        if not realtime_enabled():
            return
        try:
            engineering_realtime_hub.schedule_broadcast_rooms(
                event_rooms(event), event_payload(event)
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "engineering_realtime_schedule_failed domain=%s "
                "resource_id=%s reason=%s",
                event.domain,
                event.resource_id,
                event.reason,
            )


engineering_realtime_notifier = EngineeringRealtimeNotifier()
