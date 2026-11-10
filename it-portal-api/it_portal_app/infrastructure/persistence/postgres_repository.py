"""Repositório PostgreSQL do Portal de TI (schema `it_portal`).

Cada escrita e seu evento de auditoria são gravados na mesma transação.
Concorrência otimista: updates exigem a `revision` lida pelo cliente.
"""

from __future__ import annotations

from datetime import date

import psycopg
from psycopg import errors as pg_errors

from it_portal_app.application.ports import (
    ActionPlanQuery,
    Actor,
    AuditEvent,
    ServerQuery,
)
from it_portal_app.domain.action_plans import ActionPlanFields, format_action_code
from it_portal_app.domain.catalogs import (
    ACTION_PRIORITIES,
    CRITICALITIES,
    HIGH_CRITICALITIES,
    OPEN_ACTION_STATUSES,
)
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.servers import ServerFields, format_server_code
from it_portal_app.infrastructure.persistence.postgres_base import (
    SCHEMA as _S,
)
from it_portal_app.infrastructure.persistence.postgres_base import (
    PostgresRepositoryBase,
    escape_like,
    history_row,
)

_CRITICALITY_RANK_SQL = (
    "CASE s.criticality "
    + " ".join(f"WHEN '{value}' THEN {index}" for index, value in enumerate(CRITICALITIES))
    + " END"
)
_PRIORITY_RANK_SQL = (
    "CASE a.priority "
    + " ".join(f"WHEN '{value}' THEN {index}" for index, value in enumerate(ACTION_PRIORITIES))
    + " END"
)

_SERVER_SORT_SQL = {
    "name": "lower(s.name)",
    "hostname": "lower(s.hostname)",
    "criticality": _CRITICALITY_RANK_SQL,
    "environment": "s.environment",
    "created_at": "s.created_at",
    "updated_at": "s.updated_at",
}
_ACTION_SORT_SQL = {
    "due_date": "a.due_date",
    "priority": _PRIORITY_RANK_SQL,
    "status": "a.status",
    "created_at": "a.created_at",
    "updated_at": "a.updated_at",
    "title": "lower(a.title)",
}

_OPEN_STATUSES = list(OPEN_ACTION_STATUSES)

_SERVER_SELECT = f"""
    SELECT s.*,
           (SELECT count(*) FROM {_S}.action_plans a
             WHERE a.server_id = s.id AND a.status = ANY(%(open_statuses)s)
           ) AS open_action_count
      FROM {_S}.servers s
"""

_ACTION_SELECT = f"""
    SELECT a.*,
           s.seq AS server_seq,
           s.name AS server_name,
           s.hostname AS server_hostname,
           s.environment AS server_environment,
           s.unit_code AS server_unit_code,
           (s.archived_at IS NOT NULL) AS server_archived
      FROM {_S}.action_plans a
      JOIN {_S}.servers s ON s.id = a.server_id
"""


