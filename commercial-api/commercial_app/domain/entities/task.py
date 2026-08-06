from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class CommercialTask:
    id: UUID
    title: str
    description: str | None
    task_type: str
    status: str
    priority: str
    due_at: datetime | None
    completed_at: datetime | None
    assignee_user_id: str
    created_by_user_id: str
    customer_code: str | None
    customer_store: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assignee_user_id": self.assignee_user_id,
            "created_by_user_id": self.created_by_user_id,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(frozen=True)
class CommercialActivity:
    id: UUID
    activity_type: str
    subject: str | None
    body: str | None
    occurred_at: datetime
    actor_user_id: str
    customer_code: str | None
    customer_store: str | None
    task_id: UUID | None
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "activity_type": self.activity_type,
            "subject": self.subject,
            "body": self.body,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "actor_user_id": self.actor_user_id,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "task_id": str(self.task_id) if self.task_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
