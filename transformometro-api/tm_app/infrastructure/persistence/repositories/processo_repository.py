from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_PROCESSO_SELECT = """
    SELECT
        p.processo_id,
        p.codigo_processo,
        p.nome_processo,
        p.descricao_processo,
        p.gestor_responsavel,
        p.objetivo_processo,
        p.status_processo,
        p.familia_processo,
        p.agrupador_ferramenta,
        p.created_at,
        p.updated_at,
        p.deletado,
        pi.instancia_id,
        f.codigo_filial AS filial_id,
        s.codigo_setor AS setor_id
    FROM transformometro.processos p
    LEFT JOIN LATERAL (
        SELECT pi2.instancia_id, pi2.filial_id, pi2.setor_id
        FROM transformometro.processo_instancias pi2
        WHERE pi2.processo_id = p.processo_id
          AND pi2.deletado = FALSE
        ORDER BY pi2.created_at ASC
        LIMIT 1
    ) pi ON TRUE
    LEFT JOIN transformometro.filiais f
        ON f.filial_id = pi.filial_id AND f.deletado = FALSE
    LEFT JOIN transformometro.setores s
        ON s.setor_id = pi.setor_id AND s.deletado = FALSE
"""


class ProcessoRepository(PluginBaseRepository):
    def next_codigo(self) -> str:
        # Inclui registros deletados: uq_processos_codigo vale para todos.
        row = self.fetch_one(
            """
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(codigo_processo FROM 6) AS INTEGER)), 0
            ) + 1 AS seq
            FROM transformometro.processos
            WHERE codigo_processo ~ '^PROC-[0-9]+$'
            """
        )
        seq = int((row or {}).get("seq") or 1)
        return f"PROC-{seq:04d}"

    def list(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        status_processo: str | None = None,
        familia_processo: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["p.deletado = FALSE"]
        params: list[Any] = []

        if filial_id:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM transformometro.processo_instancias pi_f
                    JOIN transformometro.filiais f_f ON f_f.filial_id = pi_f.filial_id
                    WHERE pi_f.processo_id = p.processo_id
                      AND pi_f.deletado = FALSE
                      AND f_f.codigo_filial = %s
                      AND f_f.deletado = FALSE
                )
                """
            )
            params.append(filial_id)
        if setor_id:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM transformometro.processo_instancias pi_s
                    JOIN transformometro.setores s_s ON s_s.setor_id = pi_s.setor_id
                    WHERE pi_s.processo_id = p.processo_id
                      AND pi_s.deletado = FALSE
                      AND s_s.codigo_setor = %s
                      AND s_s.deletado = FALSE
                )
                """
            )
            params.append(setor_id)
        if status_processo:
            clauses.append("p.status_processo = %s")
            params.append(status_processo)
        if familia_processo:
            clauses.append("p.familia_processo = %s")
            params.append(familia_processo)
        if q:
            clauses.append(
                "(p.nome_processo ILIKE %s OR p.codigo_processo ILIKE %s OR p.familia_processo ILIKE %s)"
            )
            like = f"%{q}%"
            params.extend([like, like, like])

        where_sql = " AND ".join(clauses)
        return self.fetch_all(
            f"""
            {_PROCESSO_SELECT}
            WHERE {where_sql}
            ORDER BY p.updated_at DESC, p.nome_processo ASC
            """,
            tuple(params),
        )

    def get(self, processo_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_PROCESSO_SELECT}
            WHERE p.processo_id = %s AND p.deletado = FALSE
            """,
            (processo_id,),
        )

    def create(self, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        codigo = data.get("codigo_processo") or self.next_codigo()
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.processos (
                codigo_processo, nome_processo, descricao_processo,
                gestor_responsavel, objetivo_processo,
                status_processo, familia_processo, agrupador_ferramenta
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING processo_id, codigo_processo, nome_processo, descricao_processo,
                      gestor_responsavel, objetivo_processo, status_processo,
                      familia_processo, agrupador_ferramenta, created_at, updated_at, deletado
            """,
            (
                codigo,
                data["nome_processo"],
                data.get("descricao_processo"),
                data.get("gestor_responsavel"),
                data.get("objetivo_processo"),
                data["status_processo"],
                data.get("familia_processo"),
                data.get("agrupador_ferramenta"),
            ),
            auto_commit=auto_commit,
        )
        if row is None:
            raise RuntimeError("Falha ao criar processo.")
        return row

    def update(self, processo_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.processos SET
                nome_processo = %s,
                descricao_processo = %s,
                gestor_responsavel = %s,
                objetivo_processo = %s,
                status_processo = %s,
                familia_processo = %s,
                agrupador_ferramenta = %s,
                updated_at = NOW()
            WHERE processo_id = %s AND deletado = FALSE
            RETURNING processo_id
            """,
            (
                data["nome_processo"],
                data.get("descricao_processo"),
                data.get("gestor_responsavel"),
                data.get("objetivo_processo"),
                data["status_processo"],
                data.get("familia_processo"),
                data.get("agrupador_ferramenta"),
                processo_id,
            ),
        )
        if row is None:
            return None
        return self.get(processo_id)

    def soft_delete(self, processo_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.processos
            SET deletado = TRUE, updated_at = NOW()
            WHERE processo_id = %s AND deletado = FALSE
            RETURNING processo_id
            """,
            (processo_id,),
        )
        return row is not None
