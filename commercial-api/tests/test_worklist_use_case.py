from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

from commercial_app.application.use_cases.manage_worklist import (
    CreateTaskInput,
    ManageWorklistUseCase,
)
from commercial_app.domain.entities.task import CommercialActivity, CommercialTask


class InMemoryTaskRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, CommercialTask] = {}

    def list_for_assignee(
        self,
        *,
        assignee_user_id: str,
        status: str | None = "open",
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[CommercialTask]:
        out: list[CommercialTask] = []
        for task in self.items.values():
            if task.assignee_user_id != assignee_user_id:
                continue
            if status and task.status != status:
                continue
            if due_before is not None and (task.due_at is None or task.due_at >= due_before):
                continue
            if due_after is not None and (task.due_at is None or task.due_at < due_after):
                continue
            out.append(task)
        return out[:limit]

    def get_by_id(self, task_id: UUID) -> CommercialTask | None:
        return self.items.get(task_id)

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
        now = datetime.now(timezone.utc)
        task = CommercialTask(
            id=uuid4(),
            title=title,
            description=description,
            task_type=task_type,
            status="open",
            priority=priority,
            due_at=due_at,
            completed_at=None,
            assignee_user_id=assignee_user_id,
            created_by_user_id=created_by_user_id,
            customer_code=customer_code,
            customer_store=customer_store,
            created_at=now,
            updated_at=now,
        )
        self.items[task.id] = task
        return task

    def complete(self, *, task_id: UUID, actor_user_id: str) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.assignee_user_id != actor_user_id or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        done = CommercialTask(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status="done",
            priority=task.priority,
            due_at=task.due_at,
            completed_at=now,
            assignee_user_id=task.assignee_user_id,
            created_by_user_id=task.created_by_user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            created_at=task.created_at,
            updated_at=now,
        )
        self.items[task.id] = done
        return done

    def update_due_at(
        self,
        *,
        task_id: UUID,
        actor_user_id: str,
        due_at: datetime,
    ) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.assignee_user_id != actor_user_id or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        updated = CommercialTask(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            due_at=due_at,
            completed_at=task.completed_at,
            assignee_user_id=task.assignee_user_id,
            created_by_user_id=task.created_by_user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            created_at=task.created_at,
            updated_at=now,
        )
        self.items[task.id] = updated
        return updated


class InMemoryActivityRepo:
    def __init__(self) -> None:
        self.items: list[CommercialActivity] = []

    def list_for_customer(
        self,
        *,
        customer_code: str,
        customer_store: str,
        limit: int = 50,
    ) -> Sequence[CommercialActivity]:
        return [
            a
            for a in self.items
            if a.customer_code == customer_code and a.customer_store == customer_store
        ][:limit]

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
        now = datetime.now(timezone.utc)
        activity = CommercialActivity(
            id=uuid4(),
            activity_type=activity_type,
            subject=subject,
            body=body,
            occurred_at=occurred_at or now,
            actor_user_id=actor_user_id,
            customer_code=customer_code,
            customer_store=customer_store,
            task_id=task_id,
            created_at=now,
        )
        self.items.append(activity)
        return activity


def test_worklist_buckets_and_complete():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    uc = ManageWorklistUseCase(task_repository=tasks, activity_repository=activities)

    now = datetime.now(timezone.utc)
    overdue = uc.create_task(
        user_id="u1",
        data=CreateTaskInput(title="Atrasada", due_at=now - timedelta(days=1)),
    )
    uc.create_task(
        user_id="u1",
        data=CreateTaskInput(title="Hoje", due_at=now.replace(hour=18)),
    )
    wl = uc.get_worklist(user_id="u1")
    assert wl["counts"]["open"] == 2
    assert wl["counts"]["overdue"] >= 1
    assert any(item["id"] == str(overdue.id) for item in wl["overdue"])

    done = uc.complete_task(user_id="u1", task_id=overdue.id)
    assert done.status == "done"
    assert any(a.task_id == overdue.id for a in activities.items)


def test_defer_task_updates_due_at():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    uc = ManageWorklistUseCase(task_repository=tasks, activity_repository=activities)

    now = datetime.now(timezone.utc)
    task = uc.create_task(
        user_id="u1",
        data=CreateTaskInput(title="Adiar", due_at=now),
    )
    new_due = now + timedelta(days=1)
    deferred = uc.defer_task(user_id="u1", task_id=task.id, due_at=new_due)
    assert deferred.due_at == new_due
    assert any(
        a.task_id == task.id and "adiada" in (a.subject or "").lower()
        for a in activities.items
    )


def test_create_task_persists_description_in_worklist_and_activity():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    uc = ManageWorklistUseCase(task_repository=tasks, activity_repository=activities)

    now = datetime.now(timezone.utc)
    created = uc.create_task(
        user_id="u1",
        data=CreateTaskInput(
            title="Follow-up ACME",
            description="  Confirmar NF e prazo de entrega  ",
            due_at=now.replace(hour=18),
            task_type="call",
            priority="high",
        ),
    )
    assert created.description == "Confirmar NF e prazo de entrega"

    wl = uc.get_worklist(user_id="u1")
    matched = next(
        (item for bucket in ("overdue", "today", "later") for item in wl[bucket] if item["id"] == str(created.id)),
        None,
    )
    assert matched is not None
    assert matched["description"] == "Confirmar NF e prazo de entrega"
    assert any(
        a.task_id == created.id and a.body == "Confirmar NF e prazo de entrega"
        for a in activities.items
    )


def test_permissions_helpers():
    from commercial_app.application.security.commercial_permissions import (
        can_manage_followups,
        can_view_worklist,
    )

    class User:
        def __init__(self, permissions: list[str]):
            self.permissions = permissions
            self.is_superadmin = False

    assert can_view_worklist(User(["commercial.worklist.view"]))
    assert can_manage_followups(User(["commercial.followups.manage"]))
    assert not can_manage_followups(User(["commercial.accounts.view"]))
