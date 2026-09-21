from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence

from tm_app.domain.entities.transformometro_task import TaskStatus, TransformometroTask


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
    ) -> TransformometroTask:
        raise NotImplementedError

    @abstractmethod
    def complete(self, task_id: str) -> TransformometroTask:
        raise NotImplementedError

    @abstractmethod
    def cancel(self, task_id: str) -> TransformometroTask:
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
    def list_related_to_process(self, processo_id: str) -> list[TransformometroTask]:
        """Tasks linked via interaction message → room → processo (no manual join in UI)."""
        raise NotImplementedError
