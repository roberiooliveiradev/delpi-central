from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from tm_app.domain.services.filial_catalog_service import normalize_codigo_filial
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_uuid(value: str) -> bool:
    if not _UUID_PATTERN.match(value.strip()):
        return False
    try:
        UUID(value.strip())
    except ValueError:
        return False
    return True


class FilialRepository(PluginBaseRepository):
    _LIST_QUERY = """
        SELECT
            filial_id,
            codigo_filial,
            nome_filial,
            status_filial,
            created_at,
            updated_at
        FROM transformometro.filiais
        WHERE deletado = FALSE
    """

    def list(self, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        query = self._LIST_QUERY
        if not include_inactive:
            query += " AND status_filial = 'ativo'"
        query += " ORDER BY codigo_filial ASC"
        return self.fetch_all(query)

    def get(self, filial_ref: str) -> dict[str, Any] | None:
        ref = filial_ref.strip()
        if _is_uuid(ref):
            return self.fetch_one(
                f"{self._LIST_QUERY} AND filial_id = %s::uuid",
                (ref,),
            )
        codigo = normalize_codigo_filial(ref)
        return self.fetch_one(
            f"{self._LIST_QUERY} AND codigo_filial = %s",
            (codigo,),
        )

    def list_active_codigos(self) -> set[str]:
        rows = self.list(include_inactive=False)
        return {str(row["codigo_filial"]) for row in rows}

    def list_for_options(self) -> list[dict[str, Any]]:
        rows = self.list(include_inactive=False)
        return [
            {
                "id": row["codigo_filial"],
                "filial_id": row["filial_id"],
                "codigo_filial": row["codigo_filial"],
                "label": row["nome_filial"],
            }
            for row in rows
        ]

    def count_processos(self, codigo_filial: str) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(DISTINCT pi.processo_id)::int AS total
            FROM transformometro.processo_instancias pi
            JOIN transformometro.filiais f ON f.filial_id = pi.filial_id
            JOIN transformometro.processos p ON p.processo_id = pi.processo_id
            WHERE f.codigo_filial = %s
              AND pi.deletado = FALSE
              AND p.deletado = FALSE
              AND f.deletado = FALSE
            """,
            (codigo_filial,),
        )
        return int((row or {}).get("total") or 0)

    def count_setor_vinculos(self, codigo_filial: str) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*)::int AS total
            FROM transformometro.setor_filiais
            WHERE filial_id = %s
            """,
            (codigo_filial,),
        )
        return int((row or {}).get("total") or 0)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        codigo_filial = normalize_codigo_filial(data["codigo_filial"])
        if self.get(codigo_filial):
            raise ValueError(f"Filial com código '{codigo_filial}' já existe.")

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.filiais (codigo_filial, nome_filial, status_filial)
            VALUES (%s, %s, %s)
            RETURNING filial_id, codigo_filial, nome_filial, status_filial, created_at, updated_at
            """,
            (
                codigo_filial,
                data["nome_filial"].strip(),
                data.get("status_filial", "ativo"),
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar filial.")
        return row

    def update(self, filial_ref: str, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.get(filial_ref)
        if not existing:
            return None

        row = self.execute_returning_one(
            """
            UPDATE transformometro.filiais SET
                nome_filial = %s,
                status_filial = %s,
                updated_at = NOW()
            WHERE filial_id = %s AND deletado = FALSE
            RETURNING filial_id, codigo_filial, nome_filial, status_filial, created_at, updated_at
            """,
            (
                data["nome_filial"].strip(),
                data.get("status_filial", "ativo"),
                existing["filial_id"],
            ),
        )
        return row

    def soft_delete(self, filial_ref: str) -> bool:
        existing = self.get(filial_ref)
        if not existing:
            return False

        codigo = str(existing["codigo_filial"])
        if self.count_processos(codigo) > 0:
            raise ValueError(
                "Não é possível excluir filial vinculada a processos. "
                "Altere os processos ou desative a filial."
            )
        if self.count_setor_vinculos(codigo) > 0:
            raise ValueError(
                "Não é possível excluir filial vinculada a setores. "
                "Remova os vínculos ou desative a filial."
            )

        row = self.execute_returning_one(
            """
            UPDATE transformometro.filiais
            SET deletado = TRUE, updated_at = NOW()
            WHERE filial_id = %s AND deletado = FALSE
            RETURNING filial_id
            """,
            (existing["filial_id"],),
        )
        return row is not None

    def upsert_bootstrap(
        self,
        codigo_filial: str,
        nome_filial: str,
        *,
        status_filial: str = "ativo",
    ) -> dict[str, Any]:
        codigo = normalize_codigo_filial(codigo_filial)
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.filiais (codigo_filial, nome_filial, status_filial)
            VALUES (%s, %s, %s)
            ON CONFLICT (codigo_filial) DO UPDATE SET
                nome_filial = EXCLUDED.nome_filial,
                status_filial = EXCLUDED.status_filial,
                deletado = FALSE,
                updated_at = NOW()
            RETURNING filial_id, codigo_filial, nome_filial, status_filial, created_at, updated_at
            """,
            (codigo, nome_filial.strip(), status_filial),
        )
        if row is None:
            raise RuntimeError(f"Falha ao upsert filial {codigo}.")
        return row
