from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Sequence
from uuid import UUID


@dataclass(frozen=True)
class TaskCustomerRef:
    customer_code: str
    customer_store: str
    customer_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
        }


@dataclass(frozen=True)
class TaskAssigneeGroupRef:
    id: str
    kind: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
        }


@dataclass(frozen=True)
class CommercialTask:
    id: UUID
    title: str
    description: str | None
    task_type: str
    status: str
    priority: str
    due_at: datetime | None
    completed_at: datetime | None
    assignee_user_id: str
    created_by_user_id: str
    customer_code: str | None
    customer_store: str | None
    created_at: datetime
    updated_at: datetime
    assignee_user_ids: tuple[str, ...] = field(default_factory=tuple)
    customers: tuple[TaskCustomerRef, ...] = field(default_factory=tuple)
    assignee_group_ids: tuple[str, ...] = field(default_factory=tuple)
    assignee_groups: tuple[TaskAssigneeGroupRef, ...] = field(default_factory=tuple)
    completed_by_user_id: str | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    source_interaction_message_id: UUID | None = None

    def resolved_assignee_user_ids(self) -> tuple[str, ...]:
        if self.assignee_user_ids:
            return self.assignee_user_ids
        uid = (self.assignee_user_id or "").strip()
        return (uid,) if uid else ()

    def resolved_assignee_group_ids(self) -> tuple[str, ...]:
        if self.assignee_group_ids:
            return self.assignee_group_ids
        if self.assignee_groups:
            return tuple(group.id for group in self.assignee_groups if group.id)
        return ()

    def resolved_customers(self) -> tuple[TaskCustomerRef, ...]:
        if self.customers:
            return self.customers
        code = (self.customer_code or "").strip()
        store = (self.customer_store or "").strip()
        if code and store:
            return (TaskCustomerRef(customer_code=code, customer_store=store),)
        return ()

    def to_dict(self) -> dict[str, Any]:
        assignees = list(self.resolved_assignee_user_ids())
        customers = [item.to_dict() for item in self.resolved_customers()]
        primary = customers[0] if customers else None
        group_ids = list(self.resolved_assignee_group_ids())
        groups = [item.to_dict() for item in self.assignee_groups]
        if not groups and group_ids:
            groups = [{"id": gid, "kind": "", "name": ""} for gid in group_ids]
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_by_user_id": self.completed_by_user_id,
            "assignee_user_id": assignees[0] if assignees else self.assignee_user_id,
            "assignee_user_ids": assignees,
            "assignee_group_ids": group_ids,
            "assignee_groups": groups,
            "created_by_user_id": self.created_by_user_id,
            "customer_code": primary["customer_code"] if primary else self.customer_code,
            "customer_store": primary["customer_store"] if primary else self.customer_store,
            "customer_name": primary.get("customer_name") if primary else None,
            "customers": customers,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "source_interaction_message_id": (
                str(self.source_interaction_message_id)
                if self.source_interaction_message_id
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(frozen=True)
class CommercialActivity:
    id: UUID
    activity_type: str
    subject: str | None
    body: str | None
    occurred_at: datetime
    actor_user_id: str
    customer_code: str | None
    customer_store: str | None
    task_id: UUID | None
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "activity_type": self.activity_type,
            "subject": self.subject,
            "body": self.body,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "actor_user_id": self.actor_user_id,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "task_id": str(self.task_id) if self.task_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def normalize_assignee_user_ids(
    *,
    assignee_user_ids: Sequence[str] | None,
    assignee_user_id: str | None,
    fallback_user_id: str,
    max_items: int = 20,
) -> list[str]:
    """Normaliza lista de assignees; singular legado vira lista de 1."""
    raw: list[str] = []
    if assignee_user_ids:
        raw.extend(str(item).strip() for item in assignee_user_ids if str(item).strip())
    elif assignee_user_id and str(assignee_user_id).strip():
        raw.append(str(assignee_user_id).strip())
    if not raw:
        fallback = (fallback_user_id or "").strip()
        if fallback:
            raw.append(fallback)
    deduped: list[str] = []
    seen: set[str] = set()
    for uid in raw:
        if uid in seen:
            continue
        seen.add(uid)
        deduped.append(uid)
        if len(deduped) >= max_items:
            break
    return deduped


def normalize_assignee_group_ids(
    *,
    assignee_group_ids: Sequence[str] | None,
    max_items: int = 20,
) -> list[str]:
    """Normaliza UUIDs de grupos atribuídos à tarefa (sem expandir membros)."""
    if not assignee_group_ids:
        return []
    deduped: list[str] = []
    seen: set[str] = set()
    for raw in assignee_group_ids:
        gid = str(raw or "").strip()
        if not gid or gid in seen:
            continue
        seen.add(gid)
        deduped.append(gid)
        if len(deduped) >= max_items:
            break
    return deduped


def normalize_task_customers(
    *,
    customers: Sequence[TaskCustomerRef | dict[str, Any]] | None,
    customer_code: str | None,
    customer_store: str | None,
    customer_name: str | None = None,
    max_items: int = 20,
) -> list[TaskCustomerRef]:
    """Normaliza clientes da tarefa; singular legado vira lista de 1."""
    raw: list[TaskCustomerRef] = []
    if customers:
        for item in customers:
            if isinstance(item, TaskCustomerRef):
                code = item.customer_code.strip()
                store = item.customer_store.strip()
                name = (item.customer_name or "").strip() or None
            else:
                code = str(
                    item.get("customer_code") or item.get("code") or ""
                ).strip()
                store = str(
                    item.get("customer_store") or item.get("store") or ""
                ).strip()
                name_raw = item.get("customer_name") or item.get("name")
                name = str(name_raw).strip() if name_raw else None
            if code and store:
                raw.append(
                    TaskCustomerRef(
                        customer_code=code,
                        customer_store=store,
                        customer_name=name,
                    )
                )
    else:
        code = (customer_code or "").strip()
        store = (customer_store or "").strip()
        name = (customer_name or "").strip() or None
        if code and store:
            raw.append(
                TaskCustomerRef(
                    customer_code=code,
                    customer_store=store,
                    customer_name=name,
                )
            )
    deduped: list[TaskCustomerRef] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        key = (item.customer_code, item.customer_store)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max_items:
            break
    return deduped
