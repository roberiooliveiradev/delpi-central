from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.task import (
    CommercialActivity,
    CommercialTask,
    TaskAssigneeGroupRef,
    TaskCustomerRef,
    normalize_assignee_group_ids,
    normalize_assignee_user_ids,
    normalize_task_customers,
)
from commercial_app.domain.ports.task_repository_port import (
    ActivityRepositoryPort,
    TaskRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_TASK_COLUMNS = """
    id, title, description, task_type, status, priority, due_at, completed_at,
    completed_by_user_id, assignee_user_id, created_by_user_id, customer_code, customer_store,
    related_entity_type, related_entity_id, source_interaction_message_id,
    created_at, updated_at
"""

_TASK_COLUMNS_ALIASED = """
    t.id, t.title, t.description, t.task_type, t.status, t.priority, t.due_at, t.completed_at,
    t.completed_by_user_id, t.assignee_user_id, t.created_by_user_id, t.customer_code, t.customer_store,
    t.related_entity_type, t.related_entity_id, t.source_interaction_message_id,
    t.created_at, t.updated_at
"""

_ACTIVITY_COLUMNS = """
    id, activity_type, subject, body, occurred_at, actor_user_id,
    customer_code, customer_store, task_id, created_at
"""

_OPEN_ORDER_SQL = """CASE priority
                 WHEN 'critical' THEN 0
                 WHEN 'high' THEN 1
                 WHEN 'normal' THEN 2
                 ELSE 3
               END,
               due_at ASC NULLS LAST,
               created_at ASC"""

_DONE_ORDER_SQL = "completed_at DESC NULLS LAST, updated_at DESC"

_OPEN_ORDER_SQL_ALIASED = """CASE t.priority
                 WHEN 'critical' THEN 0
                 WHEN 'high' THEN 1
                 WHEN 'normal' THEN 2
                 ELSE 3
               END,
               t.due_at ASC NULLS LAST,
               t.created_at ASC"""

_DONE_ORDER_SQL_ALIASED = "t.completed_at DESC NULLS LAST, t.updated_at DESC"


def _row_task_base(row: dict[str, Any] | None) -> CommercialTask | None:
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
        completed_by_user_id=(
            str(row["completed_by_user_id"]).strip()
            if row.get("completed_by_user_id")
            else None
        ),
        assignee_user_id=row["assignee_user_id"],
        created_by_user_id=row["created_by_user_id"],
        customer_code=row.get("customer_code"),
        customer_store=row.get("customer_store"),
        related_entity_type=(
            str(row["related_entity_type"]).strip()
            if row.get("related_entity_type")
            else None
        ),
        related_entity_id=(
            str(row["related_entity_id"]).strip()
            if row.get("related_entity_id")
            else None
        ),
        source_interaction_message_id=row.get("source_interaction_message_id"),
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
    def _load_junctions(
        self,
        task_ids: Sequence[UUID | str],
    ) -> tuple[
        dict[str, list[str]],
        dict[str, list[TaskCustomerRef]],
        dict[str, list[TaskAssigneeGroupRef]],
    ]:
        ids = [str(item) for item in task_ids if item]
        if not ids:
            return {}, {}, {}
        assignee_rows = self.fetch_all(
            """
            SELECT task_id::text AS task_id, user_id, sort_order
              FROM commercial.task_assignees
             WHERE task_id = ANY(%s::uuid[])
             ORDER BY sort_order ASC, user_id ASC
            """,
            (ids,),
        )
        customer_rows = self.fetch_all(
            """
            SELECT task_id::text AS task_id, customer_code, customer_store,
                   customer_name, sort_order
              FROM commercial.task_customers
             WHERE task_id = ANY(%s::uuid[])
             ORDER BY sort_order ASC, customer_code ASC, customer_store ASC
            """,
            (ids,),
        )
        group_rows = self.fetch_all(
            """
            SELECT tag.task_id::text AS task_id,
                   g.id::text AS group_id,
                   g.kind,
                   g.name
              FROM commercial.task_assignee_groups tag
              JOIN commercial.commercial_groups g ON g.id = tag.group_id
             WHERE tag.task_id = ANY(%s::uuid[])
             ORDER BY g.sort_order ASC, g.name ASC
            """,
            (ids,),
        )
        assignees: dict[str, list[str]] = {}
        for row in assignee_rows:
            tid = str(row["task_id"])
            assignees.setdefault(tid, []).append(str(row["user_id"]).strip())
        customers: dict[str, list[TaskCustomerRef]] = {}
        for row in customer_rows:
            tid = str(row["task_id"])
            customers.setdefault(tid, []).append(
                TaskCustomerRef(
                    customer_code=str(row["customer_code"]).strip(),
                    customer_store=str(row["customer_store"]).strip(),
                    customer_name=(
                        str(row["customer_name"]).strip()
                        if row.get("customer_name")
                        else None
                    ),
                )
            )
        groups: dict[str, list[TaskAssigneeGroupRef]] = {}
        for row in group_rows:
            tid = str(row["task_id"])
            groups.setdefault(tid, []).append(
                TaskAssigneeGroupRef(
                    id=str(row["group_id"]).strip(),
                    kind=str(row.get("kind") or "").strip(),
                    name=str(row.get("name") or "").strip(),
                )
            )
        return assignees, customers, groups

    def _hydrate(self, tasks: Sequence[CommercialTask]) -> list[CommercialTask]:
        if not tasks:
            return []
        assignees_by_id, customers_by_id, groups_by_id = self._load_junctions(
            [task.id for task in tasks]
        )
        hydrated: list[CommercialTask] = []
        for task in tasks:
            tid = str(task.id)
            assignee_ids = tuple(assignees_by_id.get(tid) or ())
            if not assignee_ids and task.assignee_user_id:
                assignee_ids = (task.assignee_user_id,)
            custs = tuple(customers_by_id.get(tid) or ())
            if not custs and task.customer_code and task.customer_store:
                custs = (
                    TaskCustomerRef(
                        customer_code=task.customer_code,
                        customer_store=task.customer_store,
                    ),
                )
            groups = tuple(groups_by_id.get(tid) or ())
            group_ids = tuple(group.id for group in groups)
            hydrated.append(
                CommercialTask(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    task_type=task.task_type,
                    status=task.status,
                    priority=task.priority,
                    due_at=task.due_at,
                    completed_at=task.completed_at,
                    completed_by_user_id=task.completed_by_user_id,
                    assignee_user_id=assignee_ids[0] if assignee_ids else task.assignee_user_id,
                    created_by_user_id=task.created_by_user_id,
                    customer_code=custs[0].customer_code if custs else task.customer_code,
                    customer_store=custs[0].customer_store if custs else task.customer_store,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    assignee_user_ids=assignee_ids,
                    customers=custs,
                    assignee_group_ids=group_ids,
                    assignee_groups=groups,
                )
            )
        return hydrated

    def _replace_assignees(
        self,
        *,
        task_id: UUID | str,
        assignee_user_ids: Sequence[str],
        auto_commit: bool = False,
    ) -> None:
        with self.db():
            tid = str(task_id)
            self.execute(
                "DELETE FROM commercial.task_assignees WHERE task_id = %s",
                (tid,),
                auto_commit=False,
            )
            values = [
                (tid, uid, index)
                for index, uid in enumerate(assignee_user_ids)
                if uid and str(uid).strip()
            ]
            if values:
                self.execute_many(
                    """
                    INSERT INTO commercial.task_assignees (task_id, user_id, sort_order)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (task_id, user_id) DO UPDATE
                       SET sort_order = EXCLUDED.sort_order
                    """,
                    values,
                    auto_commit=False,
                )
            if auto_commit:
                self.commit()

    def _replace_customers(
        self,
        *,
        task_id: UUID | str,
        customers: Sequence[TaskCustomerRef],
        auto_commit: bool = False,
    ) -> None:
        with self.db():
            tid = str(task_id)
            self.execute(
                "DELETE FROM commercial.task_customers WHERE task_id = %s",
                (tid,),
                auto_commit=False,
            )
            values = [
                (
                    tid,
                    item.customer_code,
                    item.customer_store,
                    item.customer_name,
                    index,
                )
                for index, item in enumerate(customers)
                if item.customer_code and item.customer_store
            ]
            if values:
                self.execute_many(
                    """
                    INSERT INTO commercial.task_customers (
                        task_id, customer_code, customer_store, customer_name, sort_order
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id, customer_code, customer_store) DO UPDATE
                       SET customer_name = EXCLUDED.customer_name,
                           sort_order = EXCLUDED.sort_order
                    """,
                    values,
                    auto_commit=False,
                )
            if auto_commit:
                self.commit()

    def _replace_groups(
        self,
        *,
        task_id: UUID | str,
        assignee_group_ids: Sequence[str],
        auto_commit: bool = False,
    ) -> None:
        with self.db():
            tid = str(task_id)
            self.execute(
                "DELETE FROM commercial.task_assignee_groups WHERE task_id = %s",
                (tid,),
                auto_commit=False,
            )
            values = [
                (tid, gid)
                for gid in assignee_group_ids
                if gid and str(gid).strip()
            ]
            if values:
                self.execute_many(
                    """
                    INSERT INTO commercial.task_assignee_groups (task_id, group_id)
                    VALUES (%s, %s)
                    ON CONFLICT (task_id, group_id) DO NOTHING
                    """,
                    values,
                    auto_commit=False,
                )
            if auto_commit:
                self.commit()

    def _resolve_assignees(
        self,
        *,
        assignee_user_id: str,
        assignee_user_ids: Sequence[str] | None,
    ) -> list[str]:
        return normalize_assignee_user_ids(
            assignee_user_ids=assignee_user_ids,
            assignee_user_id=assignee_user_id,
            fallback_user_id=assignee_user_id,
        )

    def _resolve_customers(
        self,
        *,
        customer_code: str | None,
        customer_store: str | None,
        customers: Sequence[TaskCustomerRef] | None,
    ) -> list[TaskCustomerRef]:
        return normalize_task_customers(
            customers=customers,
            customer_code=customer_code,
            customer_store=customer_store,
        )

    def list_for_assignee(
        self,
        *,
        assignee_user_id: str,
        status: str | None = "open",
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[CommercialTask]:
        clauses = [
            "t.deleted_at IS NULL",
            """(
                t.assignee_user_id = %s
                OR EXISTS (
                    SELECT 1
                      FROM commercial.task_assignees ta
                     WHERE ta.task_id = t.id
                       AND ta.user_id = %s
                )
                OR EXISTS (
                    SELECT 1
                      FROM commercial.task_assignee_groups tag
                      JOIN commercial.commercial_group_members cgm
                        ON cgm.group_id = tag.group_id
                     WHERE tag.task_id = t.id
                       AND cgm.user_id = %s
                )
            )""",
        ]
        params: list[Any] = [assignee_user_id, assignee_user_id, assignee_user_id]
        if status:
            clauses.append("t.status = %s")
            params.append(status)
        if due_before is not None:
            clauses.append("t.due_at IS NOT NULL AND t.due_at < %s")
            params.append(due_before)
        if due_after is not None:
            clauses.append("t.due_at IS NOT NULL AND t.due_at >= %s")
            params.append(due_after)
        params.append(max(1, min(limit, 200)))
        order_sql = _DONE_ORDER_SQL_ALIASED if status == "done" else _OPEN_ORDER_SQL_ALIASED
        rows = self.fetch_all(
            f"""
            SELECT {_TASK_COLUMNS_ALIASED}
              FROM commercial.tasks t
             WHERE {" AND ".join(clauses)}
             ORDER BY {order_sql}
             LIMIT %s
            """,
            tuple(params),
        )
        base = [task for row in rows if (task := _row_task_base(row)) is not None]
        return self._hydrate(base)

    def list_for_assignees(
        self,
        *,
        assignee_user_ids: Sequence[str],
        status: str | None = "open",
        limit: int = 200,
    ) -> Sequence[CommercialTask]:
        ids = [str(item).strip() for item in assignee_user_ids if str(item).strip()]
        if not ids:
            return []
        clauses = [
            "t.deleted_at IS NULL",
            """(
                t.assignee_user_id = ANY(%s)
                OR EXISTS (
                    SELECT 1
                      FROM commercial.task_assignees ta
                     WHERE ta.task_id = t.id
                       AND ta.user_id = ANY(%s)
                )
                OR EXISTS (
                    SELECT 1
                      FROM commercial.task_assignee_groups tag
                      JOIN commercial.commercial_group_members cgm
                        ON cgm.group_id = tag.group_id
                     WHERE tag.task_id = t.id
                       AND cgm.user_id = ANY(%s)
                )
            )""",
        ]
        params: list[Any] = [ids, ids, ids]
        if status:
            clauses.append("t.status = %s")
            params.append(status)
        params.append(max(1, min(limit, 500)))
        order_sql = _DONE_ORDER_SQL_ALIASED if status == "done" else _OPEN_ORDER_SQL_ALIASED
        rows = self.fetch_all(
            f"""
            SELECT {_TASK_COLUMNS_ALIASED}
              FROM commercial.tasks t
             WHERE {" AND ".join(clauses)}
             ORDER BY {order_sql}
             LIMIT %s
            """,
            tuple(params),
        )
        base = [task for row in rows if (task := _row_task_base(row)) is not None]
        return self._hydrate(base)

    def list_by_status(
        self,
        *,
        status: str | None = "open",
        limit: int = 500,
    ) -> Sequence[CommercialTask]:
        clauses = ["deleted_at IS NULL"]
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        params.append(max(1, min(limit, 500)))
        order_sql = _DONE_ORDER_SQL if status == "done" else _OPEN_ORDER_SQL
        rows = self.fetch_all(
            f"""
            SELECT {_TASK_COLUMNS}
              FROM commercial.tasks
             WHERE {" AND ".join(clauses)}
             ORDER BY {order_sql}
             LIMIT %s
            """,
            tuple(params),
        )
        base = [task for row in rows if (task := _row_task_base(row)) is not None]
        return self._hydrate(base)

    def get_by_id(self, task_id: UUID) -> CommercialTask | None:
        row = self.fetch_one(
            f"""
            SELECT {_TASK_COLUMNS}
              FROM commercial.tasks
             WHERE id = %s AND deleted_at IS NULL
            """,
            (str(task_id),),
        )
        base = _row_task_base(row)
        if base is None:
            return None
        hydrated = self._hydrate([base])
        return hydrated[0] if hydrated else None

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
        assignee_user_ids: Sequence[str] | None = None,
        customers: Sequence[TaskCustomerRef] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        source_interaction_message_id: UUID | None = None,
    ) -> CommercialTask:
        with self.db():
            assignees = self._resolve_assignees(
                assignee_user_id=assignee_user_id,
                assignee_user_ids=assignee_user_ids,
            )
            custs = self._resolve_customers(
                customer_code=customer_code,
                customer_store=customer_store,
                customers=customers,
            )
            groups = normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids)
            primary_assignee = assignees[0] if assignees else assignee_user_id
            primary_customer = custs[0] if custs else None
            related_type = (related_entity_type or "").strip() or None
            related_id = (related_entity_id or "").strip() or None
            row = self.execute_returning_one(
                f"""
                INSERT INTO commercial.tasks (
                    title, description, task_type, priority, due_at,
                    assignee_user_id, created_by_user_id, customer_code, customer_store,
                    related_entity_type, related_entity_id, source_interaction_message_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {_TASK_COLUMNS}
                """,
                (
                    title,
                    description,
                    task_type,
                    priority,
                    due_at,
                    primary_assignee,
                    created_by_user_id,
                    primary_customer.customer_code if primary_customer else None,
                    primary_customer.customer_store if primary_customer else None,
                    related_type,
                    related_id,
                    source_interaction_message_id,
                ),
                auto_commit=False,
            )
            task = _row_task_base(row)
            if task is None:
                self.rollback()
                raise RuntimeError("Falha ao criar tarefa.")
            try:
                self._replace_assignees(task_id=task.id, assignee_user_ids=assignees)
                self._replace_customers(task_id=task.id, customers=custs)
                self._replace_groups(task_id=task.id, assignee_group_ids=groups)
                self.commit()
            except Exception:
                self.rollback()
                raise
            hydrated = self._hydrate([task])
            return hydrated[0]

    def complete(
        self,
        *,
        task_id: UUID,
        completed_by_user_id: str | None = None,
    ) -> CommercialTask | None:
        completed_by = (completed_by_user_id or "").strip() or None
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.tasks
               SET status = 'done',
                   completed_at = NOW(),
                   completed_by_user_id = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
               AND status = 'open'
         RETURNING {_TASK_COLUMNS}
            """,
            (completed_by, str(task_id)),
        )
        base = _row_task_base(row)
        return self._hydrate([base])[0] if base else None

    def update_due_at(
        self,
        *,
        task_id: UUID,
        due_at: datetime,
    ) -> CommercialTask | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.tasks
               SET due_at = %s,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
               AND status = 'open'
         RETURNING {_TASK_COLUMNS}
            """,
            (due_at, str(task_id)),
        )
        base = _row_task_base(row)
        return self._hydrate([base])[0] if base else None

    def reassign(
        self,
        *,
        task_id: UUID,
        new_assignee_user_id: str,
        assignee_user_ids: Sequence[str] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
    ) -> CommercialTask | None:
        with self.db():
            assignees = self._resolve_assignees(
                assignee_user_id=new_assignee_user_id,
                assignee_user_ids=assignee_user_ids,
            )
            if not assignees:
                return None
            groups = normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids)
            primary = assignees[0]
            row = self.execute_returning_one(
                f"""
                UPDATE commercial.tasks
                   SET assignee_user_id = %s,
                       updated_at = NOW()
                 WHERE id = %s
                   AND deleted_at IS NULL
                   AND status = 'open'
             RETURNING {_TASK_COLUMNS}
                """,
                (primary, str(task_id)),
                auto_commit=False,
            )
            base = _row_task_base(row)
            if base is None:
                self.rollback()
                return None
            try:
                self._replace_assignees(task_id=task_id, assignee_user_ids=assignees)
                if assignee_group_ids is not None:
                    self._replace_groups(task_id=task_id, assignee_group_ids=groups)
                self.commit()
            except Exception:
                self.rollback()
                raise
            return self._hydrate([base])[0]

    def update_description(
        self,
        *,
        task_id: UUID,
        description: str | None,
    ) -> CommercialTask | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.tasks
               SET description = %s,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
         RETURNING {_TASK_COLUMNS}
            """,
            (description, str(task_id)),
        )
        base = _row_task_base(row)
        if base is None:
            return None
        hydrated = self._hydrate([base])
        return hydrated[0] if hydrated else None

    def update(
        self,
        *,
        task_id: UUID,
        title: str,
        description: str | None,
        task_type: str,
        priority: str,
        due_at: datetime | None,
        customer_code: str | None,
        customer_store: str | None,
        assignee_user_id: str,
        assignee_user_ids: Sequence[str] | None = None,
        customers: Sequence[TaskCustomerRef] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
    ) -> CommercialTask | None:
        with self.db():
            assignees = self._resolve_assignees(
                assignee_user_id=assignee_user_id,
                assignee_user_ids=assignee_user_ids,
            )
            custs = self._resolve_customers(
                customer_code=customer_code,
                customer_store=customer_store,
                customers=customers,
            )
            groups = normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids)
            primary_assignee = assignees[0] if assignees else assignee_user_id
            primary_customer = custs[0] if custs else None
            row = self.execute_returning_one(
                f"""
                UPDATE commercial.tasks
                   SET title = %s,
                       description = %s,
                       task_type = %s,
                       priority = %s,
                       due_at = %s,
                       customer_code = %s,
                       customer_store = %s,
                       assignee_user_id = %s,
                       updated_at = NOW()
                 WHERE id = %s
                   AND deleted_at IS NULL
                   AND status = 'open'
             RETURNING {_TASK_COLUMNS}
                """,
                (
                    title,
                    description,
                    task_type,
                    priority,
                    due_at,
                    primary_customer.customer_code if primary_customer else None,
                    primary_customer.customer_store if primary_customer else None,
                    primary_assignee,
                    str(task_id),
                ),
                auto_commit=False,
            )
            base = _row_task_base(row)
            if base is None:
                self.rollback()
                return None
            try:
                self._replace_assignees(task_id=task_id, assignee_user_ids=assignees)
                self._replace_customers(task_id=task_id, customers=custs)
                if assignee_group_ids is not None:
                    self._replace_groups(task_id=task_id, assignee_group_ids=groups)
                self.commit()
            except Exception:
                self.rollback()
                raise
            return self._hydrate([base])[0]

    def soft_delete(self, *, task_id: UUID) -> CommercialTask | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.tasks
               SET deleted_at = NOW(),
                   status = 'cancelled',
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
               AND status = 'open'
         RETURNING {_TASK_COLUMNS}
            """,
            (str(task_id),),
        )
        base = _row_task_base(row)
        return self._hydrate([base])[0] if base else None


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
        with self.db():
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
