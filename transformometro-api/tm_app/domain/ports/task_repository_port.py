from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask


@dataclass(frozen=True)
class TaskOriginContext:
    """Origem canônica da tarefa: sala de interação → processo, quando houver."""

    room_id: str | None = None
    context_label: str | None = None


class TaskRepositoryPort(ABC):
    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def message_exists(self, message_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, task_id: str) -> TransformometroTask | None:
        raise NotImplementedError

    @abstractmethod
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
        """Atomic write: relationship authorization is enforced inside the
        mutating statement, never from a read taken earlier. Raises
        LookupError (missing), PermissionError (actor not authorized at
        write time) or ValueError (incompatible status)."""
        raise NotImplementedError

    @abstractmethod
    def complete(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        """Same atomic contract as ``update``."""
        raise NotImplementedError

    @abstractmethod
    def cancel(
        self, task_id: str, *, actor_id: str, actor_is_manager: bool
    ) -> TransformometroTask:
        """Same atomic contract as ``update``."""
        raise NotImplementedError

    @abstractmethod
    def list_for_assignee(
        self,
        assignee_user_id: str,
        *,
        statuses: Sequence[TaskStatus],
    ) -> list[TransformometroTask]:
        raise NotImplementedError

    @abstractmethod
    def list_delegated_by(
        self,
        creator_user_id: str,
        *,
        statuses: Sequence[TaskStatus],
    ) -> list[TransformometroTask]:
        """Tasks the creator delegated to someone else (assignee != creator)."""
        raise NotImplementedError

    @abstractmethod
    def origin_contexts(
        self,
        task_ids: Sequence[str],
    ) -> dict[str, TaskOriginContext]:
        """Resolve room/process origin CANDIDATES for tasks created from
        interaction messages. This is a structural projection, NOT room
        authorization: callers must gate exposure through the canonical
        room access check before returning these values."""
        raise NotImplementedError

    @abstractmethod
    def list_related_to_process(self, processo_id: str) -> list[TransformometroTask]:
        """Tasks linked via interaction message → room → processo (no manual join in UI)."""
        raise NotImplementedError
