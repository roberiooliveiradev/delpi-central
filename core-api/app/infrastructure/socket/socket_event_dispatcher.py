# app/infrastructure/socket/socket_event_dispatcher.py

from app.domain.ports.event_dispatcher_port import EventDispatcherPort
from app.domain.events.admin_events import AdminChangedEvent
from app.extensions.socket import socketio


class SocketIOEventDispatcher(EventDispatcherPort):

    def dispatch(self, event):

        if isinstance(event, AdminChangedEvent):
            payload = {
                "entity": event.entity,
                "action": event.action,
                "payload": event.payload,
            }

            if event.target_user_id:
                socketio.emit(
                    event.name,
                    payload,
                    room=str(event.target_user_id),
                    namespace="/",
                )
            else:
                socketio.emit(
                    event.name,
                    payload,
                    namespace="/",
                )