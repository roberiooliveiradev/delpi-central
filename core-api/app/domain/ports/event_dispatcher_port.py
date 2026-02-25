# app/domain/ports/event_dispatcher_port.py

from typing import Protocol, Optional


class EventDispatcherPort(Protocol):

    def emit(self, event: str, payload: dict, room: Optional[str] = None) -> None:
        ...