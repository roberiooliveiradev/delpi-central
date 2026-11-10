"""Repositório PostgreSQL de serviços, instâncias de banco e vínculos (E2A).

Escrita + auditoria na mesma transação. Vínculos e instâncias revalidam, sob
`FOR SHARE`, que os recursos referenciados existem e estão ativos — o
arquivamento concorrente não deixa vínculo novo apontando para arquivado.
"""

from __future__ import annotations

import psycopg
from psycopg import errors as pg_errors

from it_portal_app.application.inventory_rules import reference_not_found
from it_portal_app.application.ports import (
    Actor,
    AuditEvent,
    DatabaseQuery,
    ServiceQuery,
)
from it_portal_app.domain.catalogs import CRITICALITIES
from it_portal_app.domain.database_instances import (
    DatabaseInstanceFields,
    format_database_code,
)
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.inventory_links import ConsumerFields, HostingFields
from it_portal_app.domain.it_services import ServiceFields, format_service_code
from it_portal_app.domain.servers import format_server_code
from it_portal_app.infrastructure.persistence.postgres_base import (
    SCHEMA as _S,
)
from it_portal_app.infrastructure.persistence.postgres_base import (
    PostgresRepositoryBase,
    escape_like,
    history_row,
)

LINK_LIST_LIMIT = 500


def _rank_sql(column: str) -> str:
    return (
        f"CASE {column} "
        + " ".join(f"WHEN '{value}' THEN {index}" for index, value in enumerate(CRITICALITIES))
        + " END"
    )


_SERVICE_SORT_SQL = {
    "name": "lower(v.name)",
    "criticality": _rank_sql("v.criticality"),
    "environment": "v.environment",
    "created_at": "v.created_at",
    "updated_at": "v.updated_at",
}
_DATABASE_SORT_SQL = {
    "name": "lower(d.name)",
    "dbms": "d.dbms",
    "criticality": _rank_sql("d.criticality"),
    "environment": "d.environment",
    "created_at": "d.created_at",
    "updated_at": "d.updated_at",
}

_SERVICE_SELECT = f"""
    SELECT v.*,
           (SELECT count(*) FROM {_S}.service_hostings h WHERE h.service_id = v.id)
             AS hosting_count,
           (SELECT count(*) FROM {_S}.database_consumers c WHERE c.service_id = v.id)
             AS database_count
      FROM {_S}.services v
"""

_DATABASE_SELECT = f"""
    SELECT d.*,
           s.seq AS server_seq, s.name AS server_name, s.hostname AS server_hostname,
           s.environment AS server_environment, s.unit_code AS server_unit_code,
           (s.archived_at IS NOT NULL) AS server_archived,
           (SELECT count(*) FROM {_S}.database_consumers c
             WHERE c.database_instance_id = d.id) AS consumer_count
      FROM {_S}.database_instances d
      JOIN {_S}.servers s ON s.id = d.server_id
"""

_HOSTING_SELECT = f"""
    SELECT h.*,
           v.seq AS service_seq, v.name AS service_name, v.service_kind,
           v.environment AS service_environment, v.criticality AS service_criticality,
           (v.archived_at IS NOT NULL) AS service_archived,
           s.seq AS server_seq, s.name AS server_name, s.hostname AS server_hostname,
           s.environment AS server_environment, s.unit_code AS server_unit_code,
           (s.archived_at IS NOT NULL) AS server_archived
      FROM {_S}.service_hostings h
      JOIN {_S}.services v ON v.id = h.service_id
      JOIN {_S}.servers s ON s.id = h.server_id
"""

_CONSUMER_SELECT = f"""
    SELECT c.*,
           d.seq AS database_seq, d.name AS database_name, d.dbms,
           d.environment AS database_environment, d.criticality AS database_criticality,
           (d.archived_at IS NOT NULL) AS database_archived,
           v.seq AS service_seq, v.name AS service_name, v.service_kind,
           v.environment AS service_environment, v.criticality AS service_criticality,
           (v.archived_at IS NOT NULL) AS service_archived
      FROM {_S}.database_consumers c
      JOIN {_S}.database_instances d ON d.id = c.database_instance_id
      JOIN {_S}.services v ON v.id = c.service_id
"""

