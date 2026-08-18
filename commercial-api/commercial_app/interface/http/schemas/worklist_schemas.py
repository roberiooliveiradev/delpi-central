from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TaskCustomerBody(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    store: str = Field(..., min_length=1, max_length=16)
    name: str | None = Field(default=None, max_length=255)


class CreateTaskBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    task_type: Literal["follow_up", "call", "todo", "email", "visit", "internal", "other"] = "follow_up"
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    customers: list[TaskCustomerBody] | None = Field(
        default=None,
        max_length=20,
        description="Clientes da tarefa (até 20). Singular legado ainda aceito.",
    )
    assignee_user_id: str | None = Field(
        default=None,
        description="Responsável singular (legado). Preferir assignee_user_ids.",
    )
    assignee_user_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Responsáveis (sub Minha Delpi). Default = caller. Outro usuário exige manage.",
    )
    assignee_group_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Grupos operacionais responsáveis (UUID). Exige manage; membership atual define visibilidade.",
    )
    related_entity_type: str | None = Field(
        default=None,
        max_length=64,
        description="Tipo polimórfico leve (ex.: order, customer, interaction_room).",
    )
    related_entity_id: str | None = Field(
        default=None,
        max_length=200,
        description="Identificador do registro relacionado (chave estável).",
    )
    source_interaction_message_id: UUID | None = Field(
        default=None,
        description="Mensagem da sala de interação que originou a tarefa.",
    )

    @model_validator(mode="after")
    def _require_customer_pair(self) -> CreateTaskBody:
        if self.customers:
            return self
        code = (self.customer_code or "").strip()
        store = (self.customer_store or "").strip()
        if (code and not store) or (store and not code):
            raise ValueError("customer_code e customer_store devem ser enviados juntos")
        related_type = (self.related_entity_type or "").strip()
        related_id = (self.related_entity_id or "").strip()
        if (related_type and not related_id) or (related_id and not related_type):
            raise ValueError(
                "related_entity_type e related_entity_id devem ser enviados juntos"
            )
        return self


class UpdateTaskBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    task_type: Literal["follow_up", "call", "todo", "email", "visit", "internal", "other"] = "follow_up"
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    due_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    customers: list[TaskCustomerBody] | None = Field(
        default=None,
        max_length=20,
        description="Clientes da tarefa (até 20). Singular legado ainda aceito.",
    )
    assignee_user_id: str | None = Field(
        default=None,
        description="Novo responsável singular (legado). Preferir assignee_user_ids.",
    )
    assignee_user_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Conjunto de responsáveis (substitui). Troca exige manage de carteiras.",
    )
    assignee_group_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Grupos operacionais responsáveis (substitui). Exige manage.",
    )

    @model_validator(mode="after")
    def _require_customer_pair(self) -> UpdateTaskBody:
        if self.customers:
            return self
        code = (self.customer_code or "").strip()
        store = (self.customer_store or "").strip()
        if (code and not store) or (store and not code):
            raise ValueError("customer_code e customer_store devem ser enviados juntos")
        return self


class CreateActivityBody(BaseModel):
    activity_type: Literal["call", "email", "meeting", "visit", "note", "system"]
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    customer_code: str | None = None
    customer_store: str | None = None
    task_id: UUID | None = None


class DeferTaskBody(BaseModel):
    """Adia a tarefa para a data/hora informada (padrão CRM)."""

    due_at: datetime


class ReassignTaskBody(BaseModel):
    assignee_user_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Responsável singular (legado). Preferir assignee_user_ids.",
    )
    assignee_user_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Substitui o conjunto de responsáveis da tarefa.",
    )
    assignee_group_ids: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Substitui os grupos responsáveis (opcional).",
    )

    @model_validator(mode="after")
    def _require_assignee(self) -> ReassignTaskBody:
        ids = [item.strip() for item in (self.assignee_user_ids or []) if item and item.strip()]
        singular = (self.assignee_user_id or "").strip()
        if not ids and not singular:
            raise ValueError("Informe assignee_user_ids ou assignee_user_id")
        return self
