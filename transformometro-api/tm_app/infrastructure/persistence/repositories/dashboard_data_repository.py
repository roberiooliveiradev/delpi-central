from __future__ import annotations

from typing import Any

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class DashboardDataRepository(PluginBaseRepository):
    def load_raw(self) -> TransformometroRawData:
        processos = self.fetch_all(
            "SELECT * FROM transformometro.processos WHERE deletado = FALSE"
        )
        revisoes = self.fetch_all(
            "SELECT * FROM transformometro.revisoes WHERE deletado = FALSE"
        )
        medicoes = self.fetch_all(
            "SELECT * FROM transformometro.medicoes WHERE deletado = FALSE"
        )
        investimentos = self.fetch_all(
            "SELECT * FROM transformometro.investimentos WHERE deletado = FALSE"
        )
        recursos = self.fetch_all(
            "SELECT * FROM transformometro.recursos_compartilhados WHERE deletado = FALSE"
        )
        vinculos = self.fetch_all(
            "SELECT * FROM transformometro.revisao_recursos_compartilhados WHERE deletado = FALSE"
        )
        return TransformometroRawData(
            processos=processos,
            revisoes=revisoes,
            medicoes=medicoes,
            investimentos=investimentos,
            recursos_compartilhados=recursos,
            revisao_recursos_compartilhados=vinculos,
        )


