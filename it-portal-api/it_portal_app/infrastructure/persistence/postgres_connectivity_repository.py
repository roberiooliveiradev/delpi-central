"""Repositório PostgreSQL de redes, conectividade, integrações e dependências (E2B).

Escrita + auditoria na mesma transação. Vínculos e integrações revalidam, sob
`FOR SHARE`, que os recursos referenciados existem e estão ativos; o IP de um
servidor na rede é validado contra o CIDR travado na mesma transação.
"""

from __future__ import annotations

import psycopg
from psycopg import errors as pg_errors

from it_portal_app.application.network_inventory import network_links_outside_cidr_error
from it_portal_app.application.ports import (
    Actor,
    AuditEvent,
    IntegrationQuery,
    NetworkQuery,
)
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.integrations import (
    IntegrationFields,
    ServiceDependencyFields,
    format_integration_code,
)
from it_portal_app.domain.it_services import format_service_code
from it_portal_app.domain.networks import (
    NetworkFields,
    ServerNetworkLinkFields,
    format_network_code,
    validate_link_address,
)
from it_portal_app.domain.servers import format_server_code
from it_portal_app.infrastructure.persistence.postgres_base import SCHEMA as _S
from it_portal_app.infrastructure.persistence.postgres_base import (
    PostgresRepositoryBase,
    archive_assignment,
    escape_like,
    rank_sql,
)

LINK_LIST_LIMIT = 500

_NETWORK_SORT_SQL = {
    "name": "lower(n.name)",
    "criticality": rank_sql("n.criticality"),
    "environment": "n.environment",
    "created_at": "n.created_at",
    "updated_at": "n.updated_at",
}
_INTEGRATION_SORT_SQL = {
    "name": "lower(i.name)",
    "criticality": rank_sql("i.criticality"),
    "protocol": "i.protocol",
    "created_at": "i.created_at",
    "updated_at": "i.updated_at",
}

_NETWORK_SELECT = f"""
    SELECT n.*,
           (SELECT count(*) FROM {_S}.server_network_links l WHERE l.network_id = n.id)
             AS server_count
      FROM {_S}.networks n
"""

_LINK_SELECT = f"""
    SELECT l.*,
           s.seq AS server_seq, s.name AS server_name, s.hostname AS server_hostname,
           s.environment AS server_environment, s.unit_code AS server_unit_code,
           (s.archived_at IS NOT NULL) AS server_archived,
           n.seq AS network_seq, n.name AS network_name, n.cidr AS network_cidr,
           n.vlan_id AS network_vlan_id, n.network_scope AS network_scope,
           n.environment AS network_environment, n.unit_code AS network_unit_code,
           (n.archived_at IS NOT NULL) AS network_archived
      FROM {_S}.server_network_links l
      JOIN {_S}.servers s ON s.id = l.server_id
      JOIN {_S}.networks n ON n.id = l.network_id
"""


def _service_columns(alias: str, prefix: str) -> str:
    return (
        f"{alias}.seq AS {prefix}_seq, {alias}.name AS {prefix}_name, "
        f"{alias}.service_kind AS {prefix}_kind, {alias}.environment AS {prefix}_environment, "
        f"{alias}.criticality AS {prefix}_criticality, "
        f"({alias}.archived_at IS NOT NULL) AS {prefix}_archived"
    )


_INTEGRATION_FROM = f"""
      FROM {_S}.integrations i
      LEFT JOIN {_S}.services src ON src.id = i.source_service_id
      LEFT JOIN {_S}.services tgt ON tgt.id = i.target_service_id
"""
_INTEGRATION_SELECT = (
    f"SELECT i.*, {_service_columns('src', 'source')}, {_service_columns('tgt', 'target')}"
    + _INTEGRATION_FROM
)

_DEPENDENCY_SELECT = f"""
    SELECT d.*, {_service_columns('dep', 'dependent')}, {_service_columns('req', 'required')}
      FROM {_S}.service_dependencies d
      JOIN {_S}.services dep ON dep.id = d.dependent_service_id
      JOIN {_S}.services req ON req.id = d.required_service_id
"""

