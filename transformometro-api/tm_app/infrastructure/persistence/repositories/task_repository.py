from __future__ import annotations

from datetime import date, datetime
from typing import Any, Sequence
from uuid import uuid4

from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask
from tm_app.domain.ports.task_repository_port import TaskOriginContext, TaskRepositoryPort
from tm_app.domain.services.transformometro_task_rules import (
    assert_can_cancel,
    assert_can_complete,
    assert_can_update,
    can_cancel_task,
    can_complete_task,
    can_update_task,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_S = "transformometro"


def _row_to_task(row: dict[str, Any]) -> TransformometroTask:
    due = row.get("due_date")
    if isinstance(due, datetime):
        due = due.date()
    source = row.get("source_interaction_message_id")
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
        source_interaction_message_id=str(source) if source else None,
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
        source_interaction_message_id: str | None = None,
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_tasks
                (title, description, status, assignee_user_id, created_by_user_id, due_date,
                 source_interaction_message_id)
                VALUES (%s, %s, 'pending', %s::uuid, %s::uuid, %s,
                        NULLIF(%s, '')::uuid)
                RETURNING *""",
            (
                title,
                description,
                assignee_user_id,
                created_by_user_id,
                due_date,
                source_interaction_message_id or "",
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar a tarefa.")
        return _row_to_task(row)

    def message_exists(self, message_id: str) -> bool:
        row = self.fetch_one(
            f"""SELECT 1 AS ok FROM {_S}.tm_interaction_messages
                WHERE id = %s::uuid AND deleted_at IS NULL""",
            (message_id,),
        )
        return row is not None

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
        actor_id: str,
        actor_is_manager: bool,
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET title = %s, description = %s, assignee_user_id = %s::uuid,
                    due_date = %s, updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                  AND (%s OR created_by_user_id = %s::uuid)
                RETURNING *""",
            (
                title,
                description,
                assignee_user_id,
                due_date,
                task_id,
                actor_is_manager,
                actor_id,
            ),
        )
        if row is None:
            self._raise_write_rejected(
                task_id,
                actor_id=actor_id,
                actor_is_manager=actor_is_manager,
                allowed=can_update_task,
                assert_allowed=assert_can_update,
            )
        return _row_to_task(row)

    def complete(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET status = 'completed', completed_at = NOW(), updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                  AND (%s OR created_by_user_id = %s::uuid
                       OR assignee_user_id = %s::uuid)
                RETURNING *""",
            (task_id, actor_is_manager, actor_id, actor_id),
        )
        if row is None:
            self._raise_write_rejected(
                task_id,
                actor_id=actor_id,
                actor_is_manager=actor_is_manager,
                allowed=can_complete_task,
                assert_allowed=assert_can_complete,
            )
        return _row_to_task(row)

    def cancel(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_tasks
                SET status = 'cancelled', updated_at = NOW()
                WHERE id = %s::uuid AND status = 'pending'
                  AND (%s OR created_by_user_id = %s::uuid)
                RETURNING *""",
            (task_id, actor_is_manager, actor_id),
        )
        if row is None:
            self._raise_write_rejected(
                task_id,
                actor_id=actor_id,
                actor_is_manager=actor_is_manager,
                allowed=can_cancel_task,
                assert_allowed=assert_can_cancel,
            )
        return _row_to_task(row)

    def _raise_write_rejected(
        self,
        task_id: str,
        *,
        actor_id: str,
        actor_is_manager: bool,
        allowed,
        assert_allowed,
    ) -> None:
        """Classify a zero-row conditional write against the row's current
        state: missing → LookupError, unauthorized at write time →
        PermissionError, incompatible status → ValueError. The relationship
        is re-read after the failed write, so stale authorizations are
        classified against the authoritative row, never trusted."""
        task = self.get(task_id)
        if task is None:
            raise LookupError("Tarefa não encontrada.")
        if not allowed(actor_id, actor_is_manager, task):
            raise PermissionError("Sem autorização sobre esta tarefa.")
        assert_allowed(task.status)

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

    def list_delegated_by(
        self,
        creator_user_id: str,
        *,
        statuses: Sequence[TaskStatus],
    ) -> list[TransformometroTask]:
        rows = self.fetch_all(
            f"""SELECT * FROM {_S}.tm_tasks
                WHERE created_by_user_id = %s::uuid
                  AND assignee_user_id <> %s::uuid
                  AND status = ANY(%s)
                ORDER BY due_date NULLS LAST, created_at DESC""",
            (creator_user_id, creator_user_id, list(statuses)),
        )
        return [_row_to_task(row) for row in rows]

    def origin_contexts(
        self,
        task_ids: Sequence[str],
    ) -> dict[str, TaskOriginContext]:
        ids = [str(task_id) for task_id in task_ids if str(task_id or "").strip()]
        if not ids:
            return {}
        rows = self.fetch_all(
            f"""SELECT t.id AS task_id,
                       r.id AS room_id,
                       NULLIF(btrim(p.nome_processo), '') AS nome_processo,
                       NULLIF(btrim(p.codigo_processo), '') AS codigo_processo
                FROM {_S}.tm_tasks t
                LEFT JOIN {_S}.tm_interaction_messages m
                    ON m.id = t.source_interaction_message_id
                   AND m.deleted_at IS NULL
                LEFT JOIN {_S}.tm_interaction_rooms r
                    ON r.id = m.room_id
                   AND r.deleted_at IS NULL
                LEFT JOIN {_S}.processos p
                    ON p.processo_id = r.processo_id
                WHERE t.id = ANY(%s::uuid[])""",
            (ids,),
        )
        contexts: dict[str, TaskOriginContext] = {}
        for row in rows:
            label = row.get("nome_processo") or row.get("codigo_processo")
            room_id = row.get("room_id")
            contexts[str(row["task_id"])] = TaskOriginContext(
                room_id=str(room_id) if room_id else None,
                context_label=str(label) if label else None,
            )
        return contexts

    def list_related_to_process(self, processo_id: str) -> list[TransformometroTask]:
        rows = self.fetch_all(
            f"""SELECT t.*
                FROM {_S}.tm_tasks t
                INNER JOIN {_S}.tm_interaction_messages m
                    ON m.id = t.source_interaction_message_id
                   AND m.deleted_at IS NULL
                INNER JOIN {_S}.tm_interaction_rooms r
                    ON r.id = m.room_id
                WHERE r.processo_id = %s::uuid
                ORDER BY t.created_at DESC""",
            (processo_id,),
        )
        return [_row_to_task(row) for row in rows]


