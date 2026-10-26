from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask
from tm_app.domain.ports.task_repository_port import TaskOriginContext, TaskRepositoryPort
from tm_app.domain.services.transformometro_task_rules import (
    can_view_task,
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
        room_access: Any | None = None,
    ) -> None:
        """``room_access(user, room_id, authorization) -> bool`` — the
        canonical room read-authorization capability (interaction-room
        owner). When absent, origin context is withheld (fail-closed)."""
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()
        self._room_access = room_access

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
        # O vínculo autorizador é avaliado dentro do próprio UPDATE —
        # sem read-then-write, reatribuição concorrente não concede
        # autorização obsoleta. O responsável atual é lido apenas para
        # compor o payload default quando `assignee_user_id` é omitido.
        actor = _user_id(user)
        if assignee_user_id is None:
            current = self._repo.get(task_id)
            if current is None:
                raise LookupError("Tarefa não encontrada.")
            assignee = current.assignee_user_id
        else:
            assignee = assignee_user_id
        updated = self._repo.update(
            task_id,
            title=normalize_title(title),
            description=normalize_description(description),
            assignee_user_id=normalize_user_id(assignee, field="Responsável"),
            due_date=parse_due_date(due_date),
            actor_id=actor,
            actor_is_manager=self._policy.has_manage(user),
        )
        return updated

    def complete(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        completed = self._repo.complete(
            task_id,
            actor_id=_user_id(user),
            actor_is_manager=self._policy.has_manage(user),
        )
        if completed.status != "completed" or completed.completed_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return completed

    def cancel(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        cancelled = self._repo.cancel(
            task_id,
            actor_id=_user_id(user),
            actor_is_manager=self._policy.has_manage(user),
        )
        if cancelled.status != "cancelled":
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return cancelled

    def get(self, user: Any, task_id: str) -> TransformometroTask:
        self._policy.require_access(user)
        return self._require_authorized(
            user, task_id, can_view_task, "Sem autorização para consultar esta tarefa."
        )

    def list_mine(self, user: Any, *, status: str = "pending") -> list[TransformometroTask]:
        self._policy.require_access(user)
        assignee = _user_id(user)
        statuses = self._statuses(status)
        return self._repo.list_for_assignee(assignee, statuses=statuses)

    def list_delegated(self, user: Any, *, status: str = "pending") -> list[TransformometroTask]:
        self._policy.require_access(user)
        creator = _user_id(user)
        statuses = self._statuses(status)
        return self._repo.list_delegated_by(creator, statuses=statuses)

    def origin_contexts(
        self,
        user: Any,
        task_ids: Sequence[str],
        *,
        authorization: str | None = None,
    ) -> dict[str, TaskOriginContext]:
        """Task visibility != room visibility. Origin metadata is only
        returned for rooms the viewer can actually open under the canonical
        room access check — every active link's external authority
        included. Denied/unavailable/missing-session all suppress; only the
        task itself stays visible. Decisions are evaluated once per unique
        room (no per-task N+1)."""
        self._policy.require_access(user)
        contexts = self._repo.origin_contexts(task_ids)
        allowed = self._allowed_rooms(user, contexts, authorization)
        return {
            task_id: (
                context
                if context.room_id is None or allowed.get(context.room_id)
                else TaskOriginContext()
            )
            for task_id, context in contexts.items()
        }

    def _allowed_rooms(
        self,
        user: Any,
        contexts: dict[str, TaskOriginContext],
        authorization: str | None,
    ) -> dict[str, bool]:
        room_ids = {c.room_id for c in contexts.values() if c.room_id}
        if not room_ids or self._room_access is None:
            return {}
        return {
            room_id: bool(self._room_access(user, room_id, authorization))
            for room_id in room_ids
        }

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

    def _require_authorized(
        self,
        user: Any,
        task_id: str,
        predicate,
        message: str,
    ) -> TransformometroTask:
        task = self._require(task_id)
        actor = _user_id(user)
        if not predicate(actor, self._policy.has_manage(user), task):
            raise AuthorizationDenied(message)
        return task

    @staticmethod
    def _statuses(status: str) -> tuple[TaskStatus, ...]:
        raw = (status or "pending").strip().lower()
        if raw == "all":
            return ("pending", "completed", "cancelled")
        if raw in {"pending", "completed", "cancelled"}:
            return (raw,)  # type: ignore[return-value]
        raise ValueError("Filtro de status inválido.")
