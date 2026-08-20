"""Repositório Postgres — snapshots da carga máquina."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.machine_load_snapshots"


class PostgresMachineLoadSnapshotRepository(MachineLoadSnapshotRepositoryPort):
    def get(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any] | None:
        query = f"""
            SELECT
                id::text AS id,
                branch,
                start_date,
                end_date,
                payload_json,
                schema_version,
                source,
                refreshed_at,
                refreshed_by
            FROM {_TABLE}
            WHERE branch = %s
              AND start_date = %s
              AND end_date = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch, start_date, end_date))
                row = cursor.fetchone()
        return dict(row) if row is not None else None

    def upsert(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        query = f"""
            INSERT INTO {_TABLE} (
                branch,
                start_date,
                end_date,
                payload_json,
                schema_version,
                source,
                refreshed_at,
                refreshed_by
            ) VALUES (
                %s, %s, %s, %s::jsonb, %s, %s, NOW(), %s
            )
            ON CONFLICT (branch, start_date, end_date) DO UPDATE SET
                payload_json = EXCLUDED.payload_json,
                schema_version = EXCLUDED.schema_version,
                source = EXCLUDED.source,
                refreshed_at = NOW(),
                refreshed_by = EXCLUDED.refreshed_by
            RETURNING
                id::text AS id,
                branch,
                start_date,
                end_date,
                payload_json,
                schema_version,
                source,
                refreshed_at,
                refreshed_by
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        branch,
                        start_date,
                        end_date,
                        payload_text,
                        schema_version,
                        source,
                        refreshed_by,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if row is None:
            raise RuntimeError("Falha ao gravar snapshot da carga máquina.")
        return dict(row)

    def update_payload(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        query = f"""
            UPDATE {_TABLE}
            SET payload_json = %s::jsonb
            WHERE branch = %s
              AND start_date = %s
              AND end_date = %s
            RETURNING
                id::text AS id,
                branch,
                start_date,
                end_date,
                payload_json,
                schema_version,
                source,
                refreshed_at,
                refreshed_by
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (payload_text, branch, start_date, end_date))
                row = cursor.fetchone()
            connection.commit()
        if row is None:
            raise RuntimeError("Snapshot da carga máquina não encontrado para atualizar.")
        return dict(row)