_CONFLICTS = {
    "services_active_identity_uq": ConflictError(
        "service_identity_conflict",
        "Já existe um serviço ativo com este nome nesta unidade e ambiente.",
        {"fields": {"name": "Nome já cadastrado nesta unidade e ambiente."}},
    ),
    "database_instances_active_identity_uq": ConflictError(
        "database_identity_conflict",
        "Já existe uma instância ativa com este nome neste servidor.",
        {"fields": {"name": "Nome já cadastrado neste servidor."}},
    ),
    "service_hostings_pair_uq": ConflictError(
        "service_hosting_exists", "Este serviço já está vinculado a este servidor."
    ),
    "database_consumers_pair_uq": ConflictError(
        "database_consumer_exists", "Este serviço já está vinculado a esta instância de banco."
    ),
}


def _conflict(exc: pg_errors.UniqueViolation) -> ConflictError:
    constraint = getattr(exc.diag, "constraint_name", None)
    known = _CONFLICTS.get(constraint or "")
    if known is not None:
        return ConflictError(known.code, known.message, known.details)
    return ConflictError("inventory_conflict", "Registro duplicado.")


def _service_summary(row: dict) -> dict:
    return {
        "id": str(row["service_id"]),
        "code": format_service_code(row["service_seq"]),
        "name": row["service_name"],
        "service_kind": row["service_kind"],
        "environment": row["service_environment"],
        "criticality": row["service_criticality"],
        "archived": bool(row["service_archived"]),
    }


def _server_summary(row: dict) -> dict:
    return {
        "id": str(row["server_id"]),
        "code": format_server_code(row["server_seq"]),
        "name": row["server_name"],
        "hostname": row["server_hostname"],
        "environment": row["server_environment"],
        "unit_code": row["server_unit_code"],
        "archived": bool(row["server_archived"]),
    }


