# app/application/event_handlers/admin_audit_event_handler.py

from __future__ import annotations

from uuid import UUID

from app.domain.events.admin_events import AdminChangedEvent


def _resolve_entity_id(event: AdminChangedEvent) -> str | None:
    payload = event.payload or {}

    for key in ("pluginId", "appId", "id"):
        value = payload.get(key)
        if value:
            return str(value)

    return None


class AdminAuditEventHandler:

    def __init__(self, uow):
        self.uow = uow

    def handle(self, event: AdminChangedEvent) -> None:
        if event.entity not in ("plugins", "apps"):
            return

        actor_id = event.actor_user_id or event.target_user_id
        user_id = None

        if actor_id:
            try:
                user_id = UUID(str(actor_id))
            except (TypeError, ValueError):
                user_id = None

        self.uow.audits.log(
            {
                "user_id": user_id,
                "action": event.action,
                "entity_type": event.entity,
                "entity_id": _resolve_entity_id(event),
                "payload": event.payload,
            }
        )
