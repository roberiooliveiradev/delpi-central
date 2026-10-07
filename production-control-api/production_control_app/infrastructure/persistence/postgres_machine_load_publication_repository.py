"""Repositório Postgres — publicação da carga máquina (fila PUBLISHED por filial).

O cockpit consulta a fila a cada ~15 s por tablet. O payload tem ~1,8 MB, então
a leitura usa o mesmo probe de `xmin` do snapshot WORKING: versão igual
reaproveita a linha materializada em memória, versão nova busca o JSONB.
O namespace do cache é separado — WORKING e PUBLISHED da mesma filial nunca
compartilham chave.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from production_control_app.domain.ports.machine_load_publication_repository import (
    MachineLoadPublicationRepositoryPort,
)
from production_control_app.infrastructure.persistence.machine_load_snapshot_row_cache import (
    PUBLISHED_NAMESPACE,
    clear_snapshot_row_cache,
    get_snapshot_row_cache,
    put_snapshot_row_cache,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.machine_load_publications"

_COLUMNS = """
    id::text AS id,
    branch,
    generation_id::text AS generation_id,
    start_date,
    end_date,
    payload_json,
    schema_version,
    source,
    source_refreshed_at,
    source_refreshed_by,
    published_at,
    published_by,
    xmin::text AS row_version
"""


class PostgresMachineLoadPublicationRepository(MachineLoadPublicationRepositoryPort):
    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        """Lê a fila publicada evitando rebuscar ~1,8 MB que não mudaram.

        Com conn a leitura roda dentro da transação chamadora (publicação):
        sem probe/cache, a linha vem autoritativa do banco.
        """
        if conn is not None:
            query = f"""
                SELECT {_COLUMNS}
                FROM {_TABLE}
                WHERE branch = %s
                LIMIT 1
            """
            with conn.cursor() as cursor:
                cursor.execute(query, (branch,))
                row = cursor.fetchone()
            if row is None:
                clear_snapshot_row_cache(branch, namespace=PUBLISHED_NAMESPACE)
                return None
            return self._remember(branch=branch, row=dict(row))

        row_version = self._read_row_version(branch=branch)
        if row_version is None:
            clear_snapshot_row_cache(branch, namespace=PUBLISHED_NAMESPACE)
            return None

        cached = get_snapshot_row_cache(
            branch, row_version=row_version, namespace=PUBLISHED_NAMESPACE
        )
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
            clear_snapshot_row_cache(branch, namespace=PUBLISHED_NAMESPACE)
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
        put_snapshot_row_cache(
            branch,
            row_version=row.get("row_version"),
            row=row,
            namespace=PUBLISHED_NAMESPACE,
        )
        return dict(row)

    def upsert(
        self,
        *,
        branch: str,
        generation_id: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        source_refreshed_at: datetime,
        source_refreshed_by: str | None,
        published_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
        conn: Any = None,
    ) -> dict[str, Any]:
        # ``conn`` permite que a publicação entre na mesma transação do WORKING
        # (snapshot repo expõe transaction()) quando a fila live exigir dual-write.
        query = f"""
            INSERT INTO {_TABLE} (
                branch,
                generation_id,
                start_date,
                end_date,
                payload_json,
                schema_version,
                source,
                source_refreshed_at,
                source_refreshed_by,
                published_at,
                published_by
            ) VALUES (
                %s, %s::uuid, %s, %s, %s::jsonb, %s, %s, %s, %s, NOW(), %s
            )
            ON CONFLICT (branch) DO UPDATE SET
                generation_id = EXCLUDED.generation_id,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                payload_json = EXCLUDED.payload_json,
                schema_version = EXCLUDED.schema_version,
                source = EXCLUDED.source,
                source_refreshed_at = EXCLUDED.source_refreshed_at,
                source_refreshed_by = EXCLUDED.source_refreshed_by,
                published_at = NOW(),
                published_by = EXCLUDED.published_by
            RETURNING {_COLUMNS}
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        params = (
            branch,
            generation_id,
            start_date,
            end_date,
            payload_text,
            schema_version,
            source,
            source_refreshed_at,
            source_refreshed_by,
            published_by,
        )
        if conn is not None:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
        else:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                connection.commit()
        if row is None:
            raise RuntimeError("Falha ao gravar publicação da carga máquina.")
        return self._remember(branch=branch, row=dict(row))

    def update_payload(
        self, *, branch: str, payload: dict[str, Any], conn: Any = None
    ) -> dict[str, Any]:
        """Dual-write do estado LIVE: só o conteúdo; a publicação é a mesma."""
        query = f"""
            UPDATE {_TABLE}
            SET payload_json = %s::jsonb
            WHERE branch = %s
            RETURNING {_COLUMNS}
        """
        payload_text = json.dumps(payload, ensure_ascii=False, default=str)
        if conn is not None:
            with conn.cursor() as cursor:
                cursor.execute(query, (payload_text, branch))
                row = cursor.fetchone()
        else:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (payload_text, branch))
                    row = cursor.fetchone()
                connection.commit()
        if row is None:
            raise RuntimeError(
                "Publicação da carga máquina não encontrada para atualizar."
            )
        return self._remember(branch=branch, row=dict(row))
