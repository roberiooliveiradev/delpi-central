"""Casos de uso dos planos de ação vinculados a servidores."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import date

from it_portal_app.application.ports import (
    ACTION_SORT_KEYS,
    ActionPlanQuery,
    Actor,
    AuditEvent,
    ItPortalRepository,
)
from it_portal_app.domain.action_plans import (
    ACTION_FIELD_NAMES,
    build_action_plan_fields,
    ensure_transition,
    ensure_valid_status,
    is_overdue,
)
from it_portal_app.domain.catalogs import ACTION_PRIORITIES
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.servers import diff_fields

MAX_PAGE_SIZE = 100


def _revision_conflict() -> ConflictError:
    return ConflictError(
        "revision_conflict",
        "O plano de ação foi alterado por outra pessoa. Recarregue e tente novamente.",
    )


class ActionPlanService:
    def __init__(
        self,
        repository: ItPortalRepository,
        today: Callable[[], date],
    ):
        self._repo = repository
        self._today = today

    def _with_overdue(self, plan: dict, today: date) -> dict:
        return {**plan, "is_overdue": is_overdue(plan["status"], plan["due_date"], today)}

    def list_action_plans(self, query: ActionPlanQuery) -> dict:
        errors: dict[str, str] = {}
        for status in query.statuses:
            try:
                ensure_valid_status(status)
            except ValidationError:
                errors["status"] = "Status inválido."
        if query.priority and query.priority not in ACTION_PRIORITIES:
            errors["priority"] = "Prioridade inválida."
        if query.sort not in ACTION_SORT_KEYS:
            errors["sort"] = "Ordenação inválida."
        if query.direction not in ("asc", "desc"):
            errors["direction"] = "Direção inválida."
        if errors:
            raise ValidationError("invalid_query", "Filtros inválidos.", {"fields": errors})
        q = (query.q or "").strip() or None
        normalized = replace(
            query,
            q=q[:120] if q else None,
            page=max(1, query.page),
            page_size=min(MAX_PAGE_SIZE, max(1, query.page_size)),
        )
        items, total = self._repo.list_action_plans(normalized)
        return {
            "items": [self._with_overdue(item, query.today) for item in items],
            "total": total,
            "page": normalized.page,
            "page_size": normalized.page_size,
        }

    def get_action_plan(self, action_plan_id: str) -> dict:
        plan = self._repo.get_action_plan(action_plan_id)
        if plan is None:
            raise NotFoundError("action_plan_not_found", "Plano de ação não encontrado.")
        return self._with_overdue(plan, self._today())

    def create_action_plan(self, server_id: str, raw: dict, actor: Actor) -> dict:
        server = self._repo.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        if server["archived"]:
            raise ConflictError(
                "server_archived",
                "Servidor arquivado: restaure o cadastro antes de criar planos de ação.",
            )
        fields = build_action_plan_fields(raw)
        action_plan_id = str(uuid.uuid4())
        audit = AuditEvent(
            entity_type="action_plan",
            entity_id=action_plan_id,
            server_id=server_id,
            event_type="action_plan_created",
            changes={"fields": {**fields.as_dict(), "status": "pending"}},
        )
        created = self._repo.insert_action_plan(
            action_plan_id, server_id, fields, "pending", actor, audit
        )
        return self._with_overdue(created, self._today())

    def update_action_plan(
        self, action_plan_id: str, raw: dict, expected_revision: int, actor: Actor
    ) -> dict:
        current = self.get_action_plan(action_plan_id)
        fields = build_action_plan_fields(raw)
        changes = diff_fields(current, fields.as_dict(), ACTION_FIELD_NAMES)
        if not changes:
            if current["revision"] != expected_revision:
                raise _revision_conflict()
            return current
        audit = AuditEvent(
            entity_type="action_plan",
            entity_id=action_plan_id,
            server_id=current["server_id"],
            event_type="action_plan_updated",
            changes=changes,
        )
        updated = self._repo.update_action_plan(
            action_plan_id, fields, expected_revision, actor, audit
        )
        if updated is None:
            raise _revision_conflict()
        return self._with_overdue(updated, self._today())

    def change_status(
        self, action_plan_id: str, status: str, expected_revision: int, actor: Actor
    ) -> dict:
        current = self.get_action_plan(action_plan_id)
        ensure_transition(current["status"], status)
        audit = AuditEvent(
            entity_type="action_plan",
            entity_id=action_plan_id,
            server_id=current["server_id"],
            event_type="action_plan_status_changed",
            changes={"status": {"from": current["status"], "to": status}},
        )
        updated = self._repo.update_action_plan_status(
            action_plan_id, status, expected_revision, actor, audit
        )
        if updated is None:
            raise _revision_conflict()
        return self._with_overdue(updated, self._today())
