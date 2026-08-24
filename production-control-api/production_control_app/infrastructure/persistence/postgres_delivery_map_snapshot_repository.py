"""Repositório Postgres — snapshot do mapa de entrega (uma fila viva por filial)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from production_control_app.domain.ports.delivery_map_snapshot_repository import (
    DeliveryMapSnapshotRepositoryPort,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.delivery_map_snapshots"

_COLUMNS = """
    id::text AS id,
    branch,
    horizon_end,
    payload_json,
    schema_version,
    source,
    refreshed_at,
    refreshed_by
"""


class PostgresDeliveryMapSnapshotRepository(DeliveryMapSnapshotRepositoryPort):
    def get(self, *, branch: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE branch = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch,))
                row = cursor.fetchone()
        return dict(row) if row is not None else None

    def upsert(
        self,
        *,
        branch: str,
        horizon_end: date,
        payload: dict[str, Any],
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        query = f"""
            INSERT INTO {_TABLE} (
                branch,
                horizon_end,
                payload_json,
                schema_version,
                source,
                refreshed_at,
                refreshed_by
            ) VALUES (
                %s, %s, %s::jsonb, %s, %s, NOW(), %s
            )
            ON CONFLICT (branch) DO UPDATE SET
                horizon_end = EXCLUDED.horizon_end,
                payload_json = EXCLUDED.payload_json,
                schema_version = EXCLUDED.schema_version,
                source = EXCLUDED.source,
                refreshed_at = NOW(),
                refreshed_by = EXCLUDED.refreshed_by
            RETURNING {_COLUMNS}
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        branch,
                        horizon_end,
                        payload_text,
                        schema_version,
                        source,
                        refreshed_by,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()
        if row is None:
            raise RuntimeError("Falha ao gravar snapshot do mapa de entrega.")
        return dict(row)

    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        query = f"""
            UPDATE {_TABLE}
            SET payload_json = %s::jsonb
            WHERE branch = %s
            RETURNING {_COLUMNS}
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (payload_text, branch))
                row = cursor.fetchone()
            connection.commit()
        if row is None:
            raise RuntimeError("Snapshot do mapa de entrega não encontrado para atualizar.")
        return dict(row)
