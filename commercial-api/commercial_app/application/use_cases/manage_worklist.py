from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from commercial_app.domain.entities.task import CommercialActivity, CommercialTask
from commercial_app.domain.ports.customer_avatar_repository_port import AuditLogRepositoryPort
from commercial_app.domain.ports.task_repository_port import (
    ActivityRepositoryPort,
    TaskRepositoryPort,
)

WorklistBucket = Literal["overdue", "today", "later", "open"]


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    description: str | None = None
    task_type: str = "follow_up"
    priority: str = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None


@dataclass(frozen=True)
class CreateActivityInput:
    activity_type: str
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    task_id: UUID | None = None


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_today_utc() -> datetime:
    return _start_of_today_utc().replace(hour=23, minute=59, second=59, microsecond=999999)


class ManageWorklistUseCase:
    def __init__(
        self,
        *,
        task_repository: TaskRepositoryPort,
        activity_repository: ActivityRepositoryPort,
        audit_repository: AuditLogRepositoryPort | None = None,
    ) -> None:
        self._tasks = task_repository
        self._activities = activity_repository
        self._audit = audit_repository

    def get_worklist(self, *, user_id: str) -> dict[str, Any]:
        open_tasks = list(self._tasks.list_for_assignee(assignee_user_id=user_id, status="open"))
        start = _start_of_today_utc()
        end = _end_of_today_utc()
        overdue: list[dict[str, Any]] = []
        today: list[dict[str, Any]] = []
        later: list[dict[str, Any]] = []
        for task in open_tasks:
            payload = task.to_dict()
            due = task.due_at
            if due is not None and due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due is not None and due < start:
                payload["bucket"] = "overdue"
                overdue.append(payload)
            elif due is not None and due <= end:
                payload["bucket"] = "today"
                today.append(payload)
            else:
                payload["bucket"] = "later"
                later.append(payload)
        return {
            "overdue": overdue,
            "today": today,
            "later": later,
            "counts": {
                "overdue": len(overdue),
                "today": len(today),
                "later": len(later),
                "open": len(open_tasks),
            },
        }

    def list_tasks(self, *, user_id: str, status: str | None = "open") -> list[CommercialTask]:
        return list(self._tasks.list_for_assignee(assignee_user_id=user_id, status=status))

    def create_task(self, *, user_id: str, data: CreateTaskInput) -> CommercialTask:
        title = (data.title or "").strip()
        if not title:
            raise ValueError("Título da tarefa é obrigatório.")
        task_type = (data.task_type or "follow_up").strip() or "follow_up"
        priority = (data.priority or "normal").strip() or "normal"
        description = (data.description or "").strip() or None
        task = self._tasks.create(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_at=data.due_at,
            assignee_user_id=user_id,
            created_by_user_id=user_id,
            customer_code=(data.customer_code or None),
            customer_store=(data.customer_store or None),
        )
        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.task.created",
                entity_type="task",
                entity_id=str(task.id),
                payload={"title": task.title},
            )
        self._activities.create(
            activity_type="system",
            subject=f"Tarefa criada: {task.title}",
            body=description,
            occurred_at=None,
            actor_user_id=user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            task_id=task.id,
        )
        return task

    def complete_task(self, *, user_id: str, task_id: UUID) -> CommercialTask:
        task = self._tasks.complete(task_id=task_id, actor_user_id=user_id)
        if task is None:
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.task.completed",
                entity_type="task",
                entity_id=str(task.id),
                payload={},
            )
        self._activities.create(
            activity_type="system",
            subject=f"Tarefa concluída: {task.title}",
            body=None,
            occurred_at=None,
            actor_user_id=user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            task_id=task.id,
        )
        return task

    def defer_task(self, *, user_id: str, task_id: UUID, due_at: datetime) -> CommercialTask:
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        task = self._tasks.update_due_at(
            task_id=task_id, actor_user_id=user_id, due_at=due_at
        )
        if task is None:
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.task.deferred",
                entity_type="task",
                entity_id=str(task.id),
                payload={"due_at": due_at.isoformat()},
            )
        self._activities.create(
            activity_type="system",
            subject=f"Tarefa adiada: {task.title}",
            body=None,
            occurred_at=None,
            actor_user_id=user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            task_id=task.id,
        )
        return task

    def create_activity(self, *, user_id: str, data: CreateActivityInput) -> CommercialActivity:
        activity_type = (data.activity_type or "").strip()
        if not activity_type:
            raise ValueError("Tipo de atividade é obrigatório.")
        activity = self._activities.create(
            activity_type=activity_type,
            subject=(data.subject or None),
            body=(data.body or None),
            occurred_at=data.occurred_at,
            actor_user_id=user_id,
            customer_code=(data.customer_code or None),
            customer_store=(data.customer_store or None),
            task_id=data.task_id,
        )
        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.activity.created",
                entity_type="activity",
                entity_id=str(activity.id),
                payload={"activity_type": activity.activity_type},
            )
        return activity

    def list_customer_activities(
        self,
        *,
        customer_code: str,
        customer_store: str,
        limit: int = 50,
    ) -> list[CommercialActivity]:
        return list(
            self._activities.list_for_customer(
                customer_code=customer_code,
                customer_store=customer_store,
                limit=limit,
            )
        )
