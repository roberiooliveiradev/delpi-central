from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

import pytest

from commercial_app.application.use_cases.manage_worklist import (
    CreateTaskInput,
    ManageWorklistUseCase,
    UpdateTaskInput,
)
from commercial_app.domain.entities.task import (
    CommercialActivity,
    CommercialTask,
    TaskCustomerRef,
    normalize_assignee_group_ids,
    normalize_assignee_user_ids,
    normalize_task_customers,
)


class InMemoryTaskRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, CommercialTask] = {}
        # user_id -> set(group_id) for membership-based visibility in tests
        self.user_group_ids: dict[str, set[str]] = {}

    def _matches_assignee(self, task: CommercialTask, assignee_user_id: str) -> bool:
        if assignee_user_id in task.resolved_assignee_user_ids():
            return True
        member_groups = self.user_group_ids.get(assignee_user_id, set())
        return bool(member_groups.intersection(task.resolved_assignee_group_ids()))

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
            if not self._matches_assignee(task, assignee_user_id):
                continue
            if status and task.status != status:
                continue
            if due_before is not None and (task.due_at is None or task.due_at >= due_before):
                continue
            if due_after is not None and (task.due_at is None or task.due_at < due_after):
                continue
            out.append(task)
        if status == "done":
            out.sort(
                key=lambda t: t.completed_at or t.updated_at,
                reverse=True,
            )
        return out[:limit]

    def list_for_assignees(
        self,
        *,
        assignee_user_ids: Sequence[str],
        status: str | None = "open",
        limit: int = 200,
    ) -> Sequence[CommercialTask]:
        allowed = set(assignee_user_ids)
        out = [
            task
            for task in self.items.values()
            if allowed.intersection(task.resolved_assignee_user_ids())
            and (not status or task.status == status)
        ]
        if status == "done":
            out.sort(
                key=lambda t: t.completed_at or t.updated_at,
                reverse=True,
            )
        return out[:limit]

    def list_by_status(
        self,
        *,
        status: str | None = "open",
        limit: int = 500,
    ) -> Sequence[CommercialTask]:
        out = [
            task
            for task in self.items.values()
            if not status or task.status == status
        ]
        if status == "done":
            out.sort(
                key=lambda t: t.completed_at or t.updated_at,
                reverse=True,
            )
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
        assignee_user_ids: Sequence[str] | None = None,
        customers: Sequence[TaskCustomerRef] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
    ) -> CommercialTask:
        now = datetime.now(timezone.utc)
        assignees = tuple(
            normalize_assignee_user_ids(
                assignee_user_ids=assignee_user_ids,
                assignee_user_id=assignee_user_id,
                fallback_user_id=assignee_user_id,
            )
        )
        custs = tuple(
            normalize_task_customers(
                customers=customers,
                customer_code=customer_code,
                customer_store=customer_store,
            )
        )
        groups = tuple(normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids))
        task = CommercialTask(
            id=uuid4(),
            title=title,
            description=description,
            task_type=task_type,
            status="open",
            priority=priority,
            due_at=due_at,
            completed_at=None,
            assignee_user_id=assignees[0] if assignees else assignee_user_id,
            created_by_user_id=created_by_user_id,
            customer_code=custs[0].customer_code if custs else customer_code,
            customer_store=custs[0].customer_store if custs else customer_store,
            created_at=now,
            updated_at=now,
            assignee_user_ids=assignees,
            customers=custs,
            assignee_group_ids=groups,
        )
        self.items[task.id] = task
        return task

    def complete(
        self,
        *,
        task_id: UUID,
        completed_by_user_id: str | None = None,
    ) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        done = replace(
            task,
            status="done",
            completed_at=now,
            completed_by_user_id=(completed_by_user_id or "").strip() or None,
            updated_at=now,
        )
        self.items[task.id] = done
        return done

    def update_due_at(self, *, task_id: UUID, due_at: datetime) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        updated = replace(task, due_at=due_at, updated_at=now)
        self.items[task.id] = updated
        return updated

    def reassign(
        self,
        *,
        task_id: UUID,
        new_assignee_user_id: str,
        assignee_user_ids: Sequence[str] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
    ) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        assignees = tuple(
            normalize_assignee_user_ids(
                assignee_user_ids=assignee_user_ids,
                assignee_user_id=new_assignee_user_id,
                fallback_user_id=new_assignee_user_id,
            )
        )
        groups = (
            tuple(normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids))
            if assignee_group_ids is not None
            else task.assignee_group_ids
        )
        updated = replace(
            task,
            assignee_user_id=assignees[0] if assignees else new_assignee_user_id,
            updated_at=now,
            assignee_user_ids=assignees,
            assignee_group_ids=groups,
        )
        self.items[task.id] = updated
        return updated

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
        task = self.items.get(task_id)
        if task is None or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        assignees = tuple(
            normalize_assignee_user_ids(
                assignee_user_ids=assignee_user_ids,
                assignee_user_id=assignee_user_id,
                fallback_user_id=assignee_user_id,
            )
        )
        custs = tuple(
            normalize_task_customers(
                customers=customers,
                customer_code=customer_code,
                customer_store=customer_store,
            )
        )
        groups = (
            tuple(normalize_assignee_group_ids(assignee_group_ids=assignee_group_ids))
            if assignee_group_ids is not None
            else task.assignee_group_ids
        )
        updated = replace(
            task,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_at=due_at,
            assignee_user_id=assignees[0] if assignees else assignee_user_id,
            customer_code=custs[0].customer_code if custs else customer_code,
            customer_store=custs[0].customer_store if custs else customer_store,
            updated_at=now,
            assignee_user_ids=assignees,
            customers=custs,
            assignee_group_ids=groups,
        )
        self.items[task.id] = updated
        return updated

    def soft_delete(self, *, task_id: UUID) -> CommercialTask | None:
        task = self.items.get(task_id)
        if task is None or task.status != "open":
            return None
        now = datetime.now(timezone.utc)
        deleted = replace(
            task,
            status="cancelled",
            updated_at=now,
        )
        del self.items[task.id]
        return deleted


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