_CONFLICTS = {
    "networks_active_name_uq": ConflictError(
        "network_name_conflict",
        "Já existe uma rede ativa com este nome nesta unidade.",
        {"fields": {"name": "Nome já cadastrado nesta unidade."}},
    ),
    "networks_active_corporate_cidr_uq": ConflictError(
        "network_cidr_conflict",
        "Já existe uma rede corporativa ativa com este CIDR nesta unidade.",
        {"fields": {"cidr": "CIDR já cadastrado nesta unidade."}},
    ),
    "server_network_links_pair_uq": ConflictError(
        "server_network_link_exists", "Este servidor já está vinculado a esta rede."
    ),
    "integrations_active_endpoints_uq": ConflictError(
        "integration_exists",
        "Já existe uma integração ativa entre estas pontas com este protocolo.",
        {"fields": {"protocol": "Integração já cadastrada para estas pontas."}},
    ),
    "service_dependencies_pair_uq": ConflictError(
        "service_dependency_exists", "Esta dependência já está registrada."
    ),
}


def _conflict(exc: pg_errors.UniqueViolation) -> ConflictError:
    constraint = getattr(exc.diag, "constraint_name", None)
    known = _CONFLICTS.get(constraint or "")
    if known is not None:
        return ConflictError(known.code, known.message, known.details)
    return ConflictError("inventory_conflict", "Registro duplicado.")


def _service_summary(row: dict, prefix: str, id_column: str) -> dict | None:
    if row[id_column] is None:
        return None
    return {
        "id": str(row[id_column]),
        "code": format_service_code(row[f"{prefix}_seq"]),
        "name": row[f"{prefix}_name"],
        "service_kind": row[f"{prefix}_kind"],
        "environment": row[f"{prefix}_environment"],
        "criticality": row[f"{prefix}_criticality"],
        "archived": bool(row[f"{prefix}_archived"]),
    }


def _optional_id(value) -> str | None:
    return str(value) if value is not None else None


def _network_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_network_code(row["seq"]),
        "name": row["name"],
        "cidr": row["cidr"],
        "vlan_id": row["vlan_id"],
        "gateway": row["gateway"],
        "unit_code": row["unit_code"],
        "location": row["location"],
        "purpose": row["purpose"],
        "environment": row["environment"],
        "zone": row["zone"],
        "network_scope": row["network_scope"],
        "criticality": row["criticality"],
        "responsible": row["responsible"],
        "notes": row["notes"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "server_count": int(row.get("server_count") or 0),
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _link_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "server_id": str(row["server_id"]),
        "network_id": str(row["network_id"]),
        "ip_address": row["ip_address"],
        "interface_name": row["interface_name"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "server": {
            "id": str(row["server_id"]),
            "code": format_server_code(row["server_seq"]),
            "name": row["server_name"],
            "hostname": row["server_hostname"],
            "environment": row["server_environment"],
            "unit_code": row["server_unit_code"],
            "archived": bool(row["server_archived"]),
        },
        "network": {
            "id": str(row["network_id"]),
            "code": format_network_code(row["network_seq"]),
            "name": row["network_name"],
            "cidr": row["network_cidr"],
            "vlan_id": row["network_vlan_id"],
            "network_scope": row["network_scope"],
            "environment": row["network_environment"],
            "unit_code": row["network_unit_code"],
            "archived": bool(row["network_archived"]),
        },
    }


def _integration_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "code": format_integration_code(row["seq"]),
        "name": row["name"],
        "source_service_id": _optional_id(row["source_service_id"]),
        "source_external_name": row["source_external_name"],
        "source_service": _service_summary(row, "source", "source_service_id"),
        "target_service_id": _optional_id(row["target_service_id"]),
        "target_external_name": row["target_external_name"],
        "target_service": _service_summary(row, "target", "target_service_id"),
        "protocol": row["protocol"],
        "direction": row["direction"],
        "purpose": row["purpose"],
        "criticality": row["criticality"],
        "responsible": row["responsible"],
        "administrative_status": row["administrative_status"],
        "notes": row["notes"],
        "revision": row["revision"],
        "archived": row["archived_at"] is not None,
        "archived_at": row["archived_at"],
        "archived_by_name": row["archived_by_name"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "updated_at": row["updated_at"],
        "updated_by_name": row["updated_by_name"],
    }


def _dependency_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "dependent_service_id": str(row["dependent_service_id"]),
        "required_service_id": str(row["required_service_id"]),
        "notes": row["notes"],
        "created_at": row["created_at"],
        "created_by_name": row["created_by_name"],
        "dependent_service": _service_summary(row, "dependent", "dependent_service_id"),
        "required_service": _service_summary(row, "required", "required_service_id"),
    }


