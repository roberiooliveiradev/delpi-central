"""Persistência de observações automáticas de servidor (E4.S1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from psycopg import errors as pg_errors
from psycopg.types.json import Jsonb

from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.observations import ObservationIngest
from it_portal_app.infrastructure.persistence.postgres_base import (
    SCHEMA,
    PostgresRepositoryBase,
)

_S = SCHEMA


def _observation_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "server_id": str(row["server_id"]),
        "run_id": row["run_id"],
        "source": row["source"],
        "collector_client_id": row["collector_client_id"],
        "observed_at": row["observed_at"],
        "received_at": row["received_at"],
        "schema_version": row["schema_version"],
        "status": row["status"],
        "summary": row["summary"] if isinstance(row["summary"], dict) else json.loads(row["summary"]),
        "sections_status": (
            row["sections_status"]
            if isinstance(row["sections_status"], dict)
            else json.loads(row["sections_status"] or "{}")
        ),
        "divergences": (
            row["divergences"]
            if isinstance(row["divergences"], list)
            else json.loads(row["divergences"] or "[]")
        ),
        "created_at": row["created_at"],
    }


_SELECT = f"""
    SELECT id, server_id, run_id, source, collector_client_id, observed_at, received_at,
           schema_version, status, summary, sections_status, divergences, created_at
      FROM {_S}.server_observations
"""


class PostgresObservationRepository(PostgresRepositoryBase):
    def get_by_run_id(self, run_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(_SELECT + " WHERE run_id = %s", (run_id,)).fetchone()
        return _observation_row(row) if row else None

    def get_latest_for_server(self, server_id: str) -> dict | None:
        with self._tx() as conn:
            row = conn.execute(
                _SELECT
                + " WHERE server_id = %s ORDER BY observed_at DESC, created_at DESC LIMIT 1",
                (server_id,),
            ).fetchone()
        return _observation_row(row) if row else None

    def list_for_server(self, server_id: str, *, limit: int) -> list[dict]:
        with self._tx() as conn:
            rows = conn.execute(
                _SELECT
                + " WHERE server_id = %s ORDER BY observed_at DESC, created_at DESC LIMIT %s",
                (server_id, limit),
            ).fetchall()
        return [_observation_row(row) for row in rows]

    def insert_observation(
        self,
        observation_id: str,
        server_id: str,
        ingest: ObservationIngest,
        *,
        collector_client_id: str,
        divergences: list[dict],
        retention: int,
    ) -> dict:
        received_at = datetime.now(timezone.utc)
        try:
            with self._tx() as conn:
                # Garante que o servidor ainda está ativo no momento da gravação.
                active = conn.execute(
                    f"""
                    SELECT 1 FROM {_S}.servers
                     WHERE id = %s AND archived_at IS NULL
                     FOR SHARE
                    """,
                    (server_id,),
                ).fetchone()
                if active is None:
                    raise ConflictError(
                        "server_archived",
                        "Servidor arquivado: restaure o cadastro antes de receber observações.",
                    )
                conn.execute(
                    f"""
                    INSERT INTO {_S}.server_observations
                        (id, server_id, run_id, source, collector_client_id, observed_at,
                         received_at, schema_version, status, summary, sections_status,
                         divergences)
                    VALUES
                        (%(id)s, %(server_id)s, %(run_id)s, %(source)s, %(collector_client_id)s,
                         %(observed_at)s, %(received_at)s, %(schema_version)s, %(status)s,
                         %(summary)s, %(sections_status)s, %(divergences)s)
                    """,
                    {
                        "id": observation_id,
                        "server_id": server_id,
                        "run_id": ingest.run_id,
                        "source": ingest.source,
                        "collector_client_id": collector_client_id,
                        "observed_at": ingest.observed_at,
                        "received_at": received_at,
                        "schema_version": ingest.schema_version,
                        "status": ingest.status,
                        "summary": Jsonb(ingest.summary),
                        "sections_status": Jsonb(ingest.sections_status),
                        "divergences": Jsonb(divergences),
                    },
                )
                # Retenção: remove observações além das N mais recentes do servidor.
                conn.execute(
                    f"""
                    DELETE FROM {_S}.server_observations
                     WHERE server_id = %(server_id)s
                       AND id NOT IN (
                           SELECT id FROM {_S}.server_observations
                            WHERE server_id = %(server_id)s
                            ORDER BY observed_at DESC, created_at DESC
                            LIMIT %(retention)s
                       )
                    """,
                    {"server_id": server_id, "retention": retention},
                )
                row = conn.execute(
                    _SELECT + " WHERE id = %s", (observation_id,)
                ).fetchone()
        except pg_errors.UniqueViolation as exc:
            # Corrida de replay: devolve a linha existente com o mesmo run_id.
            existing = self.get_by_run_id(ingest.run_id)
            if existing is not None:
                return existing
            raise ConflictError(
                "observation_run_id_conflict",
                "Este run_id já foi registrado.",
            ) from exc
        assert row is not None
        return _observation_row(row)