class FakePortfolio:
    def __init__(self, user_id: str, display_name: str = "Seller") -> None:
        self.user_id = user_id
        self.display_name = display_name
        self.active = True


class InMemoryPortfolioRepo:
    def __init__(self, user_ids: Sequence[str]) -> None:
        self._ids = list(user_ids)

    def list_member_user_ids(self, *, active_portfolios_only: bool = True) -> list[str]:
        return list(self._ids)

    def list_portfolios(self, *, active_only: bool = False) -> list[FakePortfolio]:
        # Só o owner espelhado em seller_portfolios.user_id — membros extras vêm de list_member_user_ids.
        return [FakePortfolio(self._ids[0])] if self._ids else []


def test_team_user_ids_includes_portfolio_members_not_only_owner():
    """Membros N:N entram na equipe mesmo sem espelho em seller_portfolios.user_id."""
    portfolios = InMemoryPortfolioRepo(["owner-1", "helper-1", "helper-2"])
    uc = ManageWorklistUseCase(
        task_repository=InMemoryTaskRepo(),
        activity_repository=InMemoryActivityRepo(),
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    assert uc.team_user_ids() == {"owner-1", "helper-1", "helper-2"}
    # list_portfolios sozinho não bastaria (só owner).
    assert {p.user_id for p in portfolios.list_portfolios(active_only=True)} == {"owner-1"}


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
        (
            item
            for bucket in ("overdue", "today", "later")
            for item in wl[bucket]
            if item["id"] == str(created.id)
        ),
        None,
    )
    assert matched is not None
    assert matched["description"] == "Confirmar NF e prazo de entrega"
    assert any(
        a.task_id == created.id and a.body == "Confirmar NF e prazo de entrega"
        for a in activities.items
    )


