from __future__ import annotations

from datetime import date, datetime
from typing import Any, Sequence
from uuid import uuid4

from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask
from tm_app.domain.ports.task_repository_port import TaskRepositoryPort
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_S = "transformometro"


def _row_to_task(row: dict[str, Any]) -> TransformometroTask:
    due = row.get("due_date")
    if isinstance(due, datetime):
        due = due.date()
    return TransformometroTask(
        id=str(row["id"]),
        title=str(row["title"]),
        description=row.get("description"),
        status=row["status"],
        assignee_user_id=str(row["assignee_user_id"]),
        created_by_user_id=str(row["created_by_user_id"]),
        due_date=due,
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        completed_at=row.get("completed_at"),
    )


class TaskRepository(PluginBaseRepository, TaskRepositoryPort):
    def create(
        self,
        *,
        title: str,
        description: str | None,
        assignee_user_id: str,
        created_by_user_id: str,
        due_date: date | None,
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_tasks
                (title, description, status, assignee_user_id, created_by_user_id, due_date)
                VALUES (%s, %s, 'pending', %s::uuid, %s::uuid, %s)
                RETURNING *""",
            (title, description, assignee_user_id, created_by_user_id, due_date),
        )
        if row is None:
            raise RuntimeError("Falha ao criar a tarefa.")
        return _row_to_task(row)

    def get(self, task_id: str) -> TransformometroTask | None:
        row = self.fetch_one(f"SELECT * FROM {_S}.tm_tasks WHERE id = %s::uuid", (task_id,))
        return _row_to_task(row) if row else None

    def update(
        self,
        task_id: str,
        *,
        title: str,
        description: str | None,
        assignee_user_id: str,
        due_date: date | None,
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET title = %s, description = %s, assignee_user_id = %s::uuid,
                    due_date = %s, updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                RETURNING *""",
            (title, description, assignee_user_id, due_date, task_id),
        )
        if row is None:
            raise LookupError("Tarefa não encontrada.")
        return _row_to_task(row)

    def complete(self, task_id: str) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET status = 'completed', completed_at = NOW(), updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                RETURNING *""",
            (task_id,),
        )
        if row is None:
            raise LookupError("Tarefa não encontrada.")
        return _row_to_task(row)

    def cancel(self, task_id: str) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET status = 'cancelled', updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                RETURNING *""",
            (task_id,),
        )
        if row is None:
            raise LookupError("Tarefa não encontrada.")
        return _row_to_task(row)

    def list_for_assignee(
        self,
        assignee_user_id: str,
        *,
        statuses: Sequence[TaskStatus],
    ) -> list[TransformometroTask]:
        rows = self.fetch_all(
            f"""SELECT * FROM {_S}.tm_tasks
                WHERE assignee_user_id = %s::uuid AND status = ANY(%s)
                ORDER BY due_date NULLS LAST, created_at DESC""",
            (assignee_user_id, list(statuses)),
        )
        return [_row_to_task(row) for row in rows]


class InMemoryTaskRepository(TaskRepositoryPort):
    def __init__(self) -> None:
        self.rows: dict[str, TransformometroTask] = {}

    def create(self, **kwargs) -> TransformometroTask:
        now = datetime.utcnow()
        task = TransformometroTask(
            id=str(uuid4()),
            status="pending",
            created_at=now,
            updated_at=now,
            completed_at=None,
            **kwargs,
        )
        self.rows[task.id] = task
        return task

    def get(self, task_id: str) -> TransformometroTask | None:
        return self.rows.get(task_id)

    def update(self, task_id: str, **kwargs) -> TransformometroTask:
        current = self.rows[task_id]
        updated = TransformometroTask(
            **{**current.__dict__, **kwargs, "updated_at": datetime.utcnow()}
        )
        self.rows[task_id] = updated
        return updated

    def complete(self, task_id: str) -> TransformometroTask:
        current = self.rows[task_id]
        updated = TransformometroTask(
            **{
                **current.__dict__,
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        self.rows[task_id] = updated
        return updated

    def cancel(self, task_id: str) -> TransformometroTask:
        current = self.rows[task_id]
        updated = TransformometroTask(
            **{**current.__dict__, "status": "cancelled", "updated_at": datetime.utcnow()}
        )
        self.rows[task_id] = updated
        return updated

    def list_for_assignee(self, assignee_user_id: str, *, statuses: Sequence[TaskStatus]):
        return [
            task
            for task in self.rows.values()
            if task.assignee_user_id == assignee_user_id and task.status in statuses
        ]
