# app/domain/events/admin_events.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class DomainEvent:
    name: str


@dataclass
class AdminChangedEvent(DomainEvent):
    entity: str
    action: str
    payload: dict
    target_user_id: Optional[str] = None

    def __init__(self, entity: str, action: str, payload: dict, target_user_id: Optional[str] = None):
        super().__init__(name="admin.changed")
        self.entity = entity
        self.action = action
        self.payload = payload
        self.target_user_id = target_user_id