def test_create_and_reassign_team_task():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["manager", "seller-a", "seller-b"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )

    created = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(title="Para A", assignee_user_id="seller-a"),
        actor_is_portfolio_manager=True,
    )
    assert created.assignee_user_id == "seller-a"

    with pytest.raises(PermissionError):
        uc.create_task(
            user_id="seller-a",
            data=CreateTaskInput(title="Hack", assignee_user_id="seller-b"),
            actor_is_portfolio_manager=False,
        )

    reassigned = uc.reassign_task(
        user_id="manager",
        task_id=created.id,
        new_assignee_user_id="seller-b",
        actor_is_portfolio_manager=True,
    )
    assert reassigned.assignee_user_id == "seller-b"

    team_wl = uc.get_worklist(
        user_id="manager",
        scope="team",
        actor_is_portfolio_manager=True,
    )
    assert team_wl["scope"] == "team"
    assert team_wl["counts"]["open"] == 1
    assert any(item["assignee_user_id"] == "seller-b" for item in team_wl["later"] + team_wl["today"] + team_wl["overdue"])

    filtered = uc.get_worklist(
        user_id="manager",
        scope="team",
        assignee_user_id="seller-b",
        actor_is_portfolio_manager=True,
    )
    assert filtered["counts"]["open"] == 1


def test_manager_assigns_portal_user_without_portfolio_and_team_sees_all():
    """Responsável = usuário do portal; fila equipe lista todas as tarefas."""
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["manager", "seller-a"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )

    created = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(
            title="Para portal user",
            assignee_user_id="portal-user-no-portfolio",
            customer_code="C999",
            customer_store="01",
        ),
        actor_is_portfolio_manager=True,
    )
    assert created.assignee_user_id == "portal-user-no-portfolio"
    assert created.customer_code == "C999"

    team_wl = uc.get_worklist(
        user_id="manager",
        scope="team",
        actor_is_portfolio_manager=True,
    )
    assert team_wl["counts"]["open"] == 1
    assert "portal-user-no-portfolio" in team_wl["team_user_ids"]

    reassigned = uc.reassign_task(
        user_id="manager",
        task_id=created.id,
        new_assignee_user_id="another-portal-user",
        actor_is_portfolio_manager=True,
    )
    assert reassigned.assignee_user_id == "another-portal-user"

    filtered = uc.get_worklist(
        user_id="manager",
        scope="team",
        assignee_user_id="another-portal-user",
        actor_is_portfolio_manager=True,
    )
    assert filtered["counts"]["open"] == 1


def test_update_task_fields_and_permission():
    from commercial_app.application.use_cases.manage_worklist import UpdateTaskInput

    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["seller-a", "seller-b"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    now = datetime.now(timezone.utc)
    created = uc.create_task(
        user_id="seller-a",
        data=CreateTaskInput(title="Original", due_at=now, priority="normal"),
    )
    updated = uc.update_task(
        user_id="seller-a",
        task_id=created.id,
        data=UpdateTaskInput(
            title="Atualizada",
            description="Nova nota",
            task_type="call",
            priority="high",
            due_at=now + timedelta(days=2),
            customer_code="C001",
            customer_store="01",
        ),
    )
    assert updated.title == "Atualizada"
    assert updated.description == "Nova nota"
    assert updated.task_type == "call"
    assert updated.priority == "high"
    assert updated.customer_code == "C001"
    assert any(
        a.task_id == created.id and "atualizada" in (a.subject or "").lower()
        for a in activities.items
    )

    with pytest.raises(PermissionError):
        uc.update_task(
            user_id="seller-b",
            task_id=created.id,
            data=UpdateTaskInput(title="Hack"),
            actor_is_portfolio_manager=False,
        )

    # Gestor da equipe não edita tarefa criada por outro (só o criador edita).
    with pytest.raises(PermissionError):
        uc.update_task(
            user_id="manager",
            task_id=created.id,
            data=UpdateTaskInput(title="Gestor não deve editar", assignee_user_id="seller-b"),
            actor_is_portfolio_manager=True,
        )

    assigned = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(title="Para A", assignee_user_id="seller-a", due_at=now),
        actor_is_portfolio_manager=True,
    )
    assert assigned.created_by_user_id == "manager"
    assert assigned.assignee_user_id == "seller-a"

    with pytest.raises(PermissionError):
        uc.update_task(
            user_id="seller-a",
            task_id=assigned.id,
            data=UpdateTaskInput(title="Assignee não edita"),
        )

    as_creator = uc.update_task(
        user_id="manager",
        task_id=assigned.id,
        data=UpdateTaskInput(title="Gestor criador editou", assignee_user_id="seller-b"),
        actor_is_portfolio_manager=True,
    )
    assert as_creator.title == "Gestor criador editou"
    assert as_creator.assignee_user_id == "seller-b"