def _server_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_server_code(row["seq"]),
        "name": row["name"],
        "hostname": row["hostname"],
        "ip_address": row["ip_address"],
        "unit_code": row["unit_code"],
        "location": row["location"],
        "environment": row["environment"],
        "server_type": row["server_type"],
        "purpose": row["purpose"],
        "operating_system": row["operating_system"],
        "criticality": row["criticality"],
        "administrative_status": row["administrative_status"],
        "responsible": row["responsible"],
        "description": row["description"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "open_action_count": int(row.get("open_action_count") or 0),
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _action_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_action_code(row["seq"]),
        "server_id": str(row["server_id"]),
        "server": {
            "id": str(row["server_id"]),
            "code": format_server_code(row["server_seq"]),
            "name": row["server_name"],
            "hostname": row["server_hostname"],
            "environment": row["server_environment"],
            "unit_code": row["server_unit_code"],
            "archived": bool(row["server_archived"]),
        },
        "title": row["title"],
        "description": row["description"],
        "responsible": row["responsible"],
        "priority": row["priority"],
        "status": row["status"],
        "due_date": row["due_date"],
        "completed_at": row["completed_at"],
        "revision": row["revision"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _note_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "server_id": str(row["server_id"]),
        "body": row["body"],
        "author_name": row["author_name"],
        "created_at": row["created_at"],
    }


class PostgresItPortalRepository(PostgresRepositoryBase):
    def _fetch_server(self, conn: psycopg.Connection, server_id: str) -> dict | None:
        row = conn.execute(
            _SERVER_SELECT + " WHERE s.id = %(id)s",
            {"id": server_id, "open_statuses": _OPEN_STATUSES},
        ).fetchone()
        return _server_row(row) if row else None

    def _fetch_action(self, conn: psycopg.Connection, action_plan_id: str) -> dict | None:
        row = conn.execute(
            _ACTION_SELECT + " WHERE a.id = %(id)s", {"id": action_plan_id}
        ).fetchone()
        return _action_row(row) if row else None

    # ---------------------------------------------------------------- servers

    def list_servers(self, query: ServerQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {"open_statuses": _OPEN_STATUSES}
        if query.archived == "active":
            where.append("s.archived_at IS NULL")
        elif query.archived == "archived":
            where.append("s.archived_at IS NOT NULL")
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(s.name ILIKE %(q)s OR s.hostname ILIKE %(q)s OR s.ip_address ILIKE %(q)s)"
            )
        for column in ("unit_code", "environment", "criticality"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"s.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order_sql = f"{_SERVER_SORT_SQL[query.sort]} {direction}, s.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.servers s WHERE {where_sql}", params
            ).fetchone()["total"]
            rows = conn.execute(
                _SERVER_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql}"
                + " LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_server_row(row) for row in rows], int(total)

    def get_server(self, server_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_server(conn, server_id)

    def insert_server(
        self, server_id: str, fields: ServerFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        values = fields.as_dict()
        try:
            with self._tx() as conn:
                conn.execute(
                    f"""
                    INSERT INTO {_S}.servers
                        (id, name, hostname, ip_address, unit_code, location,
                         environment, server_type, purpose, operating_system,
                         criticality, administrative_status, responsible, description,
                         created_by_id, created_by_name, updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(hostname)s, %(ip_address)s, %(unit_code)s,
                         %(location)s, %(environment)s, %(server_type)s, %(purpose)s,
                         %(operating_system)s, %(criticality)s, %(administrative_status)s,
                         %(responsible)s, %(description)s,
                         %(actor_id)s, %(actor_name)s, %(actor_id)s, %(actor_name)s)
                    """,
                    {**values, "id": server_id, "actor_id": actor.id, "actor_name": actor.name},
                )
                self._audit(conn, audit, actor)
                created = self._fetch_server(conn, server_id)
        except pg_errors.UniqueViolation as exc:
            raise _identity_conflict() from exc
        assert created is not None
        return created

    def update_server(
        self,
        server_id: str,
        fields: ServerFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        values = fields.as_dict()
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.servers SET
                        name = %(name)s, hostname = %(hostname)s,
                        ip_address = %(ip_address)s, unit_code = %(unit_code)s,
                        location = %(location)s, environment = %(environment)s,
                        server_type = %(server_type)s, purpose = %(purpose)s,
                        operating_system = %(operating_system)s,
                        criticality = %(criticality)s,
                        administrative_status = %(administrative_status)s,
                        responsible = %(responsible)s, description = %(description)s,
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s
                       AND archived_at IS NULL
                    """,
                    {
                        **values,
                        "id": server_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_server(conn, server_id)
        except pg_errors.UniqueViolation as exc:
            raise _identity_conflict() from exc

    def set_server_archived(
        self,
        server_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        if archived:
            assignment = (
                "archived_at = now(), archived_by_id = %(actor_id)s, "
                "archived_by_name = %(actor_name)s"
            )
            guard = "archived_at IS NULL"
        else:
            assignment = "archived_at = NULL, archived_by_id = NULL, archived_by_name = NULL"
            guard = "archived_at IS NOT NULL"
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.servers SET {assignment},
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND {guard}
                    """,
                    {
                        "id": server_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_server(conn, server_id)
        except pg_errors.UniqueViolation as exc:
            raise _identity_conflict() from exc

    def count_open_action_plans(self, server_id: str) -> int:
        with self._tx() as conn:
            row = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.action_plans "
                "WHERE server_id = %s AND status = ANY(%s)",
                (server_id, _OPEN_STATUSES),
            ).fetchone()
        return int(row["total"])

    # ------------------------------------------------------------------ notes

    def list_notes(self, server_id: str) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_S}.server_notes WHERE server_id = %s "
                "ORDER BY created_at ASC, id ASC",
                (server_id,),
            ).fetchall()
        return [_note_row(row) for row in rows]

    def insert_note(
        self, note_id: str, server_id: str, body: str, actor: Actor, audit: AuditEvent
    ) -> dict:
        with self._tx() as conn:
            row = conn.execute(
                f"""
                INSERT INTO {_S}.server_notes (id, server_id, body, author_id, author_name)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (note_id, server_id, body, actor.id, actor.name),
            ).fetchone()
            self._audit(conn, audit, actor)
        return _note_row(row)

    def list_server_history(self, server_id: str, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_S}.audit_events "
                "WHERE server_id = %(id)s OR subject_ids @> ARRAY[%(id)s]::uuid[] "
                "ORDER BY occurred_at DESC, id DESC LIMIT %(limit)s",
                {"id": server_id, "limit": limit},
            ).fetchall()
        return [history_row(row) for row in rows]

    # ----------------------------------------------------------- action plans

    def list_action_plans(self, query: ActionPlanQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {"today": query.today}
        if query.statuses:
            params["statuses"] = list(query.statuses)
            where.append("a.status = ANY(%(statuses)s)")
        if query.server_id:
            params["server_id"] = query.server_id
            where.append("a.server_id = %(server_id)s")
        if query.priority:
            params["priority"] = query.priority
            where.append("a.priority = %(priority)s")
        if query.overdue_only:
            params["open_statuses"] = _OPEN_STATUSES
            where.append(
                "a.status = ANY(%(open_statuses)s) AND a.due_date IS NOT NULL "
                "AND a.due_date < %(today)s"
            )
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(a.title ILIKE %(q)s OR s.name ILIKE %(q)s OR s.hostname ILIKE %(q)s)"
            )
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        nulls = "NULLS LAST" if query.sort == "due_date" else ""
        order_sql = f"{_ACTION_SORT_SQL[query.sort]} {direction} {nulls}, a.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.action_plans a "
                f"JOIN {_S}.servers s ON s.id = a.server_id WHERE {where_sql}",
                params,
            ).fetchone()["total"]
            rows = conn.execute(
                _ACTION_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql}"
                + " LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_action_row(row) for row in rows], int(total)

    def get_action_plan(self, action_plan_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_action(conn, action_plan_id)

    def insert_action_plan(
        self,
        action_plan_id: str,
        server_id: str,
        fields: ActionPlanFields,
        status: str,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict:
        with self._tx() as conn:
            conn.execute(
                f"""
                INSERT INTO {_S}.action_plans
                    (id, server_id, title, description, responsible, priority, status,
                     due_date, created_by_id, created_by_name, updated_by_id,
                     updated_by_name)
                VALUES (%(id)s, %(server_id)s, %(title)s, %(description)s,
                        %(responsible)s, %(priority)s, %(status)s, %(due_date)s,
                        %(actor_id)s, %(actor_name)s, %(actor_id)s, %(actor_name)s)
                """,
                {
                    **fields.as_dict(),
                    "id": action_plan_id,
                    "server_id": server_id,
                    "status": status,
                    "actor_id": actor.id,
                    "actor_name": actor.name,
                },
            )
            self._audit(conn, audit, actor)
            created = self._fetch_action(conn, action_plan_id)
        assert created is not None
        return created

    def update_action_plan(
        self,
        action_plan_id: str,
        fields: ActionPlanFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        with self._tx() as conn:
            cur = conn.execute(
                f"""
                UPDATE {_S}.action_plans SET
                    title = %(title)s, description = %(description)s,
                    responsible = %(responsible)s, priority = %(priority)s,
                    due_date = %(due_date)s,
                    revision = revision + 1, updated_at = now(),
                    updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                 WHERE id = %(id)s AND revision = %(revision)s
                """,
                {
                    **fields.as_dict(),
                    "id": action_plan_id,
                    "revision": expected_revision,
                    "actor_id": actor.id,
                    "actor_name": actor.name,
                },
            )
            if cur.rowcount != 1:
                return None
            self._audit(conn, audit, actor)
            return self._fetch_action(conn, action_plan_id)

    def update_action_plan_status(
        self,
        action_plan_id: str,
        status: str,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        with self._tx() as conn:
            cur = conn.execute(
                f"""
                UPDATE {_S}.action_plans SET
                    status = %(status)s::varchar,
                    completed_at = CASE WHEN %(status)s::varchar = 'done'
                                        THEN now() ELSE NULL END,
                    revision = revision + 1, updated_at = now(),
                    updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                 WHERE id = %(id)s AND revision = %(revision)s
                """,
                {
                    "status": status,
                    "id": action_plan_id,
                    "revision": expected_revision,
                    "actor_id": actor.id,
                    "actor_name": actor.name,
                },
            )
            if cur.rowcount != 1:
                return None
            self._audit(conn, audit, actor)
            return self._fetch_action(conn, action_plan_id)

    # -------------------------------------------------------------- dashboard

    def dashboard_counts(self, today: date) -> dict:
        with self._tx() as conn:
            row = conn.execute(
                f"""
                SELECT
                  (SELECT count(*) FROM {_S}.servers WHERE archived_at IS NULL)
                    AS servers_total,
                  (SELECT count(*) FROM {_S}.servers
                    WHERE archived_at IS NULL AND criticality = ANY(%(high)s))
                    AS servers_high_or_critical,
                  (SELECT count(*) FROM {_S}.action_plans
                    WHERE status = ANY(%(open)s)) AS actions_open,
                  (SELECT count(*) FROM {_S}.action_plans
                    WHERE status = ANY(%(open)s) AND due_date < %(today)s)
                    AS actions_overdue
                """,
                {"high": list(HIGH_CRITICALITIES), "open": _OPEN_STATUSES, "today": today},
            ).fetchone()
        return {key: int(value) for key, value in row.items()}

    def recent_servers(self, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                _SERVER_SELECT
                + " WHERE s.archived_at IS NULL ORDER BY s.created_at DESC, s.seq DESC"
                + " LIMIT %(limit)s",
                {"open_statuses": _OPEN_STATUSES, "limit": limit},
            ).fetchall()
        return [_server_row(row) for row in rows]

    def attention_action_plans(self, today: date, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                _ACTION_SELECT
                + f"""
                 WHERE a.status = ANY(%(open)s)
                 ORDER BY (a.due_date IS NOT NULL AND a.due_date < %(today)s) DESC,
                          a.due_date ASC NULLS LAST,
                          {_PRIORITY_RANK_SQL} DESC,
                          a.seq ASC
                 LIMIT %(limit)s
                """,
                {"open": _OPEN_STATUSES, "today": today, "limit": limit},
            ).fetchall()
        return [_action_row(row) for row in rows]


def _identity_conflict() -> ConflictError:
    return ConflictError(
        "server_identity_conflict",
        "Já existe um servidor ativo com este hostname nesta unidade e ambiente.",
        {"fields": {"hostname": "Hostname já cadastrado nesta unidade e ambiente."}},
    )
