# app/domain/ports/admin_event_publisher.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AdminChangedEvent:
    entity: str
    action: str
    payload: dict | None = None


class AdminEventPublisher(ABC):

    @abstractmethod
    def publish(self, event: AdminChangedEvent) -> None:
        pass