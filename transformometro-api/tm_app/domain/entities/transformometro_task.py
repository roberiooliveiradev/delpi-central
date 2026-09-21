from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

TaskStatus = Literal["pending", "completed", "cancelled"]
TASK_STATUSES = ("pending", "completed", "cancelled")


@dataclass(frozen=True)
class TransformometroTask:
    id: str
    title: str
    description: str | None
    status: TaskStatus
    assignee_user_id: str
    created_by_user_id: str
    due_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    completed_at: datetime | None
    source_interaction_message_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assignee_user_id": self.assignee_user_id,
            "created_by_user_id": self.created_by_user_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "source_interaction_message_id": self.source_interaction_message_id,
        }
