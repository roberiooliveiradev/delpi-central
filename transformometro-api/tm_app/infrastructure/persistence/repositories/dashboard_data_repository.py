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
    def replace_all(self, rows: list[dict[str, Any]]) -> int:
        self.execute("TRUNCATE transformometro.dashboard_calculos")
        if not rows:
            return 0

        inserted = 0
        for row in rows:
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
            inserted += 1
        return inserted

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
