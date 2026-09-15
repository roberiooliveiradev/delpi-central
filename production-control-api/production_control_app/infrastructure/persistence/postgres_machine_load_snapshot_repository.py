"""Repositório Postgres — snapshot da carga máquina (uma fila viva por filial)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.infrastructure.persistence.machine_load_snapshot_row_cache import (
    clear_snapshot_row_cache,
    get_snapshot_row_cache,
    put_snapshot_row_cache,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.machine_load_snapshots"

# `xmin` é a versão da tupla: muda em todo UPDATE, inclusive nos que não tocam
# `refreshed_at`. É a chave de cache correta para a fila congelada.
_COLUMNS = """
    id::text AS id,
    branch,
    start_date,
    end_date,
    payload_json,
    schema_version,
    source,
    refreshed_at,
    refreshed_by,
    xmin::text AS row_version
"""


class PostgresMachineLoadSnapshotRepository(MachineLoadSnapshotRepositoryPort):
    def get(self, *, branch: str) -> dict[str, Any] | None:
        """Lê a fila congelada, evitando rebuscar 1,8 MB que não mudaram.

        A versão da tupla é uma consulta barata; a linha inteira só volta do
        banco quando o PCP realmente reescreveu o snapshot.
        """
        row_version = self._read_row_version(branch=branch)
        if row_version is None:
            clear_snapshot_row_cache(branch)
            return None

        cached = get_snapshot_row_cache(branch, row_version=row_version)
        if cached is not None:
            return dict(cached)

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
        if row is None:
            clear_snapshot_row_cache(branch)
            return None
        return self._remember(branch=branch, row=dict(row))

    @staticmethod
    def _read_row_version(*, branch: str) -> str | None:
        query = f"""
            SELECT xmin::text AS row_version
            FROM {_TABLE}
            WHERE branch = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch,))
                row = cursor.fetchone()
        if row is None:
            return None
        return str(row.get("row_version") or "") or None

    @staticmethod
    def _remember(*, branch: str, row: dict[str, Any]) -> dict[str, Any]:
        # A versão vem da própria linha lida/escrita: se um write entrou no meio,
        # o cache guarda a versão do dado que está em mãos, não a do probe.
        put_snapshot_row_cache(branch, row_version=row.get("row_version"), row=row)
        return dict(row)

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
            ON CONFLICT (branch) DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
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
        return self._remember(branch=branch, row=dict(row))

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
            raise RuntimeError("Snapshot da carga máquina não encontrado para atualizar.")
        return self._remember(branch=branch, row=dict(row))
