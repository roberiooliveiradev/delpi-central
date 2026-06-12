from __future__ import annotations

from datetime import datetime
from typing import Any

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class MotivoRepository(PluginBaseRepository):
    def list_active(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT motivo_id, descricao
            FROM maintenance.motivos
            WHERE excluido = FALSE
            ORDER BY descricao
            """
        )

    def create(self, descricao: str) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.motivos (descricao)
            VALUES (%s)
            RETURNING motivo_id, descricao
            """,
            (descricao.strip(),),
        )
        return row or {}

    def update(self, motivo_id: int, descricao: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE maintenance.motivos
            SET descricao = %s,
                data_alteracao = NOW()
            WHERE motivo_id = %s
              AND excluido = FALSE
            RETURNING motivo_id, descricao
            """,
            (descricao.strip(), motivo_id),
        )

    def soft_delete(self, motivo_id: int) -> bool:
        self.execute(
            """
            UPDATE maintenance.motivos
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE motivo_id = %s
              AND excluido = FALSE
            """,
            (motivo_id,),
        )
        return True


class StatusPecaRepository(PluginBaseRepository):
    def list_active(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT status_id, descricao, operador, percentual
            FROM maintenance.status_peca
            WHERE excluido = FALSE
            ORDER BY percentual DESC, descricao
            """
        )

    def update(
        self,
        status_id: int,
        *,
        descricao: str | None = None,
        operador: str | None = None,
        percentual: int | None = None,
    ) -> dict[str, Any] | None:
        row = self.fetch_one(
            "SELECT * FROM maintenance.status_peca WHERE status_id = %s AND excluido = FALSE",
            (status_id,),
        )
        if not row:
            return None
        return self.execute_returning_one(
            """
            UPDATE maintenance.status_peca
            SET descricao = %s,
                operador = %s,
                percentual = %s,
                data_alteracao = NOW()
            WHERE status_id = %s
            RETURNING status_id, descricao, operador, percentual
            """,
            (
                descricao if descricao is not None else row["descricao"],
                operador if operador is not None else row["operador"],
                percentual if percentual is not None else row["percentual"],
                status_id,
            ),
        )


class ReposicaoRepository(PluginBaseRepository):
    def list_by_ferramenta(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str | None = None,
    ) -> list[dict[str, Any]]:
        where = [
            "r.excluido = FALSE",
            "r.filial = %s",
            "r.codigo_ferramenta = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta]
        if codigo_peca:
            where.append("r.codigo_peca = %s")
            params.append(codigo_peca)

        return self.fetch_all(
            f"""
            SELECT
                r.reposicao_id,
                r.filial,
                r.codigo_ferramenta,
                r.codigo_peca,
                r.data_reposicao,
                r.data_ultima_reposicao,
                r.golpes,
                r.motivo_id,
                m.descricao AS motivo_descricao,
                r.observacao,
                r.data_criacao,
                r.data_alteracao
            FROM maintenance.reposicoes r
            INNER JOIN maintenance.motivos m ON m.motivo_id = r.motivo_id
            WHERE {' AND '.join(where)}
            ORDER BY r.data_reposicao DESC, r.data_criacao DESC
            """,
            tuple(params),
        )

    def get_by_id(self, reposicao_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT *
            FROM maintenance.reposicoes
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            """,
            (reposicao_id,),
        )

    def get_ultima_data(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> datetime | None:
        row = self.fetch_one(
            """
            SELECT data_reposicao
            FROM maintenance.reposicoes
            WHERE excluido = FALSE
              AND filial = %s
              AND codigo_ferramenta = %s
              AND codigo_peca = %s
            ORDER BY data_reposicao DESC
            LIMIT 1
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        if not row:
            return None
        return row["data_reposicao"]

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.reposicoes (
                filial,
                codigo_ferramenta,
                codigo_peca,
                data_reposicao,
                data_ultima_reposicao,
                golpes,
                motivo_id,
                observacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                payload["filial"],
                payload["codigo_ferramenta"],
                payload["codigo_peca"],
                payload["data_reposicao"],
                payload.get("data_ultima_reposicao"),
                payload["golpes"],
                payload["motivo_id"],
                payload.get("observacao"),
            ),
        )
        return row or {}

    def update(self, reposicao_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE maintenance.reposicoes
            SET filial = %s,
                codigo_ferramenta = %s,
                codigo_peca = %s,
                data_reposicao = %s,
                data_ultima_reposicao = %s,
                golpes = %s,
                motivo_id = %s,
                observacao = %s,
                data_alteracao = NOW()
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            RETURNING *
            """,
            (
                payload["filial"],
                payload["codigo_ferramenta"],
                payload["codigo_peca"],
                payload["data_reposicao"],
                payload.get("data_ultima_reposicao"),
                payload["golpes"],
                payload["motivo_id"],
                payload.get("observacao"),
                reposicao_id,
            ),
        )

    def soft_delete(self, reposicao_id: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.reposicoes
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            """,
            (reposicao_id,),
        )
        return True

    def list_golpes_history(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> list[int]:
        rows = self.fetch_all(
            """
            SELECT golpes
            FROM maintenance.reposicoes
            WHERE excluido = FALSE
              AND filial = %s
              AND codigo_ferramenta = %s
              AND codigo_peca = %s
            ORDER BY data_reposicao ASC
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        return [int(row["golpes"]) for row in rows]

    def list_ultimas_por_par(self, *, filial: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT DISTINCT ON (filial, codigo_ferramenta, codigo_peca)
                reposicao_id,
                filial,
                codigo_ferramenta,
                codigo_peca,
                data_reposicao,
                golpes
            FROM maintenance.reposicoes
            WHERE excluido = FALSE
              AND filial = %s
            ORDER BY filial, codigo_ferramenta, codigo_peca, data_reposicao DESC
            """,
            (filial,),
        )

    def media_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> float:
        row = self.fetch_one(
            """
            SELECT COALESCE(AVG(golpes), 0) AS media
            FROM maintenance.reposicoes
            WHERE excluido = FALSE
              AND filial = %s
              AND codigo_ferramenta = %s
              AND codigo_peca = %s
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        if not row:
            return 0.0
        return float(row.get("media") or 0)