class InMemoryTaskRepository(TaskRepositoryPort):
    def __init__(self) -> None:
        self.rows: dict[str, TransformometroTask] = {}
        self.message_ids: set[str] = set()
        self.message_processo_ids: dict[str, str] = {}
        self.message_room_ids: dict[str, str] = {}
        self.processo_labels: dict[str, str] = {}

    def message_exists(self, message_id: str) -> bool:
        return message_id in self.message_ids

    def link_message_to_process(
        self,
        message_id: str,
        processo_id: str,
        room_id: str | None = None,
        process_label: str | None = None,
    ) -> None:
        self.message_ids.add(message_id)
        self.message_processo_ids[message_id] = processo_id
        self.message_room_ids[message_id] = room_id or f"room-{processo_id}"
        if process_label:
            self.processo_labels[processo_id] = process_label

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

    def _authorized_row(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool, allowed, assert_allowed
    ) -> TransformometroTask:
        """Mirror of the PG conditional write: relationship + status are
        evaluated against the current row inside the mutation step, so a
        stale authorization never succeeds."""
        current = self.rows.get(task_id)
        if current is None:
            raise LookupError("Tarefa não encontrada.")
        if not allowed(actor_id, actor_is_manager, current):
            raise PermissionError("Sem autorização sobre esta tarefa.")
        assert_allowed(current.status)
        return current

    def update(
        self,
        task_id: str,
        *,
        actor_id: str,
        actor_is_manager: bool,
        **kwargs,
    ) -> TransformometroTask:
        current = self._authorized_row(
            task_id,
            actor_id=actor_id,
            actor_is_manager=actor_is_manager,
            allowed=can_update_task,
            assert_allowed=assert_can_update,
        )
        updated = TransformometroTask(
            **{**current.__dict__, **kwargs, "updated_at": datetime.utcnow()}
        )
        self.rows[task_id] = updated
        return updated

    def complete(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        current = self._authorized_row(
            task_id,
            actor_id=actor_id,
            actor_is_manager=actor_is_manager,
            allowed=can_complete_task,
            assert_allowed=assert_can_complete,
        )
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

    def cancel(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        current = self._authorized_row(
            task_id,
            actor_id=actor_id,
            actor_is_manager=actor_is_manager,
            allowed=can_cancel_task,
            assert_allowed=assert_can_cancel,
        )
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

    def list_delegated_by(self, creator_user_id: str, *, statuses: Sequence[TaskStatus]):
        return [
            task
            for task in self.rows.values()
            if task.created_by_user_id == creator_user_id
            and task.assignee_user_id != creator_user_id
            and task.status in statuses
        ]

    def origin_contexts(self, task_ids: Sequence[str]) -> dict[str, TaskOriginContext]:
        contexts: dict[str, TaskOriginContext] = {}
        for task_id in task_ids:
            task = self.rows.get(str(task_id))
            if task is None:
                continue
            source = task.source_interaction_message_id
            if not source:
                contexts[task.id] = TaskOriginContext()
                continue
            processo_id = self.message_processo_ids.get(source)
            contexts[task.id] = TaskOriginContext(
                room_id=self.message_room_ids.get(source),
                context_label=self.processo_labels.get(processo_id or "") or processo_id,
            )
        return contexts

    def list_related_to_process(self, processo_id: str) -> list[TransformometroTask]:
        related: list[TransformometroTask] = []
        for task in self.rows.values():
            source = task.source_interaction_message_id
            if not source:
                continue
            if self.message_processo_ids.get(source) == processo_id:
                related.append(task)
        related.sort(key=lambda item: item.created_at or datetime.min, reverse=True)
        return related
