from __future__ import annotations

import re
from typing import Any

from tm_app.core.catalogs import FILIAIS
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_SETOR_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")


def normalize_setor_id(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9_]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug or not _SETOR_ID_PATTERN.match(slug):
        raise ValueError("setor_id inválido: use apenas letras minúsculas, números e _")
    return slug


class SetorRepository(PluginBaseRepository):
    _LIST_QUERY = """
        SELECT
            s.setor_id,
            s.nome_setor,
            s.status_setor,
            s.created_at,
            s.updated_at,
            COALESCE(
                array_agg(sf.filial_id ORDER BY sf.filial_id)
                FILTER (WHERE sf.filial_id IS NOT NULL),
                '{}'::varchar[]
            ) AS filiais
        FROM transformometro.setores s
        LEFT JOIN transformometro.setor_filiais sf ON sf.setor_id = s.setor_id
        WHERE s.deletado = FALSE
    """

    def _validate_filiais(self, filiais: list[str]) -> None:
        if not filiais:
            raise ValueError("Informe ao menos uma filial para o setor.")
        invalid = [f for f in filiais if f not in FILIAIS]
        if invalid:
            raise ValueError(f"filial_id inválido: {', '.join(invalid)}")

    def _sync_filiais(self, setor_id: str, filiais: list[str], *, auto_commit: bool) -> None:
        self.execute(
            "DELETE FROM transformometro.setor_filiais WHERE setor_id = %s",
            (setor_id,),
            auto_commit=False,
        )
        for filial_id in sorted(set(filiais)):
            self.execute(
                """
                INSERT INTO transformometro.setor_filiais (setor_id, filial_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (setor_id, filial_id),
                auto_commit=False,
            )
        if auto_commit:
            self._connection.commit()

    def list(self, filial_id: str | None = None) -> list[dict[str, Any]]:
        query = self._LIST_QUERY
        params: tuple[Any, ...] | None = None
        if filial_id:
            query += """
                AND EXISTS (
                    SELECT 1 FROM transformometro.setor_filiais sf2
                    WHERE sf2.setor_id = s.setor_id AND sf2.filial_id = %s
                )
            """
            params = (filial_id,)
        query += """
        GROUP BY s.setor_id, s.nome_setor, s.status_setor, s.created_at, s.updated_at
        ORDER BY s.nome_setor ASC
        """
        return self.fetch_all(query, params)

    def get(self, setor_id: str) -> dict[str, Any] | None:
        rows = self.fetch_all(
            f"{self._LIST_QUERY} AND s.setor_id = %s"
            """
            GROUP BY s.setor_id, s.nome_setor, s.status_setor, s.created_at, s.updated_at
            """,
            (setor_id,),
        )
        return rows[0] if rows else None

    def list_for_options(self) -> list[dict[str, Any]]:
        rows = self.list()
        return [
            {
                "id": row["setor_id"],
                "label": row["nome_setor"],
                "filiais": list(row.get("filiais") or []),
            }
            for row in rows
            if row.get("status_setor") == "ativo"
        ]

    def is_active_for_filial(self, setor_id: str, filial_id: str) -> bool:
        row = self.fetch_one(
            """
            SELECT 1 AS ok
            FROM transformometro.setores s
            JOIN transformometro.setor_filiais sf ON sf.setor_id = s.setor_id
            WHERE s.setor_id = %s
              AND sf.filial_id = %s
              AND s.status_setor = 'ativo'
              AND s.deletado = FALSE
            """,
            (setor_id, filial_id),
        )
        return bool(row)

    def count_processos(self, setor_id: str) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*)::int AS total
            FROM transformometro.processos
            WHERE setor_id = %s AND deletado = FALSE
            """,
            (setor_id,),
        )
        return int((row or {}).get("total") or 0)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        setor_id = normalize_setor_id(data.get("setor_id") or data["nome_setor"])
        if self.get(setor_id):
            raise ValueError(f"Setor '{setor_id}' já existe.")

        filiais = list(data["filiais"])
        self._validate_filiais(filiais)

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.setores (setor_id, nome_setor, status_setor)
            VALUES (%s, %s, %s)
            RETURNING setor_id, nome_setor, status_setor, created_at, updated_at
            """,
            (
                setor_id,
                data["nome_setor"].strip(),
                data.get("status_setor", "ativo"),
            ),
            auto_commit=False,
        )
        if row is None:
            self._connection.rollback()
            raise RuntimeError("Falha ao criar setor.")

        self._sync_filiais(setor_id, filiais, auto_commit=True)
        created = self.get(setor_id)
        if created is None:
            raise RuntimeError("Falha ao carregar setor criado.")
        return created

    def update(self, setor_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        if not self.get(setor_id):
            return None

        filiais = list(data["filiais"])
        self._validate_filiais(filiais)

        row = self.execute_returning_one(
            """
            UPDATE transformometro.setores SET
                nome_setor = %s,
                status_setor = %s,
                updated_at = NOW()
            WHERE setor_id = %s AND deletado = FALSE
            RETURNING setor_id
            """,
            (
                data["nome_setor"].strip(),
                data.get("status_setor", "ativo"),
                setor_id,
            ),
            auto_commit=False,
        )
        if row is None:
            self._connection.rollback()
            return None

        self._sync_filiais(setor_id, filiais, auto_commit=True)
        return self.get(setor_id)

    def soft_delete(self, setor_id: str) -> bool:
        if self.count_processos(setor_id) > 0:
            raise ValueError(
                "Não é possível excluir setor vinculado a processos. "
                "Altere os processos ou desative o setor."
            )
        row = self.execute_returning_one(
            """
            UPDATE transformometro.setores
            SET deletado = TRUE, updated_at = NOW()
            WHERE setor_id = %s AND deletado = FALSE
            RETURNING setor_id
            """,
            (setor_id,),
        )
        return row is not None