def _service_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_service_code(row["seq"]),
        "name": row["name"],
        "description": row["description"],
        "service_kind": row["service_kind"],
        "service_type": row["service_type"],
        "technology": row["technology"],
        "environment": row["environment"],
        "unit_code": row["unit_code"],
        "port": row["port"],
        "criticality": row["criticality"],
        "responsible": row["responsible"],
        "administrative_status": row["administrative_status"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "hosting_count": int(row.get("hosting_count") or 0),
        "database_count": int(row.get("database_count") or 0),
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _database_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_database_code(row["seq"]),
        "name": row["name"],
        "dbms": row["dbms"],
        "version": row["version"],
        "server_id": str(row["server_id"]),
        "server": _server_summary(row),
        "port": row["port"],
        "environment": row["environment"],
        "purpose": row["purpose"],
        "criticality": row["criticality"],
        "responsible": row["responsible"],
        "administrative_status": row["administrative_status"],
        "technical_notes": row["technical_notes"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "consumer_count": int(row.get("consumer_count") or 0),
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _hosting_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "service_id": str(row["service_id"]),
        "server_id": str(row["server_id"]),
        "runtime": row["runtime"],
        "instance_name": row["instance_name"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "service": _service_summary(row),
        "server": _server_summary(row),
    }


def _consumer_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "database_instance_id": str(row["database_instance_id"]),
        "service_id": str(row["service_id"]),
        "notes": row["notes"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "database": {
            "id": str(row["database_instance_id"]),
            "code": format_database_code(row["database_seq"]),
            "name": row["database_name"],
            "dbms": row["dbms"],
            "environment": row["database_environment"],
            "criticality": row["database_criticality"],
            "archived": bool(row["database_archived"]),
        },
        "service": _service_summary(row),
    }


def _archive_assignment(archived: bool) -> tuple[str, str]:
    if archived:
        return (
            "archived_at = now(), archived_by_id = %(actor_id)s, "
            "archived_by_name = %(actor_name)s",
            "archived_at IS NULL",
        )
    return (
        "archived_at = NULL, archived_by_id = NULL, archived_by_name = NULL",
        "archived_at IS NOT NULL",
    )


class PostgresInventoryRepository(PostgresRepositoryBase):
    # --------------------------------------------------------------- guards

    @staticmethod
    def _require_active(
        conn: psycopg.Connection,
        table: str,
        row_id: str,
        *,
        field: str,
        missing_message: str,
        archived_error: ConflictError,
    ) -> None:
        row = conn.execute(
            f"SELECT archived_at FROM {_S}.{table} WHERE id = %s FOR SHARE", (row_id,)
        ).fetchone()
        if row is None:
            raise reference_not_found(field, missing_message)
        if row["archived_at"] is not None:
            raise ConflictError(archived_error.code, archived_error.message)

    def _require_active_server(self, conn: psycopg.Connection, server_id: str) -> None:
        self._require_active(
            conn,
            "servers",
            server_id,
            field="server_id",
            missing_message="Servidor não encontrado.",
            archived_error=ConflictError(
                "server_archived", "Servidor arquivado: restaure o cadastro antes de vinculá-lo."
            ),
        )

    def _require_active_service(self, conn: psycopg.Connection, service_id: str) -> None:
        self._require_active(
            conn,
            "services",
            service_id,
            field="service_id",
            missing_message="Serviço não encontrado.",
            archived_error=ConflictError(
                "service_archived", "Serviço arquivado: restaure o cadastro antes de alterá-lo."
            ),
        )

    # ------------------------------------------------------------- services

    def _fetch_service(self, conn: psycopg.Connection, service_id: str) -> dict | None:
        row = conn.execute(_SERVICE_SELECT + " WHERE v.id = %s", (service_id,)).fetchone()
        return _service_row(row) if row else None

    def list_services(self, query: ServiceQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {}
        if query.archived == "active":
            where.append("v.archived_at IS NULL")
        elif query.archived == "archived":
            where.append("v.archived_at IS NOT NULL")
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append("(v.name ILIKE %(q)s OR v.technology ILIKE %(q)s)")
        for column in ("service_kind", "environment", "unit_code", "criticality"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"v.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order_sql = f"{_SERVICE_SORT_SQL[query.sort]} {direction}, v.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.services v WHERE {where_sql}", params
            ).fetchone()["total"]
            rows = conn.execute(
                _SERVICE_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql} LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_service_row(row) for row in rows], int(total)

    def get_service(self, service_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_service(conn, service_id)

    def insert_service(
        self, service_id: str, fields: ServiceFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                conn.execute(
                    f"""
                    INSERT INTO {_S}.services
                        (id, name, description, service_kind, service_type, technology,
                         environment, unit_code, port, criticality, responsible,
                         administrative_status, created_by_id, created_by_name,
                         updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(description)s, %(service_kind)s,
                         %(service_type)s, %(technology)s, %(environment)s, %(unit_code)s,
                         %(port)s, %(criticality)s, %(responsible)s,
                         %(administrative_status)s, %(actor_id)s, %(actor_name)s,
                         %(actor_id)s, %(actor_name)s)
                    """,
                    {
                        **fields.as_dict(),
                        "id": service_id,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                self._audit(conn, audit, actor)
                created = self._fetch_service(conn, service_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        assert created is not None
        return created

    def update_service(
        self,
        service_id: str,
        fields: ServiceFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.services SET
                        name = %(name)s, description = %(description)s,
                        service_kind = %(service_kind)s, service_type = %(service_type)s,
                        technology = %(technology)s, environment = %(environment)s,
                        unit_code = %(unit_code)s, port = %(port)s,
                        criticality = %(criticality)s, responsible = %(responsible)s,
                        administrative_status = %(administrative_status)s,
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND archived_at IS NULL
                    """,
                    {
                        **fields.as_dict(),
                        "id": service_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_service(conn, service_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    def set_service_archived(
        self,
        service_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        assignment, guard = _archive_assignment(archived)
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.services SET {assignment},
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND {guard}
                    """,
                    {
                        "id": service_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_service(conn, service_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    # ------------------------------------------------------------- hostings

    def list_hostings(
        self, *, service_id: str | None = None, server_id: str | None = None
    ) -> list[dict]:
        where, params = [], {"limit": LINK_LIST_LIMIT}
        if service_id:
            where.append("h.service_id = %(service_id)s")
            params["service_id"] = service_id
        if server_id:
            where.append("h.server_id = %(server_id)s")
            params["server_id"] = server_id
        where_sql = " AND ".join(where) or "TRUE"
        with self._tx() as conn:
            rows = conn.execute(
                _HOSTING_SELECT
                + f" WHERE {where_sql} ORDER BY lower(v.name), lower(s.name), h.id"
                + " LIMIT %(limit)s",
                params,
            ).fetchall()
        return [_hosting_row(row) for row in rows]

    def get_hosting(self, hosting_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(_HOSTING_SELECT + " WHERE h.id = %s", (hosting_id,)).fetchone()
        return _hosting_row(row) if row else None

    def insert_hosting(
        self, hosting_id: str, fields: HostingFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                self._require_active_service(conn, fields.service_id)
                self._require_active_server(conn, fields.server_id)
                conn.execute(
                    f"""
                    INSERT INTO {_S}.service_hostings
                        (id, service_id, server_id, runtime, instance_name, notes,
                         created_by_id, created_by_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        hosting_id,
                        fields.service_id,
                        fields.server_id,
                        fields.runtime,
                        fields.instance_name,
                        fields.notes,
                        actor.id,
                        actor.name,
                    ),
                )
                self._audit(conn, audit, actor)
                row = conn.execute(_HOSTING_SELECT + " WHERE h.id = %s", (hosting_id,)).fetchone()
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        return _hosting_row(row)

    def delete_hosting(self, hosting_id: str, actor: Actor, audit: AuditEvent) -> bool:
        with self._tx() as conn:
            cur = conn.execute(f"DELETE FROM {_S}.service_hostings WHERE id = %s", (hosting_id,))
            if cur.rowcount != 1:
                return False
            self._audit(conn, audit, actor)
        return True

    # ------------------------------------------------------------ databases

    def _fetch_database(self, conn: psycopg.Connection, database_id: str) -> dict | None:
        row = conn.execute(_DATABASE_SELECT + " WHERE d.id = %s", (database_id,)).fetchone()
        return _database_row(row) if row else None

    def list_databases(self, query: DatabaseQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {}
        if query.archived == "active":
            where.append("d.archived_at IS NULL")
        elif query.archived == "archived":
            where.append("d.archived_at IS NOT NULL")
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(d.name ILIKE %(q)s OR d.version ILIKE %(q)s OR s.name ILIKE %(q)s "
                "OR s.hostname ILIKE %(q)s)"
            )
        for column in ("dbms", "environment", "criticality", "server_id"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"d.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order_sql = f"{_DATABASE_SORT_SQL[query.sort]} {direction}, d.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.database_instances d "
                f"JOIN {_S}.servers s ON s.id = d.server_id WHERE {where_sql}",
                params,
            ).fetchone()["total"]
            rows = conn.execute(
                _DATABASE_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql} LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_database_row(row) for row in rows], int(total)

    def get_database(self, database_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_database(conn, database_id)

    def insert_database(
        self,
        database_id: str,
        fields: DatabaseInstanceFields,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict:
        try:
            with self._tx() as conn:
                self._require_active_server(conn, fields.server_id)
                conn.execute(
                    f"""
                    INSERT INTO {_S}.database_instances
                        (id, name, dbms, version, server_id, port, environment, purpose,
                         criticality, responsible, administrative_status, technical_notes,
                         created_by_id, created_by_name, updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(dbms)s, %(version)s, %(server_id)s, %(port)s,
                         %(environment)s, %(purpose)s, %(criticality)s, %(responsible)s,
                         %(administrative_status)s, %(technical_notes)s,
                         %(actor_id)s, %(actor_name)s, %(actor_id)s, %(actor_name)s)
                    """,
                    {
                        **fields.as_dict(),
                        "id": database_id,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                self._audit(conn, audit, actor)
                created = self._fetch_database(conn, database_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        assert created is not None
        return created

    def update_database(
        self,
        database_id: str,
        fields: DatabaseInstanceFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        try:
            with self._tx() as conn:
                current = conn.execute(
                    f"SELECT server_id FROM {_S}.database_instances WHERE id = %s FOR UPDATE",
                    (database_id,),
                ).fetchone()
                if current is None:
                    return None
                if str(current["server_id"]) != fields.server_id:
                    self._require_active_server(conn, fields.server_id)
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.database_instances SET
                        name = %(name)s, dbms = %(dbms)s, version = %(version)s,
                        server_id = %(server_id)s, port = %(port)s,
                        environment = %(environment)s, purpose = %(purpose)s,
                        criticality = %(criticality)s, responsible = %(responsible)s,
                        administrative_status = %(administrative_status)s,
                        technical_notes = %(technical_notes)s,
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND archived_at IS NULL
                    """,
                    {
                        **fields.as_dict(),
                        "id": database_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_database(conn, database_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    def set_database_archived(
        self,
        database_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        assignment, guard = _archive_assignment(archived)
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.database_instances SET {assignment},
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND {guard}
                    """,
                    {
                        "id": database_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_database(conn, database_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    # ------------------------------------------------------------ consumers

    def list_consumers(
        self, *, database_id: str | None = None, service_id: str | None = None
    ) -> list[dict]:
        where, params = [], {"limit": LINK_LIST_LIMIT}
        if database_id:
            where.append("c.database_instance_id = %(database_id)s")
            params["database_id"] = database_id
        if service_id:
            where.append("c.service_id = %(service_id)s")
            params["service_id"] = service_id
        where_sql = " AND ".join(where) or "TRUE"
        with self._tx() as conn:
            rows = conn.execute(
                _CONSUMER_SELECT
                + f" WHERE {where_sql} ORDER BY lower(d.name), lower(v.name), c.id"
                + " LIMIT %(limit)s",
                params,
            ).fetchall()
        return [_consumer_row(row) for row in rows]

    def get_consumer(self, consumer_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(_CONSUMER_SELECT + " WHERE c.id = %s", (consumer_id,)).fetchone()
        return _consumer_row(row) if row else None

    def insert_consumer(
        self, consumer_id: str, fields: ConsumerFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                self._require_active(
                    conn,
                    "database_instances",
                    fields.database_instance_id,
                    field="database_instance_id",
                    missing_message="Instância de banco não encontrada.",
                    archived_error=ConflictError(
                        "database_instance_archived",
                        "Instância arquivada: restaure o cadastro antes de alterá-la.",
                    ),
                )
                self._require_active_service(conn, fields.service_id)
                conn.execute(
                    f"""
                    INSERT INTO {_S}.database_consumers
                        (id, database_instance_id, service_id, notes,
                         created_by_id, created_by_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        consumer_id,
                        fields.database_instance_id,
                        fields.service_id,
                        fields.notes,
                        actor.id,
                        actor.name,
                    ),
                )
                self._audit(conn, audit, actor)
                row = conn.execute(
                    _CONSUMER_SELECT + " WHERE c.id = %s", (consumer_id,)
                ).fetchone()
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        return _consumer_row(row)

    def delete_consumer(self, consumer_id: str, actor: Actor, audit: AuditEvent) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                f"DELETE FROM {_S}.database_consumers WHERE id = %s", (consumer_id,)
            )
            if cur.rowcount != 1:
                return False
            self._audit(conn, audit, actor)
        return True

    # -------------------------------------------------------------- history

    def list_subject_history(self, subject_id: str, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_S}.audit_events "
                "WHERE entity_id = %(id)s OR subject_ids @> ARRAY[%(id)s]::uuid[] "
                "ORDER BY occurred_at DESC, id DESC LIMIT %(limit)s",
                {"id": subject_id, "limit": limit},
            ).fetchall()
        return [history_row(row) for row in rows]
