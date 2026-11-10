"""Base dos repositórios PostgreSQL do Portal de TI (schema `it_portal`).

Transação por operação, mapeamento de falhas para erros de domínio e gravação
do evento de auditoria na mesma transação da escrita.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import errors as pg_errors

from it_portal_app.application.inventory_rules import reference_not_found
from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.domain.catalogs import CRITICALITIES
from it_portal_app.domain.errors import ConflictError, PersistenceUnavailableError
from it_portal_app.infrastructure.persistence.db import db_configured, db_connect

logger = logging.getLogger(__name__)

SCHEMA = "it_portal"


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def rank_sql(column: str) -> str:
    return (
        f"CASE {column} "
        + " ".join(f"WHEN '{value}' THEN {index}" for index, value in enumerate(CRITICALITIES))
        + " END"
    )


def archive_assignment(archived: bool) -> tuple[str, str]:
    """SET e guarda WHERE para arquivar/restaurar um cadastro versionado."""
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


def history_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "entity_type": row["entity_type"],
        "entity_id": str(row["entity_id"]),
        "event_type": row["event_type"],
        "changes": row["changes"],
        "actor_name": row["actor_name"],
        "occurred_at": row["occurred_at"],
    }


class PostgresRepositoryBase:
    @contextmanager
    def _tx(self) -> Iterator[psycopg.Connection]:
        if not db_configured():
            raise PersistenceUnavailableError(
                "persistence_unavailable", "Armazenamento do Portal de TI não configurado."
            )
        try:
            conn = db_connect()
        except psycopg.OperationalError as exc:
            logger.error("it_portal_db_connect_failed error=%s", type(exc).__name__)
            raise PersistenceUnavailableError(
                "persistence_unavailable",
                "Armazenamento do Portal de TI indisponível no momento.",
            ) from exc
        try:
            with conn.transaction():
                yield conn
        except pg_errors.QueryCanceled as exc:
            logger.error("it_portal_db_statement_timeout")
            raise PersistenceUnavailableError(
                "persistence_timeout", "A consulta demorou demais. Tente novamente."
            ) from exc
        finally:
            conn.close()

    @staticmethod
    def _require_active(
        conn: psycopg.Connection,
        table: str,
        row_id: str,
        *,
        field: str,
        missing_message: str,
        archived_error: ConflictError,
    ) -> dict:
        """Referência existente e ativa, travada (`FOR SHARE`) até o fim da transação."""
        row = conn.execute(
            f"SELECT * FROM {SCHEMA}.{table} WHERE id = %s FOR SHARE", (row_id,)
        ).fetchone()
        if row is None:
            raise reference_not_found(field, missing_message)
        if row["archived_at"] is not None:
            raise ConflictError(archived_error.code, archived_error.message)
        return row

    def _require_active_server(
        self, conn: psycopg.Connection, server_id: str, *, field: str = "server_id"
    ) -> dict:
        return self._require_active(
            conn,
            "servers",
            server_id,
            field=field,
            missing_message="Servidor não encontrado.",
            archived_error=ConflictError(
                "server_archived", "Servidor arquivado: restaure o cadastro antes de vinculá-lo."
            ),
        )

    def _require_active_service(
        self, conn: psycopg.Connection, service_id: str, *, field: str = "service_id"
    ) -> dict:
        return self._require_active(
            conn,
            "services",
            service_id,
            field=field,
            missing_message="Serviço não encontrado.",
            archived_error=ConflictError(
                "service_archived", "Serviço arquivado: restaure o cadastro antes de alterá-lo."
            ),
        )

    @staticmethod
    def _audit(conn: psycopg.Connection, audit: AuditEvent, actor: Actor) -> None:
        conn.execute(
            f"""
            INSERT INTO {SCHEMA}.audit_events
                (id, entity_type, entity_id, server_id, event_type, changes,
                 actor_id, actor_name, subject_ids)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::uuid[])
            """,
            (
                str(uuid.uuid4()),
                audit.entity_type,
                audit.entity_id,
                audit.server_id,
                audit.event_type,
                json.dumps(audit.changes, default=str, ensure_ascii=False),
                actor.id,
                actor.name,
                list(audit.subject_ids),
            ),
        )
