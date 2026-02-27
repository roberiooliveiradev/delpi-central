# app/infrastructure/events/socket_admin_event_publisher.py

from app.domain.ports.admin_event_publicher import (
    AdminEventPublisher,
    AdminChangedEvent,
)
from app.extensions.socket import socketio


class SocketAdminEventPublisher(AdminEventPublisher):

    def publish(self, event: AdminChangedEvent) -> None:
        payload = {
            "entity": event.entity,
            "action": event.action,
            "payload": event.payload or {},
        }

        # 🎯 Se o evento tiver target_user_id → envia apenas para ele
        if getattr(event, "target_user_id", None):
            socketio.emit(
                "admin.changed",
                payload,
                room=str(event.target_user_id),
                namespace="/",
            )
        else:
            # 🔵 Broadcast global
            socketio.emit(
                "admin.changed",
                payload,
                namespace="/",
            )