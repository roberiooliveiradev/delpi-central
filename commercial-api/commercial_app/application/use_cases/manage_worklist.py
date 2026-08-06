from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from commercial_app.domain.entities.task import CommercialActivity, CommercialTask
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.customer_avatar_repository_port import AuditLogRepositoryPort
from commercial_app.domain.ports.seller_portfolio_repository_port import SellerPortfolioRepositoryPort
from commercial_app.domain.ports.task_repository_port import (
    ActivityRepositoryPort,
    TaskRepositoryPort,
)

WorklistScope = Literal["mine", "team"]


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    description: str | None = None
    task_type: str = "follow_up"
    priority: str = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    assignee_user_id: str | None = None


@dataclass(frozen=True)
class UpdateTaskInput:
    title: str
    description: str | None = None
    task_type: str = "follow_up"
    priority: str = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    assignee_user_id: str | None = None


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


def _bucket_tasks(
    open_tasks: list[CommercialTask],
    *,
    attachment_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    start = _start_of_today_utc()
    end = _end_of_today_utc()
    counts = attachment_counts or {}
    overdue: list[dict[str, Any]] = []
    today: list[dict[str, Any]] = []
    later: list[dict[str, Any]] = []
    for task in open_tasks:
        payload = task.to_dict()
        payload["attachment_count"] = int(counts.get(str(task.id), 0))
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


class ManageWorklistUseCase:
    def __init__(
        self,
        *,
        task_repository: TaskRepositoryPort,
        activity_repository: ActivityRepositoryPort,
        audit_repository: AuditLogRepositoryPort | None = None,
        portfolio_repository: SellerPortfolioRepositoryPort | None = None,
        attachment_repository: AttachmentRepositoryPort | None = None,
    ) -> None:
        self._tasks = task_repository
        self._activities = activity_repository
        self._audit = audit_repository
        self._portfolios = portfolio_repository
        self._attachments = attachment_repository

    def _attachment_counts(self, tasks: list[CommercialTask]) -> dict[str, int]:
        if self._attachments is None or not tasks:
            return {}
        return self._attachments.count_for_owners(
            owner_type="task",
            owner_ids=[str(task.id) for task in tasks],
        )
    def team_user_ids(self) -> set[str]:
        if self._portfolios is None:
            return set()
        return {
            str(item.user_id).strip()
            for item in self._portfolios.list_portfolios(active_only=True)
            if str(item.user_id or "").strip()
        }

    def _assert_team_member(self, user_id: str) -> None:
        team = self.team_user_ids()
        if user_id not in team:
            raise ValueError("Responsável deve ter carteira ativa no Comercial.")

    def _can_act_on_task(
        self,
        *,
        task: CommercialTask,
        actor_user_id: str,
        actor_is_portfolio_manager: bool,
    ) -> bool:
        if task.assignee_user_id == actor_user_id:
            return True
        if not actor_is_portfolio_manager:
            return False
        return task.assignee_user_id in self.team_user_ids()

    def _can_edit_task(self, *, task: CommercialTask, actor_user_id: str) -> bool:
        """Só o criador edita campos/anexos via formulário — assignee de tarefa atribuída não."""
        return (task.created_by_user_id or "").strip() == (actor_user_id or "").strip()

    def get_worklist(
        self,
        *,
        user_id: str,
        scope: WorklistScope = "mine",
        assignee_user_id: str | None = None,
        actor_is_portfolio_manager: bool = False,
    ) -> dict[str, Any]:
        normalized_scope: WorklistScope = "team" if scope == "team" else "mine"
        filter_assignee = (assignee_user_id or "").strip() or None

        if normalized_scope == "team":
            if not actor_is_portfolio_manager:
                raise PermissionError("Sem permissão para ver a fila da equipe.")
            team_ids = sorted(self.team_user_ids())
            if not team_ids:
                open_tasks: list[CommercialTask] = []
            elif filter_assignee:
                if filter_assignee not in team_ids:
                    raise ValueError("Filtro de responsável fora da equipe.")
                open_tasks = list(
                    self._tasks.list_for_assignee(
                        assignee_user_id=filter_assignee,
                        status="open",
                        limit=200,
                    )
                )
            else:
                open_tasks = list(
                    self._tasks.list_for_assignees(
                        assignee_user_ids=team_ids,
                        status="open",
                        limit=500,
                    )
                )
            payload = _bucket_tasks(
                open_tasks,
                attachment_counts=self._attachment_counts(open_tasks),
            )
            payload["scope"] = "team"
            payload["team_user_ids"] = team_ids
            return payload

        open_tasks = list(
            self._tasks.list_for_assignee(assignee_user_id=user_id, status="open", limit=200)
        )
        payload = _bucket_tasks(
            open_tasks,
            attachment_counts=self._attachment_counts(open_tasks),
        )
        payload["scope"] = "mine"
        return payload

    def get_completed_worklist(
        self,
        *,
        user_id: str,
        scope: WorklistScope = "mine",
        assignee_user_id: str | None = None,
        actor_is_portfolio_manager: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Lista tarefas concluídas (status=done), mais recentes primeiro."""
        normalized_scope: WorklistScope = "team" if scope == "team" else "mine"
        filter_assignee = (assignee_user_id or "").strip() or None
        capped = max(1, min(int(limit or 50), 100))

        if normalized_scope == "team":
            if not actor_is_portfolio_manager:
                raise PermissionError("Sem permissão para ver a fila da equipe.")
            team_ids = sorted(self.team_user_ids())
            if not team_ids:
                done_tasks: list[CommercialTask] = []
            elif filter_assignee:
                if filter_assignee not in team_ids:
                    raise ValueError("Filtro de responsável fora da equipe.")
                done_tasks = list(
                    self._tasks.list_for_assignee(
                        assignee_user_id=filter_assignee,
                        status="done",
                        limit=capped,
                    )
                )
            else:
                done_tasks = list(
                    self._tasks.list_for_assignees(
                        assignee_user_ids=team_ids,
                        status="done",
                        limit=capped,
                    )
                )
            counts = self._attachment_counts(done_tasks)
            items = []
            for task in done_tasks:
                payload = task.to_dict()
                payload["attachment_count"] = int(counts.get(str(task.id), 0))
                payload["bucket"] = "done"
                items.append(payload)
            return {
                "items": items,
                "count": len(items),
                "scope": "team",
                "team_user_ids": team_ids,
                "limit": capped,
            }

        done_tasks = list(
            self._tasks.list_for_assignee(
                assignee_user_id=user_id,
                status="done",
                limit=capped,
            )
        )
        counts = self._attachment_counts(done_tasks)
        items = []
        for task in done_tasks:
            payload = task.to_dict()
            payload["attachment_count"] = int(counts.get(str(task.id), 0))
            payload["bucket"] = "done"
            items.append(payload)
        return {
            "items": items,
            "count": len(items),
            "scope": "mine",
            "limit": capped,
        }

    def list_tasks(self, *, user_id: str, status: str | None = "open") -> list[CommercialTask]:
        return list(self._tasks.list_for_assignee(assignee_user_id=user_id, status=status))

    def create_task(
        self,
        *,
        user_id: str,
        data: CreateTaskInput,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialTask:
        title = (data.title or "").strip()
        if not title:
            raise ValueError("Título da tarefa é obrigatório.")
        task_type = (data.task_type or "follow_up").strip() or "follow_up"
        priority = (data.priority or "normal").strip() or "normal"
        description = (data.description or "").strip() or None
        assignee = (data.assignee_user_id or user_id).strip() or user_id
        if assignee != user_id:
            if not actor_is_portfolio_manager:
                raise PermissionError("Sem permissão para atribuir tarefa a outro usuário.")
            self._assert_team_member(assignee)

        task = self._tasks.create(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_at=data.due_at,
            assignee_user_id=assignee,
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
                payload={"title": task.title, "assignee_user_id": task.assignee_user_id},
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

    def update_task(
        self,
        *,
        user_id: str,
        task_id: UUID,
        data: UpdateTaskInput,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialTask:
        existing = self._tasks.get_by_id(task_id)
        if existing is None or existing.status != "open":
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if not self._can_edit_task(task=existing, actor_user_id=user_id):
            raise PermissionError(
                "Só quem criou a tarefa pode editá-la. Tarefas atribuídas a você "
                "podem ser adiadas ou concluídas."
            )

        title = (data.title or "").strip()
        if not title:
            raise ValueError("Título da tarefa é obrigatório.")
        task_type = (data.task_type or existing.task_type or "follow_up").strip() or "follow_up"
        priority = (data.priority or existing.priority or "normal").strip() or "normal"
        description = (data.description or "").strip() or None
        due_at = data.due_at
        if due_at is not None and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)

        assignee = (data.assignee_user_id or existing.assignee_user_id).strip() or existing.assignee_user_id
        if assignee != existing.assignee_user_id:
            if not actor_is_portfolio_manager:
                raise PermissionError("Sem permissão para reatribuir ao editar.")
            self._assert_team_member(assignee)

        customer_code = (data.customer_code or "").strip() or None
        customer_store = (data.customer_store or "").strip() or None
        if customer_code and not customer_store:
            raise ValueError("Informe a loja do cliente junto com o código.")
        if customer_store and not customer_code:
            raise ValueError("Informe o código do cliente junto com a loja.")

        task = self._tasks.update(
            task_id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_at=due_at,
            customer_code=customer_code,
            customer_store=customer_store,
            assignee_user_id=assignee,
        )
        if task is None:
            raise LookupError("Tarefa não encontrada ou já concluída.")

        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.task.updated",
                entity_type="task",
                entity_id=str(task.id),
                payload={
                    "title": task.title,
                    "assignee_user_id": task.assignee_user_id,
                    "priority": task.priority,
                    "task_type": task.task_type,
                },
            )
        self._activities.create(
            activity_type="system",
            subject=f"Tarefa atualizada: {task.title}",
            body=description,
            occurred_at=None,
            actor_user_id=user_id,
            customer_code=task.customer_code,
            customer_store=task.customer_store,
            task_id=task.id,
        )
        return task

    def complete_task(
        self,
        *,
        user_id: str,
        task_id: UUID,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialTask:
        existing = self._tasks.get_by_id(task_id)
        if existing is None or existing.status != "open":
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if not self._can_act_on_task(
            task=existing,
            actor_user_id=user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        ):
            raise PermissionError("Sem permissão para concluir esta tarefa.")
        task = self._tasks.complete(task_id=task_id)
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

    def defer_task(
        self,
        *,
        user_id: str,
        task_id: UUID,
        due_at: datetime,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialTask:
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        existing = self._tasks.get_by_id(task_id)
        if existing is None or existing.status != "open":
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if not self._can_act_on_task(
            task=existing,
            actor_user_id=user_id,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        ):
            raise PermissionError("Sem permissão para adiar esta tarefa.")
        task = self._tasks.update_due_at(task_id=task_id, due_at=due_at)
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

    def reassign_task(
        self,
        *,
        user_id: str,
        task_id: UUID,
        new_assignee_user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> CommercialTask:
        new_assignee = (new_assignee_user_id or "").strip()
        if not new_assignee:
            raise ValueError("Informe o novo responsável.")
        existing = self._tasks.get_by_id(task_id)
        if existing is None or existing.status != "open":
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if not actor_is_portfolio_manager:
            raise PermissionError("Sem permissão para reatribuir tarefas.")
        self._assert_team_member(new_assignee)
        if existing.assignee_user_id == new_assignee:
            return existing

        # Gestor só reatribui tarefas da equipe (inclui as próprias)
        if existing.assignee_user_id not in self.team_user_ids():
            raise PermissionError("Tarefa fora do escopo da equipe.")

        task = self._tasks.reassign(task_id=task_id, new_assignee_user_id=new_assignee)
        if task is None:
            raise LookupError("Tarefa não encontrada ou já concluída.")
        if self._audit:
            self._audit.append(
                actor_user_id=user_id,
                action="commercial.task.reassigned",
                entity_type="task",
                entity_id=str(task.id),
                payload={
                    "from_assignee_user_id": existing.assignee_user_id,
                    "to_assignee_user_id": new_assignee,
                },
            )
        self._activities.create(
            activity_type="system",
            subject=f"Tarefa reatribuída: {task.title}",
            body=f"De {existing.assignee_user_id} para {new_assignee}",
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
