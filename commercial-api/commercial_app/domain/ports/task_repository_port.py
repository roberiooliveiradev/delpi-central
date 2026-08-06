from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence
from uuid import UUID

from commercial_app.domain.entities.task import CommercialActivity, CommercialTask


class TaskRepositoryPort(ABC):
    @abstractmethod
    def list_for_assignee(
        self,
        *,
        assignee_user_id: str,
        status: str | None = "open",
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[CommercialTask]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, task_id: UUID) -> CommercialTask | None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def complete(self, *, task_id: UUID, actor_user_id: str) -> CommercialTask | None:
        raise NotImplementedError

    @abstractmethod
    def update_due_at(
        self,
        *,
        task_id: UUID,
        actor_user_id: str,
        due_at: datetime,
    ) -> CommercialTask | None:
        raise NotImplementedError


class ActivityRepositoryPort(ABC):
    @abstractmethod
    def list_for_customer(
        self,
        *,
        customer_code: str,
        customer_store: str,
        limit: int = 50,
    ) -> Sequence[CommercialActivity]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