class DashboardCalculoRepository(PluginBaseRepository):
    def _insert_row(self, row: dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO transformometro.dashboard_calculos (
                dashboard_calculo_id, revisao_id, processo_id, competencia,
                filial_id, setor_id, cenario_tipo, revisao_ativa,
                economia_tempo, economia_retrabalho, economia_erros, economia_outros,
                economia_recursos_compartilhados, economia_bruta,
                investimento_unico_mes, custo_recorrente_mes, economia_liquida_mes,
                custo_recursos_compartilhados_mes, horas_economizadas_mes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (dashboard_calculo_id) DO UPDATE SET
                revisao_id = EXCLUDED.revisao_id,
                processo_id = EXCLUDED.processo_id,
                competencia = EXCLUDED.competencia,
                filial_id = EXCLUDED.filial_id,
                setor_id = EXCLUDED.setor_id,
                cenario_tipo = EXCLUDED.cenario_tipo,
                revisao_ativa = EXCLUDED.revisao_ativa,
                economia_tempo = EXCLUDED.economia_tempo,
                economia_retrabalho = EXCLUDED.economia_retrabalho,
                economia_erros = EXCLUDED.economia_erros,
                economia_outros = EXCLUDED.economia_outros,
                economia_recursos_compartilhados = EXCLUDED.economia_recursos_compartilhados,
                economia_bruta = EXCLUDED.economia_bruta,
                investimento_unico_mes = EXCLUDED.investimento_unico_mes,
                custo_recorrente_mes = EXCLUDED.custo_recorrente_mes,
                economia_liquida_mes = EXCLUDED.economia_liquida_mes,
                custo_recursos_compartilhados_mes = EXCLUDED.custo_recursos_compartilhados_mes,
                horas_economizadas_mes = EXCLUDED.horas_economizadas_mes,
                calculated_at = NOW()
            """,
            (
                row["dashboard_calculo_id"],
                row["revisao_id"],
                row["processo_id"],
                row["competencia"],
                row.get("filial_id"),
                row.get("setor_id"),
                row["cenario_tipo"],
                row.get("revisao_ativa", False),
                row.get("economia_tempo", 0),
                row.get("economia_retrabalho", 0),
                row.get("economia_erros", 0),
                row.get("economia_outros", 0),
                row.get("economia_recursos_compartilhados", 0),
                row.get("economia_bruta", 0),
                row.get("investimento_unico_mes", 0),
                row.get("custo_recorrente_mes", 0),
                row.get("economia_liquida_mes", 0),
                row.get("custo_recursos_compartilhados_mes", 0),
                row.get("horas_economizadas_mes", 0),
            ),
        )

    def upsert_rows(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        for row in rows:
            self._insert_row(row)
        return len(rows)

    def replace_all(self, rows: list[dict[str, Any]]) -> int:
        self.execute("TRUNCATE transformometro.dashboard_calculos")
        return self.upsert_rows(rows)

    def delete_by_revisao(self, revisao_id: str) -> int:
        row = self.fetch_one(
            """
            WITH deleted AS (
                DELETE FROM transformometro.dashboard_calculos
                WHERE revisao_id = %s
                RETURNING 1
            )
            SELECT COUNT(*)::int AS total FROM deleted
            """,
            (revisao_id,),
        )
        return int((row or {}).get("total") or 0)

    def delete_by_processo(self, processo_id: str) -> int:
        row = self.fetch_one(
            """
            WITH deleted AS (
                DELETE FROM transformometro.dashboard_calculos
                WHERE processo_id = %s
                RETURNING 1
            )
            SELECT COUNT(*)::int AS total FROM deleted
            """,
            (processo_id,),
        )
        return int((row or {}).get("total") or 0)

    def delete_by_competencia_range(
        self,
        *,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> int:
        clauses: list[str] = []
        params: list[Any] = []
        if competencia_inicio:
            clauses.append("competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("competencia <= %s")
            params.append(competencia_fim)
        if not clauses:
            return 0
        where_sql = " AND ".join(clauses)
        row = self.fetch_one(
            f"""
            WITH deleted AS (
                DELETE FROM transformometro.dashboard_calculos
                WHERE {where_sql}
                RETURNING 1
            )
            SELECT COUNT(*)::int AS total FROM deleted
            """,
            tuple(params),
        )
        return int((row or {}).get("total") or 0)

    def count(self) -> int:
        row = self.fetch_one("SELECT COUNT(*)::int AS total FROM transformometro.dashboard_calculos")
        return int((row or {}).get("total") or 0)

    def query_resumo(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []

        if filial_id:
            clauses.append("filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("setor_id = %s")
            params.append(setor_id)
        if competencia_inicio:
            clauses.append("competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("competencia <= %s")
            params.append(competencia_fim)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        return self.fetch_one(
            f"""
            SELECT
                COUNT(DISTINCT revisao_id) FILTER (
                    WHERE cenario_tipo IN ('melhoria', 'automacao', 'correcao')
                ) AS solucoes_implementadas,
                COALESCE(SUM(economia_bruta), 0) AS economia_bruta_total,
                COALESCE(SUM(economia_liquida_mes), 0) AS economia_liquida_total,
                COALESCE(SUM(investimento_unico_mes), 0) AS investimento_unico_total,
                COALESCE(SUM(custo_recorrente_mes), 0) AS custo_recorrente_total,
                COALESCE(SUM(horas_economizadas_mes), 0) AS horas_economizadas_total
            FROM transformometro.dashboard_calculos
            {where_sql}
            """,
            tuple(params),
        ) or {}

    def query_evolucao(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if filial_id:
            clauses.append("filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("setor_id = %s")
            params.append(setor_id)
        if competencia_inicio:
            clauses.append("competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("competencia <= %s")
            params.append(competencia_fim)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        return self.fetch_all(
            f"""
            SELECT
                competencia,
                SUM(economia_bruta) AS economia_bruta,
                SUM(investimento_unico_mes) AS investimento_unico_mes,
                SUM(custo_recorrente_mes) AS custo_recorrente_mes,
                SUM(economia_liquida_mes) AS economia_liquida_mes
            FROM transformometro.dashboard_calculos
            {where_sql}
            GROUP BY competencia
            ORDER BY competencia ASC
            """,
            tuple(params),
        )

    def query_ranking_processos(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if filial_id:
            clauses.append("d.filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("d.setor_id = %s")
            params.append(setor_id)
        if competencia:
            clauses.append("d.competencia = %s")
            params.append(competencia)
        else:
            clauses.append(
                "d.competencia = (SELECT MAX(competencia) FROM transformometro.dashboard_calculos)"
            )

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        return self.fetch_all(
            f"""
            SELECT
                p.processo_id,
                p.codigo_processo,
                p.nome_processo,
                p.filial_id,
                p.setor_id,
                SUM(d.economia_liquida_mes) AS economia_liquida_mes,
                SUM(d.economia_bruta) AS economia_bruta,
                SUM(d.economia_liquida_mes) / 30.0 AS economia_diaria
            FROM transformometro.dashboard_calculos d
            JOIN transformometro.processos p ON p.processo_id = d.processo_id
            {where_sql}
            GROUP BY p.processo_id, p.codigo_processo, p.nome_processo, p.filial_id, p.setor_id
            ORDER BY economia_liquida_mes DESC
            LIMIT %s
            """,
            tuple(params),
        )

    def query_process_monthly_liquida(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')"]
        params: list[Any] = []

        if filial_id:
            clauses.append("d.filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("d.setor_id = %s")
            params.append(setor_id)
        if familia_processo:
            clauses.append("p.familia_processo = %s")
            params.append(familia_processo)
        if competencia_inicio:
            clauses.append("d.competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("d.competencia <= %s")
            params.append(competencia_fim)

        where_sql = " AND ".join(clauses)

        return self.fetch_all(
            f"""
            SELECT
                d.processo_id,
                p.codigo_processo,
                p.nome_processo,
                p.filial_id,
                p.setor_id,
                p.familia_processo,
                p.agrupador_ferramenta,
                d.competencia,
                SUM(d.economia_liquida_mes) AS economia_liquida_mes
            FROM transformometro.dashboard_calculos d
            JOIN transformometro.processos p ON p.processo_id = d.processo_id
            WHERE {where_sql}
            GROUP BY
                d.processo_id, p.codigo_processo, p.nome_processo,
                p.filial_id, p.setor_id, p.familia_processo, p.agrupador_ferramenta,
                d.competencia
            ORDER BY d.processo_id, d.competencia
            """,
            tuple(params),
        )

    def query_export_rows(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if filial_id:
            clauses.append("d.filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("d.setor_id = %s")
            params.append(setor_id)
        if familia_processo:
            clauses.append("p.familia_processo = %s")
            params.append(familia_processo)
        if competencia_inicio:
            clauses.append("d.competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("d.competencia <= %s")
            params.append(competencia_fim)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        return self.fetch_all(
            f"""
            SELECT
                p.codigo_processo,
                p.nome_processo,
                p.familia_processo,
                p.agrupador_ferramenta,
                d.filial_id,
                d.setor_id,
                d.competencia,
                d.cenario_tipo,
                d.economia_bruta,
                d.economia_liquida_mes,
                d.investimento_unico_mes,
                d.custo_recorrente_mes,
                d.horas_economizadas_mes
            FROM transformometro.dashboard_calculos d
            JOIN transformometro.processos p ON p.processo_id = d.processo_id
            {where_sql}
            ORDER BY d.competencia, p.codigo_processo
            """,
            tuple(params),
        )

    def query_resumo_por_familia(
        self,
        *,
        filial_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["p.familia_processo IS NOT NULL", "p.familia_processo <> ''"]
        params: list[Any] = []

        if filial_id:
            clauses.append("d.filial_id = %s")
            params.append(filial_id)
        if competencia_inicio:
            clauses.append("d.competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("d.competencia <= %s")
            params.append(competencia_fim)

        where_sql = " AND ".join(clauses)

        return self.fetch_all(
            f"""
            SELECT
                p.familia_processo,
                COUNT(DISTINCT d.processo_id) AS processos,
                SUM(d.economia_bruta) AS economia_bruta,
                SUM(d.economia_liquida_mes) AS economia_liquida_mes
            FROM transformometro.dashboard_calculos d
            JOIN transformometro.processos p ON p.processo_id = d.processo_id
            WHERE {where_sql}
            GROUP BY p.familia_processo
            ORDER BY economia_liquida_mes DESC
            """,
            tuple(params),
        )
