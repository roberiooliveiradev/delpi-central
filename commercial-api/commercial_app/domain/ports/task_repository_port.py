from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import UUID

from commercial_app.domain.entities.task import (
    CommercialActivity,
    CommercialTask,
    TaskCustomerRef,
)


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
    def list_for_assignees(
        self,
        *,
        assignee_user_ids: Sequence[str],
        status: str | None = "open",
        limit: int = 200,
    ) -> Sequence[CommercialTask]:
        raise NotImplementedError

    @abstractmethod
    def list_by_status(
        self,
        *,
        status: str | None = "open",
        limit: int = 500,
    ) -> Sequence[CommercialTask]:
        """Lista tarefas por status sem filtrar por assignee (fila equipe global)."""
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
        assignee_user_ids: Sequence[str] | None = None,
        customers: Sequence[TaskCustomerRef] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        source_interaction_message_id: UUID | None = None,
        source_message_mentions: Sequence[Mapping[str, Any]] | None = None,
    ) -> CommercialTask:
        raise NotImplementedError

    @abstractmethod
    def complete(
        self,
        *,
        task_id: UUID,
        completed_by_user_id: str | None = None,
    ) -> CommercialTask | None:
        """Marca tarefa aberta como concluída (autorização no use case)."""
        raise NotImplementedError

    @abstractmethod
    def update_due_at(
        self,
        *,
        task_id: UUID,
        due_at: datetime,
    ) -> CommercialTask | None:
        """Atualiza prazo de tarefa aberta (autorização no use case)."""
        raise NotImplementedError

    @abstractmethod
    def reassign(
        self,
        *,
        task_id: UUID,
        new_assignee_user_id: str,
        assignee_user_ids: Sequence[str] | None = None,
        assignee_group_ids: Sequence[str] | None = None,
    ) -> CommercialTask | None:
        """Reatribui tarefa aberta (autorização no use case)."""
        raise NotImplementedError

    @abstractmethod
    def update_description(
        self,
        *,
        task_id: UUID,
        description: str | None,
    ) -> CommercialTask | None:
        """Atualiza observação da tarefa (uso interno pós-create)."""
        raise NotImplementedError

    @abstractmethod
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
        """Atualiza campos de tarefa aberta (autorização no use case)."""
        raise NotImplementedError

    @abstractmethod
    def soft_delete(self, *, task_id: UUID) -> CommercialTask | None:
        """Marca tarefa como excluída (deleted_at); autorização no use case."""
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
