from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.task import CommercialActivity, CommercialTask
from commercial_app.domain.ports.task_repository_port import (
    ActivityRepositoryPort,
    TaskRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_TASK_COLUMNS = """
    id, title, description, task_type, status, priority, due_at, completed_at,
    assignee_user_id, created_by_user_id, customer_code, customer_store,
    created_at, updated_at
"""

_ACTIVITY_COLUMNS = """
    id, activity_type, subject, body, occurred_at, actor_user_id,
    customer_code, customer_store, task_id, created_at
"""


def _row_task(row: dict[str, Any] | None) -> CommercialTask | None:
    if not row:
        return None
    return CommercialTask(
        id=row["id"],
        title=row["title"],
        description=row.get("description"),
        task_type=row["task_type"],
        status=row["status"],
        priority=row["priority"],
        due_at=row.get("due_at"),
        completed_at=row.get("completed_at"),
        assignee_user_id=row["assignee_user_id"],
        created_by_user_id=row["created_by_user_id"],
        customer_code=row.get("customer_code"),
        customer_store=row.get("customer_store"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_activity(row: dict[str, Any] | None) -> CommercialActivity | None:
    if not row:
        return None
    return CommercialActivity(
        id=row["id"],
        activity_type=row["activity_type"],
        subject=row.get("subject"),
        body=row.get("body"),
        occurred_at=row["occurred_at"],
        actor_user_id=row["actor_user_id"],
        customer_code=row.get("customer_code"),
        customer_store=row.get("customer_store"),
        task_id=row.get("task_id"),
        created_at=row["created_at"],
    )


class PostgresTaskRepository(PluginBaseRepository, TaskRepositoryPort):
    def list_for_assignee(
        self,
        *,
        assignee_user_id: str,
        status: str | None = "open",
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[CommercialTask]:
        clauses = ["deleted_at IS NULL", "assignee_user_id = %s"]
        params: list[Any] = [assignee_user_id]
        if status:
            clauses.append("status = %s")
            params.append(status)
        if due_before is not None:
            clauses.append("due_at IS NOT NULL AND due_at < %s")
            params.append(due_before)
        if due_after is not None:
            clauses.append("due_at IS NOT NULL AND due_at >= %s")
            params.append(due_after)
        params.append(max(1, min(limit, 200)))
        rows = self.fetch_all(
            f"""
            SELECT {_TASK_COLUMNS}
              FROM commercial.tasks
             WHERE {" AND ".join(clauses)}
             ORDER BY
               CASE priority
                 WHEN 'critical' THEN 0
                 WHEN 'high' THEN 1
                 WHEN 'normal' THEN 2
                 ELSE 3
               END,
               due_at ASC NULLS LAST,
               created_at ASC
             LIMIT %s
            """,
            tuple(params),
        )
        return [task for row in rows if (task := _row_task(row)) is not None]

    def get_by_id(self, task_id: UUID) -> CommercialTask | None:
        row = self.fetch_one(
            f"""
            SELECT {_TASK_COLUMNS}
              FROM commercial.tasks
             WHERE id = %s AND deleted_at IS NULL
            """,
            (str(task_id),),
        )
        return _row_task(row)

    def create(
        self,
        *,
        title: str,
        description: str | None,
        task_type: str,
        priority: str,
        due_at: datetime | None,
        assignee_user_id: str,
        created_by_user_id: str,
        customer_code: str | None,
        customer_store: str | None,
    ) -> CommercialTask:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.tasks (
                title, description, task_type, priority, due_at,
                assignee_user_id, created_by_user_id, customer_code, customer_store
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {_TASK_COLUMNS}
            """,
            (
                title,
                description,
                task_type,
                priority,
                due_at,
                assignee_user_id,
                created_by_user_id,
                customer_code,
                customer_store,
            ),
        )
        task = _row_task(row)
        if task is None:
            raise RuntimeError("Falha ao criar tarefa.")
        return task

    def complete(self, *, task_id: UUID, actor_user_id: str) -> CommercialTask | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.tasks
               SET status = 'done',
                   completed_at = NOW(),
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
               AND assignee_user_id = %s
               AND status = 'open'
         RETURNING {_TASK_COLUMNS}
            """,
            (str(task_id), actor_user_id),
        )
        return _row_task(row)


class PostgresActivityRepository(PluginBaseRepository, ActivityRepositoryPort):
    def list_for_customer(
        self,
        *,
        customer_code: str,
        customer_store: str,
        limit: int = 50,
    ) -> Sequence[CommercialActivity]:
        rows = self.fetch_all(
            f"""
            SELECT {_ACTIVITY_COLUMNS}
              FROM commercial.activities
             WHERE customer_code = %s AND customer_store = %s
             ORDER BY occurred_at DESC
             LIMIT %s
            """,
            (customer_code, customer_store, max(1, min(limit, 100))),
        )
        return [act for row in rows if (act := _row_activity(row)) is not None]

    def create(
        self,
        *,
        activity_type: str,
        subject: str | None,
        body: str | None,
        occurred_at: datetime | None,
        actor_user_id: str,
        customer_code: str | None,
        customer_store: str | None,
        task_id: UUID | None,
    ) -> CommercialActivity:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.activities (
                activity_type, subject, body, occurred_at, actor_user_id,
                customer_code, customer_store, task_id
            ) VALUES (
                %s, %s, %s, COALESCE(%s, NOW()), %s, %s, %s, %s
            )
            RETURNING {_ACTIVITY_COLUMNS}
            """,
            (
                activity_type,
                subject,
                body,
                occurred_at,
                actor_user_id,
                customer_code,
                customer_store,
                str(task_id) if task_id else None,
            ),
        )
        activity = _row_activity(row)
        if activity is None:
            raise RuntimeError("Falha ao criar atividade.")
        return activity
