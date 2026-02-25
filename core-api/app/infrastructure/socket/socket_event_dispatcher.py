# app/infrastructure/socket/socket_event_dispatcher.py

from app.domain.ports.event_dispatcher_port import EventDispatcherPort
from app.extensions.socket import socketio


class SocketIOEventDispatcher(EventDispatcherPort):

    def emit(self, event: str, payload: dict, room: str | None = None) -> None:
        socketio.emit(event, payload, room=room)