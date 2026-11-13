"""Persistencia G1 de computadores; cada escrita e auditada na mesma transacao."""

from __future__ import annotations

import psycopg
from psycopg import errors as pg_errors

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.application.workstation_ports import WorkstationQuery
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.workstations import WorkstationFields, format_workstation_code
from it_portal_app.infrastructure.persistence.postgres_base import (
    SCHEMA as _S,
    PostgresRepositoryBase,
    archive_assignment,
    escape_like,
    history_row,
)

SORT_SQL = {
    "name": "lower(w.name)",
    "hostname": "lower(w.hostname)",
    "device_kind": "w.device_kind",
    "updated_at": "w.updated_at",
    "created_at": "w.created_at",
}


def identity_conflict() -> ConflictError:
    return ConflictError(
        "workstation_identity_conflict",
        "Ja existe um computador ativo com esse hostname nesta unidade.",
    )


def workstation_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_workstation_code(row["seq"]),
        "name": row["name"],
        "hostname": row["hostname"],
        "ip_address": row["ip_address"],
        "unit_code": row["unit_code"],
        "device_kind": row["device_kind"],
        "department": row["department"],
        "location": row["location"],
        "responsible": row["responsible"],
        "operating_system": row["operating_system"],
        "administrative_status": row["administrative_status"],
        "description": row["description"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


class PostgresWorkstationRepository(PostgresRepositoryBase):
    def _fetch(self, conn: psycopg.Connection, workstation_id: str) -> dict | None:
        row = conn.execute(
            f"SELECT * FROM {_S}.workstations WHERE id = %(id)s", {"id": workstation_id}
        ).fetchone()
        return workstation_row(row) if row else None

    def list_workstations(self, query: WorkstationQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {}
        if query.archived == "active":
            where.append("w.archived_at IS NULL")
        elif query.archived == "archived":
            where.append("w.archived_at IS NOT NULL")
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(w.name ILIKE %(q)s OR w.hostname ILIKE %(q)s "
                "OR w.ip_address ILIKE %(q)s OR w.department ILIKE %(q)s)"
            )
        for column in ("unit_code", "device_kind", "administrative_status"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"w.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order = f"{SORT_SQL[query.sort]} {direction}, w.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.workstations w WHERE {where_sql}", params
            ).fetchone()["total"]
            rows = conn.execute(
                f"SELECT w.* FROM {_S}.workstations w WHERE {where_sql} "
                f"ORDER BY {order} LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [workstation_row(row) for row in rows], int(total)

    def get_workstation(self, workstation_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch(conn, workstation_id)

    def insert_workstation(
        self, workstation_id: str, fields: WorkstationFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        values = fields.as_dict()
        try:
            with self._tx() as conn:
                conn.execute(
                    f"""
                    INSERT INTO {_S}.workstations
                        (id, name, hostname, ip_address, unit_code, device_kind,
                         department, location, responsible, operating_system,
                         administrative_status, description, created_by_id,
                         created_by_name, updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(hostname)s, %(ip_address)s,
                         %(unit_code)s, %(device_kind)s, %(department)s, %(location)s,
                         %(responsible)s, %(operating_system)s, %(administrative_status)s,
                         %(description)s, %(actor_id)s, %(actor_name)s,
                         %(actor_id)s, %(actor_name)s)
                    """,
                    {**values, "id": workstation_id, "actor_id": actor.id, "actor_name": actor.name},
                )
                self._audit(conn, audit, actor)
                created = self._fetch(conn, workstation_id)
        except pg_errors.UniqueViolation as exc:
            raise identity_conflict() from exc
        assert created is not None
        return created

    def update_workstation(
        self,
        workstation_id: str,
        fields: WorkstationFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.workstations SET
                        name = %(name)s, hostname = %(hostname)s,
                        ip_address = %(ip_address)s, unit_code = %(unit_code)s,
                        device_kind = %(device_kind)s, department = %(department)s,
                        location = %(location)s, responsible = %(responsible)s,
                        operating_system = %(operating_system)s,
                        administrative_status = %(administrative_status)s,
                        description = %(description)s, revision = revision + 1,
                        updated_at = now(), updated_by_id = %(actor_id)s,
                        updated_by_name = %(actor_name)s
                    WHERE id = %(id)s AND revision = %(revision)s AND archived_at IS NULL
                    """,
                    {
                        **fields.as_dict(),
                        "id": workstation_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch(conn, workstation_id)
        except pg_errors.UniqueViolation as exc:
            raise identity_conflict() from exc

    def set_workstation_archived(
        self,
        workstation_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        assignment, guard = archive_assignment(archived)
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.workstations SET {assignment},
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                    WHERE id = %(id)s AND revision = %(revision)s AND {guard}
                    """,
                    {
                        "id": workstation_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch(conn, workstation_id)
        except pg_errors.UniqueViolation as exc:
            raise identity_conflict() from exc

    def list_history(self, workstation_id: str, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_S}.audit_events WHERE entity_type = 'workstation' "
                "AND entity_id = %(id)s ORDER BY occurred_at DESC, id DESC "
                "LIMIT %(limit)s",
                {"id": workstation_id, "limit": limit},
            ).fetchall()
        return [history_row(row) for row in rows]
