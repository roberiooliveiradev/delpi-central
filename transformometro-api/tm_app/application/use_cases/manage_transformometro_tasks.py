from __future__ import annotations

from datetime import date
from typing import Any

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask
from tm_app.domain.ports.task_repository_port import TaskRepositoryPort
from tm_app.domain.services.transformometro_task_rules import (
    assert_can_cancel,
    assert_can_complete,
    assert_can_update,
    normalize_description,
    normalize_title,
    normalize_user_id,
    parse_due_date,
)


def _user_id(user: Any) -> str:
    return normalize_user_id(str(getattr(user, "id", "") or ""), field="Usuário autenticado")


class TaskCommandUseCases:
    def __init__(
        self,
        repo: TaskRepositoryPort,
        policy: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()

    def create(
        self,
        user: Any,
        *,
        title: str,
        description: str | None,
        assignee_user_id: str | None,
        due_date: str | date | None,
        source_interaction_message_id: str | None = None,
    ) -> TransformometroTask:
        self._policy.require_access(user)
        actor = _user_id(user)
        assignee = normalize_user_id(assignee_user_id or actor, field="Responsável")
        source_id = (source_interaction_message_id or "").strip() or None
        if source_id and not self._repo.message_exists(source_id):
            raise LookupError("Mensagem de origem não encontrada.")
        created = self._repo.create(
            title=normalize_title(title),
            description=normalize_description(description),
            assignee_user_id=assignee,
            created_by_user_id=actor,
            due_date=parse_due_date(due_date),
            source_interaction_message_id=source_id,
        )
        read_back = self._repo.get(created.id)
        if (
            read_back is None
            or read_back.title != created.title
            or read_back.assignee_user_id != assignee
            or (read_back.source_interaction_message_id or None) != source_id
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return read_back

    def update(
        self,
        user: Any,
        task_id: str,
        *,
        title: str,
        description: str | None,
        assignee_user_id: str | None,
        due_date: str | date | None,
    ) -> TransformometroTask:
        self._policy.require_access(user)
        current = self._require(task_id)
        assert_can_update(current.status)
        updated = self._repo.update(
            task_id,
            title=normalize_title(title),
            description=normalize_description(description),
            assignee_user_id=normalize_user_id(
                assignee_user_id or current.assignee_user_id,
                field="Responsável",
            ),
            due_date=parse_due_date(due_date),
        )
        return updated

    def complete(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        current = self._require(task_id)
        assert_can_complete(current.status)
        completed = self._repo.complete(task_id)
        if completed.status != "completed" or completed.completed_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return completed

    def cancel(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        current = self._require(task_id)
        assert_can_cancel(current.status)
        cancelled = self._repo.cancel(task_id)
        if cancelled.status != "cancelled":
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return cancelled

    def get(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        return self._require(task_id)

    def list_mine(self, user: Any, *, status: str = "pending") -> list[TransformometroTask]:
        self._policy.require_access(user)
        assignee = _user_id(user)
        statuses = self._statuses(status)
        return self._repo.list_for_assignee(assignee, statuses=statuses)

    def list_related_to_process(self, user: Any, processo_id: str) -> list[TransformometroTask]:
        self._policy.require_access(user)
        pid = (processo_id or "").strip()
        if not pid:
            raise ValueError("Processo inválido.")
        return self._repo.list_related_to_process(pid)

    def _require(self, task_id: str) -> TransformometroTask:
        task = self._repo.get(task_id)
        if task is None:
            raise LookupError("Tarefa não encontrada.")
        return task

    @staticmethod
    def _statuses(status: str) -> tuple[TaskStatus, ...]:
        raw = (status or "pending").strip().lower()
        if raw == "all":
            return ("pending", "completed", "cancelled")
        if raw in {"pending", "completed", "cancelled"}:
            return (raw,)  # type: ignore[return-value]
        raise ValueError("Filtro de status inválido.")