def test_delete_task_permissions():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["manager", "seller-a", "seller-b"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    now = datetime.now(timezone.utc)
    mine = uc.create_task(
        user_id="seller-a",
        data=CreateTaskInput(title="Minha", due_at=now),
    )
    assigned = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(title="Atribuída", assignee_user_id="seller-a", due_at=now),
        actor_is_portfolio_manager=True,
    )

    with pytest.raises(PermissionError):
        uc.delete_task(user_id="seller-b", task_id=mine.id)

    with pytest.raises(PermissionError):
        uc.delete_task(user_id="seller-a", task_id=assigned.id)

    deleted_mine = uc.delete_task(user_id="seller-a", task_id=mine.id)
    assert deleted_mine.status == "cancelled"
    assert tasks.get_by_id(mine.id) is None

    deleted_by_creator = uc.delete_task(user_id="manager", task_id=assigned.id)
    assert deleted_by_creator.title == "Atribuída"


def test_assignee_can_complete_but_not_defer():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["manager", "seller-a"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    now = datetime.now(timezone.utc)
    assigned = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(title="Só concluir", assignee_user_id="seller-a", due_at=now),
        actor_is_portfolio_manager=True,
    )
    with pytest.raises(PermissionError):
        uc.defer_task(
            user_id="seller-a",
            task_id=assigned.id,
            due_at=now + timedelta(days=1),
        )
    done = uc.complete_task(user_id="seller-a", task_id=assigned.id)
    assert done.status == "done"


def test_team_worklist_requires_manager():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["u1", "u2"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    with pytest.raises(PermissionError):
        uc.get_worklist(user_id="u1", scope="team", actor_is_portfolio_manager=False)


def test_get_completed_worklist_mine_and_team():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    portfolios = InMemoryPortfolioRepo(["manager", "seller-a", "seller-b"])
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        portfolio_repository=portfolios,  # type: ignore[arg-type]
    )
    now = datetime.now(timezone.utc)
    open_task = uc.create_task(
        user_id="seller-a",
        data=CreateTaskInput(title="Ainda aberta", due_at=now),
    )
    done = uc.create_task(
        user_id="seller-a",
        data=CreateTaskInput(title="Já feita", due_at=now),
    )
    uc.complete_task(user_id="seller-a", task_id=done.id)

    mine = uc.get_completed_worklist(user_id="seller-a")
    assert mine["scope"] == "mine"
    assert mine["count"] == 1
    assert mine["items"][0]["title"] == "Já feita"
    assert mine["items"][0]["status"] == "done"
    assert mine["items"][0]["bucket"] == "done"
    assert str(open_task.id) not in {item["id"] for item in mine["items"]}

    team = uc.get_completed_worklist(
        user_id="manager",
        scope="team",
        actor_is_portfolio_manager=True,
    )
    assert team["scope"] == "team"
    assert team["count"] == 1

    with pytest.raises(PermissionError):
        uc.get_completed_worklist(
            user_id="seller-a",
            scope="team",
            actor_is_portfolio_manager=False,
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


def test_multi_assignees_and_customers_visible_and_any_completes():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    uc = ManageWorklistUseCase(task_repository=tasks, activity_repository=activities)

    created = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(
            title="Visita conjunta",
            assignee_user_ids=["seller-a", "seller-b"],
            customers=[
                TaskCustomerRef("0001", "01", "ACME"),
                TaskCustomerRef("0002", "01", "Beta"),
            ],
        ),
        actor_is_portfolio_manager=True,
    )
    assert created.assignee_user_id == "seller-a"
    assert list(created.resolved_assignee_user_ids()) == ["seller-a", "seller-b"]
    assert len(created.resolved_customers()) == 2
    assert created.to_dict()["customers"][0]["customer_name"] == "ACME"

    mine_a = uc.get_worklist(user_id="seller-a")
    mine_b = uc.get_worklist(user_id="seller-b")
    assert any(item["id"] == str(created.id) for item in mine_a["today"] + mine_a["later"] + mine_a["overdue"])
    assert any(item["id"] == str(created.id) for item in mine_b["today"] + mine_b["later"] + mine_b["overdue"])

    completed = uc.complete_task(user_id="seller-b", task_id=created.id)
    assert completed.status == "done"

    open_task = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(
            title="Reassign multi",
            assignee_user_ids=["seller-a"],
        ),
        actor_is_portfolio_manager=True,
    )
    reassigned = uc.reassign_task(
        user_id="manager",
        task_id=open_task.id,
        assignee_user_ids=["seller-c", "seller-a"],
        actor_is_portfolio_manager=True,
    )
    assert list(reassigned.resolved_assignee_user_ids()) == ["seller-c", "seller-a"]

    updated = uc.update_task(
        user_id="manager",
        task_id=open_task.id,
        data=UpdateTaskInput(
            title="Reassign multi",
            assignee_user_ids=["seller-a", "seller-b"],
            customers=[TaskCustomerRef("0099", "01", "Zeta")],
        ),
        actor_is_portfolio_manager=True,
    )
    assert list(updated.resolved_assignee_user_ids()) == ["seller-a", "seller-b"]
    assert updated.customer_code == "0099"
    assert updated.customers[0].customer_name == "Zeta"