def _archived_where(alias: str, archived: str) -> str | None:
    if archived == "active":
        return f"{alias}.archived_at IS NULL"
    if archived == "archived":
        return f"{alias}.archived_at IS NOT NULL"
    return None


class PostgresConnectivityRepository(PostgresRepositoryBase):
    # ------------------------------------------------------------- networks

    def _fetch_network(self, conn: psycopg.Connection, network_id: str) -> dict | None:
        row = conn.execute(_NETWORK_SELECT + " WHERE n.id = %s", (network_id,)).fetchone()
        return _network_row(row) if row else None

    def _require_active_network(self, conn: psycopg.Connection, network_id: str) -> dict:
        return self._require_active(
            conn,
            "networks",
            network_id,
            field="network_id",
            missing_message="Rede não encontrada.",
            archived_error=ConflictError(
                "network_archived", "Rede arquivada: restaure o cadastro antes de alterá-la."
            ),
        )

    def list_networks(self, query: NetworkQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {}
        archived = _archived_where("n", query.archived)
        if archived:
            where.append(archived)
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(n.name ILIKE %(q)s OR n.cidr ILIKE %(q)s OR n.zone ILIKE %(q)s "
                "OR n.location ILIKE %(q)s)"
            )
        for column in ("unit_code", "environment", "network_scope", "criticality"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"n.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order_sql = f"{_NETWORK_SORT_SQL[query.sort]} {direction}, n.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                f"SELECT count(*) AS total FROM {_S}.networks n WHERE {where_sql}", params
            ).fetchone()["total"]
            rows = conn.execute(
                _NETWORK_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql} LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_network_row(row) for row in rows], int(total)

    def get_network(self, network_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_network(conn, network_id)

    def insert_network(
        self, network_id: str, fields: NetworkFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                conn.execute(
                    f"""
                    INSERT INTO {_S}.networks
                        (id, name, cidr, vlan_id, gateway, unit_code, location, purpose,
                         environment, zone, network_scope, criticality, responsible, notes,
                         created_by_id, created_by_name, updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(cidr)s, %(vlan_id)s, %(gateway)s, %(unit_code)s,
                         %(location)s, %(purpose)s, %(environment)s, %(zone)s,
                         %(network_scope)s, %(criticality)s, %(responsible)s, %(notes)s,
                         %(actor_id)s, %(actor_name)s, %(actor_id)s, %(actor_name)s)
                    """,
                    {
                        **fields.as_dict(),
                        "id": network_id,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                self._audit(conn, audit, actor)
                created = self._fetch_network(conn, network_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        assert created is not None
        return created

    def update_network(
        self,
        network_id: str,
        fields: NetworkFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        try:
            with self._tx() as conn:
                current = conn.execute(
                    f"SELECT cidr FROM {_S}.networks WHERE id = %s FOR UPDATE", (network_id,)
                ).fetchone()
                if current is None:
                    return None
                if current["cidr"] != fields.cidr:
                    outside = conn.execute(
                        f"""
                        SELECT 1 FROM {_S}.server_network_links
                         WHERE network_id = %s AND ip_address IS NOT NULL
                           AND NOT (ip_address::inet <<= %s::cidr)
                         LIMIT 1
                        """,
                        (network_id, fields.cidr),
                    ).fetchone()
                    if outside is not None:
                        raise network_links_outside_cidr_error()
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.networks SET
                        name = %(name)s, cidr = %(cidr)s, vlan_id = %(vlan_id)s,
                        gateway = %(gateway)s, unit_code = %(unit_code)s,
                        location = %(location)s, purpose = %(purpose)s,
                        environment = %(environment)s, zone = %(zone)s,
                        network_scope = %(network_scope)s, criticality = %(criticality)s,
                        responsible = %(responsible)s, notes = %(notes)s,
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND archived_at IS NULL
                    """,
                    {
                        **fields.as_dict(),
                        "id": network_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_network(conn, network_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    def set_network_archived(
        self,
        network_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        return self._set_archived(
            "networks", network_id, archived, expected_revision, actor, audit, self._fetch_network
        )

    # ---------------------------------------------------------- connectivity

    def list_network_links(
        self, *, network_id: str | None = None, server_id: str | None = None
    ) -> list[dict]:
        where, params = [], {"limit": LINK_LIST_LIMIT}
        if network_id:
            where.append("l.network_id = %(network_id)s")
            params["network_id"] = network_id
        if server_id:
            where.append("l.server_id = %(server_id)s")
            params["server_id"] = server_id
        where_sql = " AND ".join(where) or "TRUE"
        with self._tx() as conn:
            rows = conn.execute(
                _LINK_SELECT
                + f" WHERE {where_sql} ORDER BY lower(n.name), lower(s.name), l.id"
                + " LIMIT %(limit)s",
                params,
            ).fetchall()
        return [_link_row(row) for row in rows]

    def get_network_link(self, link_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(_LINK_SELECT + " WHERE l.id = %s", (link_id,)).fetchone()
        return _link_row(row) if row else None

    def insert_network_link(
        self, link_id: str, fields: ServerNetworkLinkFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                self._require_active_server(conn, fields.server_id)
                network = self._require_active_network(conn, fields.network_id)
                validate_link_address(fields.ip_address, network["cidr"])
                conn.execute(
                    f"""
                    INSERT INTO {_S}.server_network_links
                        (id, server_id, network_id, ip_address, interface_name, notes,
                         created_by_id, created_by_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        link_id,
                        fields.server_id,
                        fields.network_id,
                        fields.ip_address,
                        fields.interface_name,
                        fields.notes,
                        actor.id,
                        actor.name,
                    ),
                )
                self._audit(conn, audit, actor)
                row = conn.execute(_LINK_SELECT + " WHERE l.id = %s", (link_id,)).fetchone()
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        return _link_row(row)

    def delete_network_link(self, link_id: str, actor: Actor, audit: AuditEvent) -> bool:
        return self._delete_link("server_network_links", link_id, actor, audit)

    # --------------------------------------------------------- integrations

    def _fetch_integration(self, conn: psycopg.Connection, integration_id: str) -> dict | None:
        row = conn.execute(
            _INTEGRATION_SELECT + " WHERE i.id = %s", (integration_id,)
        ).fetchone()
        return _integration_row(row) if row else None

    def list_integrations(self, query: IntegrationQuery) -> tuple[list[dict], int]:
        where = ["TRUE"]
        params: dict = {}
        archived = _archived_where("i", query.archived)
        if archived:
            where.append(archived)
        if query.q:
            params["q"] = f"%{escape_like(query.q)}%"
            where.append(
                "(i.name ILIKE %(q)s OR i.source_external_name ILIKE %(q)s "
                "OR i.target_external_name ILIKE %(q)s OR src.name ILIKE %(q)s "
                "OR tgt.name ILIKE %(q)s)"
            )
        if query.service_id:
            params["service_id"] = query.service_id
            where.append(
                "(i.source_service_id = %(service_id)s OR i.target_service_id = %(service_id)s)"
            )
        for column in ("protocol", "criticality", "administrative_status"):
            value = getattr(query, column)
            if value:
                params[column] = value
                where.append(f"i.{column} = %({column})s")
        where_sql = " AND ".join(where)
        direction = "DESC" if query.direction == "desc" else "ASC"
        order_sql = f"{_INTEGRATION_SORT_SQL[query.sort]} {direction}, i.seq {direction}"
        params["limit"] = query.page_size
        params["offset"] = (query.page - 1) * query.page_size
        with self._tx() as conn:
            total = conn.execute(
                "SELECT count(*) AS total" + _INTEGRATION_FROM + f" WHERE {where_sql}", params
            ).fetchone()["total"]
            rows = conn.execute(
                _INTEGRATION_SELECT
                + f" WHERE {where_sql} ORDER BY {order_sql} LIMIT %(limit)s OFFSET %(offset)s",
                params,
            ).fetchall()
        return [_integration_row(row) for row in rows], int(total)

    def get_integration(self, integration_id: str) -> dict | None:
        with self._tx() as conn:
            return self._fetch_integration(conn, integration_id)

    def list_server_integrations(self, server_id: str) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                _INTEGRATION_SELECT
                + f"""
                 WHERE i.source_service_id IN (
                           SELECT h.service_id FROM {_S}.service_hostings h
                            WHERE h.server_id = %(server_id)s)
                    OR i.target_service_id IN (
                           SELECT h.service_id FROM {_S}.service_hostings h
                            WHERE h.server_id = %(server_id)s)
                 ORDER BY lower(i.name), i.seq
                 LIMIT %(limit)s
                """,
                {"server_id": server_id, "limit": LINK_LIST_LIMIT},
            ).fetchall()
        return [_integration_row(row) for row in rows]

    def _lock_endpoints(
        self, conn: psycopg.Connection, fields: IntegrationFields, only: set[str] | None = None
    ) -> None:
        for side in ("source", "target"):
            service_id = getattr(fields, f"{side}_service_id")
            if service_id and (only is None or service_id in only):
                self._require_active_service(conn, service_id, field=f"{side}_service_id")

    def insert_integration(
        self, integration_id: str, fields: IntegrationFields, actor: Actor, audit: AuditEvent
    ) -> dict:
        try:
            with self._tx() as conn:
                self._lock_endpoints(conn, fields)
                conn.execute(
                    f"""
                    INSERT INTO {_S}.integrations
                        (id, name, source_service_id, source_external_name,
                         target_service_id, target_external_name, protocol, direction,
                         purpose, criticality, responsible, administrative_status, notes,
                         created_by_id, created_by_name, updated_by_id, updated_by_name)
                    VALUES
                        (%(id)s, %(name)s, %(source_service_id)s, %(source_external_name)s,
                         %(target_service_id)s, %(target_external_name)s, %(protocol)s,
                         %(direction)s, %(purpose)s, %(criticality)s, %(responsible)s,
                         %(administrative_status)s, %(notes)s,
                         %(actor_id)s, %(actor_name)s, %(actor_id)s, %(actor_name)s)
                    """,
                    {
                        **fields.as_dict(),
                        "id": integration_id,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                self._audit(conn, audit, actor)
                created = self._fetch_integration(conn, integration_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        assert created is not None
        return created

    def update_integration(
        self,
        integration_id: str,
        fields: IntegrationFields,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        try:
            with self._tx() as conn:
                current = conn.execute(
                    f"SELECT source_service_id, target_service_id FROM {_S}.integrations "
                    "WHERE id = %s FOR UPDATE",
                    (integration_id,),
                ).fetchone()
                if current is None:
                    return None
                previous = {
                    str(value)
                    for value in (current["source_service_id"], current["target_service_id"])
                    if value is not None
                }
                added = set(fields.internal_service_ids()) - previous
                self._lock_endpoints(conn, fields, added)
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.integrations SET
                        name = %(name)s,
                        source_service_id = %(source_service_id)s,
                        source_external_name = %(source_external_name)s,
                        target_service_id = %(target_service_id)s,
                        target_external_name = %(target_external_name)s,
                        protocol = %(protocol)s, direction = %(direction)s,
                        purpose = %(purpose)s, criticality = %(criticality)s,
                        responsible = %(responsible)s,
                        administrative_status = %(administrative_status)s, notes = %(notes)s,
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND archived_at IS NULL
                    """,
                    {
                        **fields.as_dict(),
                        "id": integration_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return self._fetch_integration(conn, integration_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    def set_integration_archived(
        self,
        integration_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict | None:
        return self._set_archived(
            "integrations",
            integration_id,
            archived,
            expected_revision,
            actor,
            audit,
            self._fetch_integration,
        )

    # --------------------------------------------------------- dependencies

    def list_dependencies(self, service_id: str) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                _DEPENDENCY_SELECT
                + " WHERE d.dependent_service_id = %(id)s OR d.required_service_id = %(id)s"
                + " ORDER BY lower(dep.name), lower(req.name), d.id LIMIT %(limit)s",
                {"id": service_id, "limit": LINK_LIST_LIMIT},
            ).fetchall()
        return [_dependency_row(row) for row in rows]

    def get_dependency(self, dependency_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(
                _DEPENDENCY_SELECT + " WHERE d.id = %s", (dependency_id,)
            ).fetchone()
        return _dependency_row(row) if row else None

    def insert_dependency(
        self,
        dependency_id: str,
        fields: ServiceDependencyFields,
        actor: Actor,
        audit: AuditEvent,
    ) -> dict:
        try:
            with self._tx() as conn:
                self._require_active_service(
                    conn, fields.dependent_service_id, field="dependent_service_id"
                )
                self._require_active_service(
                    conn, fields.required_service_id, field="required_service_id"
                )
                conn.execute(
                    f"""
                    INSERT INTO {_S}.service_dependencies
                        (id, dependent_service_id, required_service_id, notes,
                         created_by_id, created_by_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        dependency_id,
                        fields.dependent_service_id,
                        fields.required_service_id,
                        fields.notes,
                        actor.id,
                        actor.name,
                    ),
                )
                self._audit(conn, audit, actor)
                row = conn.execute(
                    _DEPENDENCY_SELECT + " WHERE d.id = %s", (dependency_id,)
                ).fetchone()
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc
        return _dependency_row(row)

    def delete_dependency(self, dependency_id: str, actor: Actor, audit: AuditEvent) -> bool:
        return self._delete_link("service_dependencies", dependency_id, actor, audit)

    # -------------------------------------------------------------- helpers

    def _set_archived(
        self,
        table: str,
        row_id: str,
        archived: bool,
        expected_revision: int,
        actor: Actor,
        audit: AuditEvent,
        fetch,
    ) -> dict | None:
        assignment, guard = archive_assignment(archived)
        try:
            with self._tx() as conn:
                cur = conn.execute(
                    f"""
                    UPDATE {_S}.{table} SET {assignment},
                        revision = revision + 1, updated_at = now(),
                        updated_by_id = %(actor_id)s, updated_by_name = %(actor_name)s
                     WHERE id = %(id)s AND revision = %(revision)s AND {guard}
                    """,
                    {
                        "id": row_id,
                        "revision": expected_revision,
                        "actor_id": actor.id,
                        "actor_name": actor.name,
                    },
                )
                if cur.rowcount != 1:
                    return None
                self._audit(conn, audit, actor)
                return fetch(conn, row_id)
        except pg_errors.UniqueViolation as exc:
            raise _conflict(exc) from exc

    def _delete_link(self, table: str, link_id: str, actor: Actor, audit: AuditEvent) -> bool:
        with self._tx() as conn:
            cur = conn.execute(f"DELETE FROM {_S}.{table} WHERE id = %s", (link_id,))
            if cur.rowcount != 1:
                return False
            self._audit(conn, audit, actor)
        return True
