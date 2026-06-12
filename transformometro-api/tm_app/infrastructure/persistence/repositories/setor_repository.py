from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from tm_app.core.catalogs import FILIAIS
from tm_app.domain.services.filial_catalog_service import validate_codigos_filiais
from tm_app.domain.services.setor_catalog_service import normalize_codigo_setor
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def normalize_setor_id(value: str) -> str:
    """Alias legado — normaliza slug de negócio (codigo_setor)."""
    return normalize_codigo_setor(value)


def _is_uuid(value: str) -> bool:
    if not _UUID_PATTERN.match(value.strip()):
        return False
    try:
        UUID(value.strip())
    except ValueError:
        return False
    return True


class SetorRepository(PluginBaseRepository):
    _LIST_QUERY = """
        SELECT
            s.setor_id,
            s.codigo_setor,
            s.nome_setor,
            s.status_setor,
            s.created_at,
            s.updated_at,
            COALESCE(
                array_agg(f.codigo_filial ORDER BY f.codigo_filial)
                FILTER (WHERE f.codigo_filial IS NOT NULL),
                '{}'::varchar[]
            ) AS filiais
        FROM transformometro.setores s
        LEFT JOIN transformometro.setor_filiais sf ON sf.setor_id = s.setor_id
        LEFT JOIN transformometro.filiais f ON f.filial_id = sf.filial_id AND f.deletado = FALSE
        WHERE s.deletado = FALSE
    """

    def _active_filial_codigos(self) -> set[str]:
        try:
            active = FilialRepository(connection=self._connection).list_active_codigos()
        except PluginsRepositoryError:
            active = set()
        if active:
            return active
        return set(FILIAIS.keys())

    def _validate_filiais(self, filiais: list[str]) -> None:
        validate_codigos_filiais(filiais, self._active_filial_codigos())

    def _resolve_setor_uuid(self, setor_ref: str) -> str | None:
        ref = setor_ref.strip()
        if _is_uuid(ref):
            row = self.fetch_one(
                """
                SELECT setor_id::text AS setor_id
                FROM transformometro.setores
                WHERE setor_id = %s::uuid AND deletado = FALSE
                """,
                (ref,),
            )
            return str(row["setor_id"]) if row else None

        codigo = normalize_codigo_setor(ref)
        row = self.fetch_one(
            """
            SELECT setor_id::text AS setor_id
            FROM transformometro.setores
            WHERE codigo_setor = %s AND deletado = FALSE
            """,
            (codigo,),
        )
        return str(row["setor_id"]) if row else None

    def _resolve_filial_uuid(self, codigo_filial: str) -> str | None:
        row = FilialRepository(connection=self._connection).get(codigo_filial)
        if not row:
            return None
        return str(row["filial_id"])

    def _sync_filiais(self, setor_uuid: str, filiais: list[str], *, auto_commit: bool) -> None:
        self.execute(
            "DELETE FROM transformometro.setor_filiais WHERE setor_id = %s::uuid",
            (setor_uuid,),
            auto_commit=False,
        )
        for codigo_filial in sorted(set(filiais)):
            filial_uuid = self._resolve_filial_uuid(codigo_filial)
            if not filial_uuid:
                raise ValueError(f"filial_id inválido: {codigo_filial}")
            self.execute(
                """
                INSERT INTO transformometro.setor_filiais (setor_id, filial_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT DO NOTHING
                """,
                (setor_uuid, filial_uuid),
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
                    SELECT 1
                    FROM transformometro.setor_filiais sf2
                    JOIN transformometro.filiais f2 ON f2.filial_id = sf2.filial_id
                    WHERE sf2.setor_id = s.setor_id
                      AND f2.codigo_filial = %s
                      AND f2.deletado = FALSE
                )
            """
            params = (filial_id,)
        query += """
        GROUP BY s.setor_id, s.codigo_setor, s.nome_setor, s.status_setor, s.created_at, s.updated_at
        ORDER BY s.nome_setor ASC
        """
        return self.fetch_all(query, params)

    def get(self, setor_ref: str) -> dict[str, Any] | None:
        ref = setor_ref.strip()
        if _is_uuid(ref):
            predicate = "s.setor_id = %s::uuid"
            param: Any = ref
        else:
            predicate = "s.codigo_setor = %s"
            param = normalize_codigo_setor(ref)

        rows = self.fetch_all(
            f"{self._LIST_QUERY} AND {predicate}"
            """
            GROUP BY s.setor_id, s.codigo_setor, s.nome_setor, s.status_setor, s.created_at, s.updated_at
            """,
            (param,),
        )
        return rows[0] if rows else None

    def list_for_options(self) -> list[dict[str, Any]]:
        rows = self.list()
        return [
            {
                "id": row["codigo_setor"],
                "setor_id": row["setor_id"],
                "codigo_setor": row["codigo_setor"],
                "label": row["nome_setor"],
                "filiais": list(row.get("filiais") or []),
            }
            for row in rows
            if row.get("status_setor") == "ativo"
        ]

    def is_active_for_filial(self, setor_ref: str, filial_id: str) -> bool:
        if _is_uuid(setor_ref.strip()):
            setor_predicate = "s.setor_id = %s::uuid"
            setor_param: Any = setor_ref.strip()
        else:
            setor_predicate = "s.codigo_setor = %s"
            setor_param = normalize_codigo_setor(setor_ref)

        row = self.fetch_one(
            f"""
            SELECT 1 AS ok
            FROM transformometro.setores s
            JOIN transformometro.setor_filiais sf ON sf.setor_id = s.setor_id
            JOIN transformometro.filiais f ON f.filial_id = sf.filial_id
            WHERE {setor_predicate}
              AND f.codigo_filial = %s
              AND s.status_setor = 'ativo'
              AND s.deletado = FALSE
              AND f.deletado = FALSE
            """,
            (setor_param, filial_id),
        )
        return bool(row)

    def count_processos(self, setor_ref: str) -> int:
        row_data = self.get(setor_ref)
        if not row_data:
            return 0
        row = self.fetch_one(
            """
            SELECT COUNT(DISTINCT pi.processo_id)::int AS total
            FROM transformometro.processo_instancia_setores pis
            JOIN transformometro.processo_instancias pi
                ON pi.instancia_id = pis.instancia_id
            JOIN transformometro.processos p ON p.processo_id = pi.processo_id
            WHERE pis.setor_id = %s::uuid
              AND pi.deletado = FALSE
              AND p.deletado = FALSE
            """,
            (row_data["setor_id"],),
        )
        return int((row or {}).get("total") or 0)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        codigo_setor = normalize_codigo_setor(data.get("setor_id") or data["nome_setor"])
        if self.get(codigo_setor):
            raise ValueError(f"Setor '{codigo_setor}' já existe.")

        filiais = list(data["filiais"])
        self._validate_filiais(filiais)

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.setores (codigo_setor, nome_setor, status_setor)
            VALUES (%s, %s, %s)
            RETURNING setor_id, codigo_setor, nome_setor, status_setor, created_at, updated_at
            """,
            (
                codigo_setor,
                data["nome_setor"].strip(),
                data.get("status_setor", "ativo"),
            ),
            auto_commit=False,
        )
        if row is None:
            self._connection.rollback()
            raise RuntimeError("Falha ao criar setor.")

        self._sync_filiais(str(row["setor_id"]), filiais, auto_commit=True)
        created = self.get(str(row["setor_id"]))
        if created is None:
            raise RuntimeError("Falha ao carregar setor criado.")
        return created

    def update(self, setor_ref: str, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.get(setor_ref)
        if not existing:
            return None

        filiais = list(data["filiais"])
        self._validate_filiais(filiais)

        row = self.execute_returning_one(
            """
            UPDATE transformometro.setores SET
                nome_setor = %s,
                status_setor = %s,
                updated_at = NOW()
            WHERE setor_id = %s::uuid AND deletado = FALSE
            RETURNING setor_id
            """,
            (
                data["nome_setor"].strip(),
                data.get("status_setor", "ativo"),
                existing["setor_id"],
            ),
            auto_commit=False,
        )
        if row is None:
            self._connection.rollback()
            return None

        self._sync_filiais(str(existing["setor_id"]), filiais, auto_commit=True)
        return self.get(str(existing["setor_id"]))

    def soft_delete(self, setor_ref: str) -> bool:
        if self.count_processos(setor_ref) > 0:
            raise ValueError(
                "Não é possível excluir setor vinculado a processos. "
                "Altere os processos ou desative o setor."
            )
        setor_uuid = self._resolve_setor_uuid(setor_ref)
        if not setor_uuid:
            return False

        row = self.execute_returning_one(
            """
            UPDATE transformometro.setores
            SET deletado = TRUE, updated_at = NOW()
            WHERE setor_id = %s::uuid AND deletado = FALSE
            RETURNING setor_id
            """,
            (setor_uuid,),
        )
        return row is not None
