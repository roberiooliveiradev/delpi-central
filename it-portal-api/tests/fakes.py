"""Repositório em memória — exclusivo de testes de serviço/HTTP.

Reproduz as garantias observáveis do adapter Postgres (revisão otimista,
unicidade ativa por unidade+ambiente+hostname, auditoria por escrita).
A paridade real é coberta por `test_postgres_integration.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from it_portal_app.application.ports import (
    ActionPlanQuery,
    Actor,
    AuditEvent,
    ServerQuery,
)
from it_portal_app.domain.action_plans import ActionPlanFields, format_action_code
from it_portal_app.domain.catalogs import (
    CRITICALITY_RANK,
    HIGH_CRITICALITIES,
    OPEN_ACTION_STATUSES,
)
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.servers import ServerFields, format_server_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InMemoryItPortalRepository:
    servers: dict[str, dict] = field(default_factory=dict)
    notes: list[dict] = field(default_factory=list)
    actions: dict[str, dict] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)
    _server_seq: int = 0
    _action_seq: int = 0

    def _record(self, audit: AuditEvent, actor: Actor) -> None:
        self.audit.append(
            {
                "id": f"evt-{len(self.audit) + 1}",
                "entity_type": audit.entity_type,
                "entity_id": audit.entity_id,
                "server_id": audit.server_id,
                "event_type": audit.event_type,
                "changes": audit.changes,
                "actor_name": actor.name,
                "actor_id": actor.id,
                "occurred_at": _now(),
            }
        )

    def _ensure_unique(self, server_id: str, fields: dict) -> None:
        for other in self.servers.values():
            if other["id"] == server_id or other["archived"]:
                continue
            if (
                other["unit_code"] == fields["unit_code"]
                and other["environment"] == fields["environment"]
                and other["hostname"].lower() == fields["hostname"].lower()
            ):
                raise ConflictError("server_identity_conflict", "duplicado")

    def _view(self, server: dict) -> dict:
        open_count = sum(
            1
            for action in self.actions.values()
            if action["server_id"] == server["id"]
            and action["status"] in OPEN_ACTION_STATUSES
        )
        return {**server, "open_action_count": open_count}

    def _action_view(self, action: dict) -> dict:
        server = self.servers[action["server_id"]]
        return {
            **action,
            "server": {
                "id": server["id"],
                "code": server["code"],
                "name": server["name"],
                "hostname": server["hostname"],
                "environment": server["environment"],
                "unit_code": server["unit_code"],
                "archived": server["archived"],
            },
        }

    # servers
    def list_servers(self, query: ServerQuery):
        items = list(self.servers.values())
        if query.archived == "active":
            items = [s for s in items if not s["archived"]]
        elif query.archived == "archived":
            items = [s for s in items if s["archived"]]
        if query.q:
            needle = query.q.lower()
            items = [
                s
                for s in items
                if needle in s["name"].lower()
                or needle in s["hostname"].lower()
                or needle in (s["ip_address"] or "")
            ]
        for column in ("unit_code", "environment", "criticality"):
            value = getattr(query, column)
            if value:
                items = [s for s in items if s[column] == value]

        def key(server: dict):
            if query.sort == "criticality":
                primary = CRITICALITY_RANK[server["criticality"]]
            elif query.sort in ("name", "hostname"):
                primary = server[query.sort].lower()
            else:
                primary = server[query.sort]
            return (primary, server["seq"])

        items.sort(key=key, reverse=query.direction == "desc")
        start = (query.page - 1) * query.page_size
        page = items[start : start + query.page_size]
        return [self._view(s) for s in page], len(items)

    def get_server(self, server_id: str):
        server = self.servers.get(server_id)
        return self._view(server) if server else None

    def insert_server(self, server_id, fields: ServerFields, actor, audit):
        values = fields.as_dict()
        self._ensure_unique(server_id, values)
        self._server_seq += 1
        now = _now()
        self.servers[server_id] = {
            **values,
            "id": server_id,
            "seq": self._server_seq,
            "code": format_server_code(self._server_seq),
            "revision": 1,
            "archived": False,
            "archived_at": None,
            "archived_by_name": None,
            "created_at": now,
            "created_by_name": actor.name,
            "updated_at": now,
            "updated_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_server(server_id)

    def update_server(self, server_id, fields, expected_revision, actor, audit):
        server = self.servers[server_id]
        if server["revision"] != expected_revision or server["archived"]:
            return None
        values = fields.as_dict()
        self._ensure_unique(server_id, values)
        server.update(values)
        server.update(revision=server["revision"] + 1, updated_at=_now(), updated_by_name=actor.name)
        self._record(audit, actor)
        return self.get_server(server_id)

    def set_server_archived(self, server_id, archived, expected_revision, actor, audit):
        server = self.servers[server_id]
        if server["revision"] != expected_revision or server["archived"] == archived:
            return None
        if not archived:
            self._ensure_unique(server_id, server)
        server.update(
            archived=archived,
            archived_at=_now() if archived else None,
            archived_by_name=actor.name if archived else None,
            revision=server["revision"] + 1,
            updated_at=_now(),
            updated_by_name=actor.name,
        )
        self._record(audit, actor)
        return self.get_server(server_id)

    def count_open_action_plans(self, server_id):
        return self.get_server(server_id)["open_action_count"]

    # notes
    def list_notes(self, server_id):
        return [n for n in self.notes if n["server_id"] == server_id]

    def insert_note(self, note_id, server_id, body, actor, audit):
        note = {
            "id": note_id,
            "server_id": server_id,
            "body": body,
            "author_name": actor.name,
            "author_id": actor.id,
            "created_at": _now(),
        }
        self.notes.append(note)
        self._record(audit, actor)
        return note

    def list_server_history(self, server_id, limit):
        events = [e for e in self.audit if e["server_id"] == server_id]
        return list(reversed(events))[:limit]

    # action plans
    def list_action_plans(self, query: ActionPlanQuery):
        items = list(self.actions.values())
        if query.statuses:
            items = [a for a in items if a["status"] in query.statuses]
        if query.server_id:
            items = [a for a in items if a["server_id"] == query.server_id]
        if query.priority:
            items = [a for a in items if a["priority"] == query.priority]
        if query.overdue_only:
            items = [
                a
                for a in items
                if a["status"] in OPEN_ACTION_STATUSES
                and a["due_date"]
                and a["due_date"] < query.today
            ]
        items.sort(key=lambda a: (a["due_date"] or date.max, a["seq"]))
        start = (query.page - 1) * query.page_size
        return [self._action_view(a) for a in items[start : start + query.page_size]], len(items)

    def get_action_plan(self, action_plan_id):
        action = self.actions.get(action_plan_id)
        return self._action_view(action) if action else None

    def insert_action_plan(self, action_plan_id, server_id, fields: ActionPlanFields, status, actor, audit):
        self._action_seq += 1
        now = _now()
        self.actions[action_plan_id] = {
            **fields.as_dict(),
            "id": action_plan_id,
            "seq": self._action_seq,
            "code": format_action_code(self._action_seq),
            "server_id": server_id,
            "status": status,
            "completed_at": None,
            "revision": 1,
            "created_at": now,
            "created_by_name": actor.name,
            "updated_at": now,
            "updated_by_name": actor.name,
        }
        self._record(audit, actor)
        return self.get_action_plan(action_plan_id)

    def update_action_plan(self, action_plan_id, fields, expected_revision, actor, audit):
        action = self.actions[action_plan_id]
        if action["revision"] != expected_revision:
            return None
        action.update(fields.as_dict())
        action.update(revision=action["revision"] + 1, updated_at=_now(), updated_by_name=actor.name)
        self._record(audit, actor)
        return self.get_action_plan(action_plan_id)

    def update_action_plan_status(self, action_plan_id, status, expected_revision, actor, audit):
        action = self.actions[action_plan_id]
        if action["revision"] != expected_revision:
            return None
        action.update(
            status=status,
            completed_at=_now() if status == "done" else None,
            revision=action["revision"] + 1,
            updated_at=_now(),
            updated_by_name=actor.name,
        )
        self._record(audit, actor)
        return self.get_action_plan(action_plan_id)

    # dashboard
    def dashboard_counts(self, today):
        active = [s for s in self.servers.values() if not s["archived"]]
        open_actions = [a for a in self.actions.values() if a["status"] in OPEN_ACTION_STATUSES]
        return {
            "servers_total": len(active),
            "servers_high_or_critical": sum(
                1 for s in active if s["criticality"] in HIGH_CRITICALITIES
            ),
            "actions_open": len(open_actions),
            "actions_overdue": sum(
                1 for a in open_actions if a["due_date"] and a["due_date"] < today
            ),
        }

    def recent_servers(self, limit):
        active = [s for s in self.servers.values() if not s["archived"]]
        active.sort(key=lambda s: s["seq"], reverse=True)
        return [self._view(s) for s in active[:limit]]

    def attention_action_plans(self, today, limit):
        open_actions = [a for a in self.actions.values() if a["status"] in OPEN_ACTION_STATUSES]
        open_actions.sort(
            key=lambda a: (
                not (a["due_date"] and a["due_date"] < today),
                a["due_date"] or date.max,
                a["seq"],
            )
        )
        return [self._action_view(a) for a in open_actions[:limit]]
