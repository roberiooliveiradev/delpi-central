# app/domain/ports/event_dispatcher_port.py

from typing import Protocol
from app.domain.events.admin_events import DomainEvent


class EventDispatcherPort(Protocol):
    def dispatch(self, event: DomainEvent) -> None:
        ...