def test_multi_assign_requires_manager():
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    uc = ManageWorklistUseCase(task_repository=tasks, activity_repository=activities)
    with pytest.raises(PermissionError):
        uc.create_task(
            user_id="seller-a",
            data=CreateTaskInput(
                title="Hack",
                assignee_user_ids=["seller-a", "seller-b"],
            ),
            actor_is_portfolio_manager=False,
        )

class FakeGroup:
    def __init__(self, group_id: str, *, active: bool = True) -> None:
        self.id = group_id
        self.kind = "team"
        self.name = f"Grupo {group_id}"
        self.active = active
        self.members = ()


class FakeGroupsRepo:
    def __init__(self, groups: dict[str, FakeGroup], memberships: dict[str, set[str]]) -> None:
        self._groups = groups
        self._memberships = memberships

    def get_by_id(self, group_id: str) -> FakeGroup | None:
        return self._groups.get(str(group_id))

    def list_groups_by_user_id(self, user_id: str) -> list[FakeGroup]:
        ids = self._memberships.get(user_id, set())
        return [self._groups[gid] for gid in ids if gid in self._groups]


def test_task_assignee_groups_visibility_and_completed_by():
    group_id = str(uuid4())
    tasks = InMemoryTaskRepo()
    tasks.user_group_ids = {"member-a": {group_id}, "member-b": {group_id}}
    activities = InMemoryActivityRepo()
    groups = FakeGroupsRepo(
        {group_id: FakeGroup(group_id)},
        {"member-a": {group_id}, "member-b": {group_id}},
    )
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        group_repository=groups,  # type: ignore[arg-type]
    )

    created = uc.create_task(
        user_id="manager",
        data=CreateTaskInput(
            title="Tarefa do grupo",
            assignee_user_ids=["manager"],
            assignee_group_ids=[group_id],
        ),
        actor_is_portfolio_manager=True,
    )
    assert list(created.resolved_assignee_group_ids()) == [group_id]
    assert created.to_dict()["assignee_group_ids"] == [group_id]

    mine = uc.get_worklist(user_id="member-a")
    assert any(
        item["id"] == str(created.id)
        for item in mine["today"] + mine["later"] + mine["overdue"]
    )

    completed = uc.complete_task(user_id="member-b", task_id=created.id)
    assert completed.status == "done"
    assert completed.completed_by_user_id == "member-b"
    assert completed.to_dict()["completed_by_user_id"] == "member-b"


def test_assign_group_requires_manager():
    group_id = str(uuid4())
    tasks = InMemoryTaskRepo()
    activities = InMemoryActivityRepo()
    groups = FakeGroupsRepo({group_id: FakeGroup(group_id)}, {})
    uc = ManageWorklistUseCase(
        task_repository=tasks,
        activity_repository=activities,
        group_repository=groups,  # type: ignore[arg-type]
    )
    with pytest.raises(PermissionError):
        uc.create_task(
            user_id="seller-a",
            data=CreateTaskInput(
                title="Sem manage",
                assignee_group_ids=[group_id],
            ),
            actor_is_portfolio_manager=False,
        )
