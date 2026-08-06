from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateTaskBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    task_type: Literal["follow_up", "call", "todo", "email", "visit", "internal", "other"] = "follow_up"
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    assignee_user_id: str | None = Field(
        default=None,
        description="Responsável (sub Minha Delpi). Default = caller. Outro usuário exige manage de carteiras.",
    )


class CreateActivityBody(BaseModel):
    activity_type: Literal["call", "email", "meeting", "visit", "note", "system"]
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    task_id: UUID | None = None


class DeferTaskBody(BaseModel):
    """Adia a tarefa para a data/hora informada (padrão CRM)."""

    due_at: datetime


class ReassignTaskBody(BaseModel):
    assignee_user_id: str = Field(..., min_length=1, max_length=200)
