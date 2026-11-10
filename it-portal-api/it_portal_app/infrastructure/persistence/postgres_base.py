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

from it_portal_app.application.ports import Actor, AuditEvent
from it_portal_app.domain.errors import PersistenceUnavailableError
from it_portal_app.infrastructure.persistence.db import db_configured, db_connect

logger = logging.getLogger(__name__)

SCHEMA = "it_portal"


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
