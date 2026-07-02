from __future__ import annotations

import json
from typing import Any

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_cache_denorm_service import (
    filial_filter_sql,
    setor_filter_sql,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

# Expressões alinhadas ao cálculo em tempo real (DashboardCalculatorService).
_INVESTIMENTO_TOTAL_SQL = """
    COALESCE(investimento_unico_mes, 0)
  + COALESCE(custo_recorrente_mes, 0)
  + COALESCE(custo_recursos_compartilhados_mes, 0)
"""

# Cenários comparáveis materializados no cache (baseline não é materializado).
_COMPARABLE_CENARIOS_SQL = "d.cenario_tipo IN ('melhoria', 'automacao', 'correcao')"

# Instância como ambiente: NULL (legado) cai para o processo (1 instância).
_INSTANCE_KEY_SQL = "COALESCE(d.instancia_id::text, d.processo_id::text)"


def _instance_average_cte(row_where_sql: str) -> str:
    """CTE de agregação em 2 níveis para a **média por instância** (regra jul/2026).

    - ``inst_lvl``: soma as revisões dentro de cada instância (grão instância × competência).
    - ``proc_lvl``: média entre as instâncias ativas (grão processo × competência).

    O filtro de escopo (filial/setor) entra em ``row_where_sql`` no grão de linha, logo o
    consolidado vira a média das instâncias e o recorte por unidade sobra 1 instância
    (``AVG`` de 1 = valor real). Espelha ``DashboardCalculatorService`` /
    ``calc_rules.prorate_dashboard_row_for_period``.
    """
    return f"""
    WITH inst_lvl AS (
        SELECT
            d.processo_id AS processo_id,
            d.competencia AS competencia,
            {_INSTANCE_KEY_SQL} AS instancia_key,
            MAX(d.codigo_filial) AS codigo_filial,
            MAX(d.codigo_setor) AS codigo_setor,
            SUM(COALESCE(d.economia_bruta, 0)) AS economia_bruta,
            SUM(COALESCE(d.economia_liquida_mes, 0)) AS economia_liquida_mes,
            SUM(COALESCE(d.investimento_unico_mes, 0)) AS investimento_unico_mes,
            SUM(COALESCE(d.custo_recorrente_mes, 0)) AS custo_recorrente_mes,
            SUM(COALESCE(d.custo_recursos_compartilhados_mes, 0))
                AS custo_recursos_compartilhados_mes,
            SUM(COALESCE(d.horas_economizadas_mes, 0)) AS horas_economizadas_mes,
            COUNT(DISTINCT d.revisao_id) AS revisoes,
            MAX(d.calculated_at) AS calculated_at
        FROM transformometro.dashboard_calculos d
        WHERE {row_where_sql}
        GROUP BY d.processo_id, d.competencia, {_INSTANCE_KEY_SQL}
    ),
    proc_lvl AS (
        SELECT
            processo_id,
            competencia,
            AVG(economia_bruta) AS economia_bruta,
            AVG(economia_liquida_mes) AS economia_liquida_mes,
            AVG(investimento_unico_mes) AS investimento_unico_mes,
            AVG(custo_recorrente_mes) AS custo_recorrente_mes,
            AVG(custo_recursos_compartilhados_mes) AS custo_recursos_compartilhados_mes,
            AVG(horas_economizadas_mes) AS horas_economizadas_mes,
            SUM(revisoes) AS revisoes,
            MAX(codigo_filial) AS codigo_filial,
            MAX(codigo_setor) AS codigo_setor,
            MAX(calculated_at) AS calculated_at,
            COUNT(*) AS instancias_ativas
        FROM inst_lvl
        GROUP BY processo_id, competencia
    )
    """
class DashboardDataRepository(PluginBaseRepository):
    def load_raw(self) -> TransformometroRawData:
        processos = self.fetch_all(
            """
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
                SELECT pi2.instancia_id, pi2.filial_id
                FROM transformometro.processo_instancias pi2
                WHERE pi2.processo_id = p.processo_id
                  AND pi2.deletado = FALSE
                ORDER BY pi2.created_at ASC
                LIMIT 1
            ) pi ON TRUE
            LEFT JOIN transformometro.filiais f
                ON f.filial_id = pi.filial_id AND f.deletado = FALSE
            LEFT JOIN LATERAL (
                SELECT s.codigo_setor
                FROM transformometro.processo_instancia_setores pis
                JOIN transformometro.setores s ON s.setor_id = pis.setor_id AND s.deletado = FALSE
                WHERE pis.instancia_id = pi.instancia_id
                ORDER BY s.codigo_setor ASC
                LIMIT 1
            ) s ON TRUE
            WHERE p.deletado = FALSE
            """
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
        custos = self.fetch_all(
            "SELECT * FROM transformometro.recurso_custos WHERE deletado = FALSE"
        )
        instancias = self.fetch_all(
            """
            SELECT
                pi.instancia_id,
                pi.processo_id,
                pi.filial_id,
                pi.todas_filiais_ativas,
                f.codigo_filial,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'setor_id', s.setor_id,
                            'codigo_setor', s.codigo_setor,
                            'nome_setor', s.nome_setor
                        )
                        ORDER BY s.codigo_setor
                    ) FILTER (WHERE s.setor_id IS NOT NULL),
                    '[]'::json
                ) AS setores
            FROM transformometro.processo_instancias pi
            LEFT JOIN transformometro.filiais f
                ON f.filial_id = pi.filial_id AND f.deletado = FALSE
            LEFT JOIN transformometro.processo_instancia_setores pis
                ON pis.instancia_id = pi.instancia_id
            LEFT JOIN transformometro.setores s
                ON s.setor_id = pis.setor_id AND s.deletado = FALSE
            WHERE pi.deletado = FALSE
            GROUP BY
                pi.instancia_id,
                pi.processo_id,
                pi.filial_id,
                pi.todas_filiais_ativas,
                f.codigo_filial
            """
        )
        for row in instancias:
            setores = row.get("setores") or []
            if isinstance(setores, str):
                setores = json.loads(setores)
            row["setores"] = setores
            if setores:
                first = setores[0]
                row["setor_id"] = first.get("setor_id")
                row["codigo_setor"] = first.get("codigo_setor")
        return TransformometroRawData(
            processos=processos,
            processo_instancias=instancias,
            revisoes=revisoes,
            medicoes=medicoes,
            investimentos=investimentos,
            recursos_compartilhados=recursos,
            revisao_recursos_compartilhados=vinculos,
            recurso_custos=custos,
        )


class DashboardCalculoRepository(PluginBaseRepository):
    _UPSERT_SQL = """
            INSERT INTO transformometro.dashboard_calculos (
                revisao_id, processo_id, instancia_id, competencia,
                filial_id, setor_id, codigo_filial, codigo_setor,
                cenario_tipo, revisao_ativa,
                economia_tempo, economia_retrabalho, economia_erros, economia_outros,
                economia_recursos_compartilhados, economia_bruta,
                investimento_unico_mes, custo_recorrente_mes, economia_liquida_mes,
                custo_recursos_compartilhados_mes, horas_economizadas_mes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (revisao_id, competencia) DO UPDATE SET
                processo_id = EXCLUDED.processo_id,
                instancia_id = EXCLUDED.instancia_id,
                filial_id = EXCLUDED.filial_id,
                setor_id = EXCLUDED.setor_id,
                codigo_filial = EXCLUDED.codigo_filial,
                codigo_setor = EXCLUDED.codigo_setor,
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
            """

    def _row_where(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        extra_clauses: list[str] | None = None,
        extra_params: list[Any] | None = None,
    ) -> tuple[str, list[Any]]:
        """WHERE no grão de linha (alias ``d``) para alimentar ``_instance_average_cte``."""
        clauses: list[str] = [_COMPARABLE_CENARIOS_SQL]
        params: list[Any] = []
        self._append_scope_filters(
            clauses, params, table_alias="d", filial_id=filial_id, setor_id=setor_id
        )
        if competencia_inicio:
            clauses.append("d.competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("d.competencia <= %s")
            params.append(competencia_fim)
        if extra_clauses:
            clauses.extend(extra_clauses)
        if extra_params:
            params.extend(extra_params)
        return " AND ".join(clauses), params

    @staticmethod
    def _append_scope_filters(
        clauses: list[str],
        params: list[Any],
        *,
        table_alias: str | None = "d",
        filial_id: str | None = None,
        setor_id: str | None = None,
    ) -> None:
        if filial_id:
            sql, bound = filial_filter_sql(table_alias or "", filial_id)
            clauses.append(sql)
            params.extend(bound)
        if setor_id:
            sql, bound = setor_filter_sql(table_alias or "", setor_id)
            clauses.append(sql)
            params.extend(bound)

    def _row_params(self, row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            row["revisao_id"],
            row["processo_id"],
            row.get("instancia_id"),
            row["competencia"],
            row.get("filial_id"),
            row.get("setor_id"),
            row.get("codigo_filial"),
            row.get("codigo_setor"),
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
        )

    def _upsert_many(self, rows: list[dict[str, Any]], *, auto_commit: bool = True) -> int:
        if not rows:
            return 0
        params = [self._row_params(row) for row in rows]
        try:
            with self._connection.cursor() as cursor:
                cursor.executemany(self._UPSERT_SQL, params)
            if auto_commit:
                self._connection.commit()
        except Exception as exc:
            self._connection.rollback()
            raise exc
        return len(rows)

    def _insert_row(self, row: dict[str, Any]) -> None:
        self._upsert_many([row])

    def upsert_rows(self, rows: list[dict[str, Any]]) -> int:
        return self._upsert_many(rows)

    def replace_all(self, rows: list[dict[str, Any]]) -> int:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("TRUNCATE transformometro.dashboard_calculos")
                if rows:
                    cursor.executemany(self._UPSERT_SQL, [self._row_params(row) for row in rows])
            self._connection.commit()
        except Exception as exc:
            self._connection.rollback()
            raise exc
        return len(rows)

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

    def latest_calculated_at(self) -> str | None:
        row = self.fetch_one(
            "SELECT MAX(calculated_at) AS latest FROM transformometro.dashboard_calculos"
        )
        latest = (row or {}).get("latest")
        return str(latest) if latest is not None else None

    def query_linhas(
        self,
        *,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if processo_id:
            clauses.append("d.processo_id = %s")
            params.append(processo_id)
        if revisao_id:
            clauses.append("d.revisao_id = %s")
            params.append(revisao_id)
        self._append_scope_filters(
            clauses, params, filial_id=filial_id, setor_id=setor_id
        )
        if competencia_inicio:
            clauses.append("d.competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("d.competencia <= %s")
            params.append(competencia_fim)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        return self.fetch_all(
            f"""
            SELECT
                d.dashboard_calculo_id,
                d.revisao_id,
                d.processo_id,
                p.codigo_processo,
                p.nome_processo,
                d.competencia,
                d.instancia_id,
                d.codigo_filial AS filial_id,
                d.codigo_setor AS setor_id,
                d.cenario_tipo,
                d.revisao_ativa,
                d.economia_bruta,
                d.economia_liquida_mes,
                d.investimento_unico_mes,
                d.custo_recorrente_mes,
                d.custo_recursos_compartilhados_mes,
                (
                    COALESCE(d.investimento_unico_mes, 0)
                  + COALESCE(d.custo_recorrente_mes, 0)
                  + COALESCE(d.custo_recursos_compartilhados_mes, 0)
                ) AS investimento_total_mes,
                d.horas_economizadas_mes,
                d.calculated_at
            FROM transformometro.dashboard_calculos d
            JOIN transformometro.processos p ON p.processo_id = d.processo_id
            {where_sql}
            ORDER BY d.competencia DESC, p.codigo_processo ASC
            LIMIT %s
            """,
            tuple(params),
        )

    def query_processo_competencia_snapshot(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if filial_id:
            clauses.append("filial_id = %s")
            params.append(filial_id)
        if setor_id:
            clauses.append("setor_id = %s")
            params.append(setor_id)
        if familia_processo:
            clauses.append("familia_processo = %s")
            params.append(familia_processo)
        if processo_id:
            clauses.append("processo_id = %s")
            params.append(processo_id)
        if competencia_inicio:
            clauses.append("competencia >= %s")
            params.append(competencia_inicio)
        if competencia_fim:
            clauses.append("competencia <= %s")
            params.append(competencia_fim)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        return self.fetch_all(
            f"""
            SELECT *
            FROM transformometro.processo_competencia_snapshot
            {where_sql}
            ORDER BY competencia DESC, economia_liquida_mes DESC
            LIMIT %s
            """,
            tuple(params),
        )

    def query_resumo(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        where_sql, params = self._row_where(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        cte = _instance_average_cte(where_sql)
        # ``solucoes_implementadas`` = nº de soluções (distintas) no recorte — não é média.
        # A subquery reaproveita o mesmo WHERE, então os parâmetros entram duas vezes.
        full_params = list(params) + list(params)

        return self.fetch_one(
            f"""
            {cte}
            SELECT
                (
                    SELECT COUNT(DISTINCT d.revisao_id)
                    FROM transformometro.dashboard_calculos d
                    WHERE {where_sql}
                ) AS solucoes_implementadas,
                COALESCE(SUM(economia_bruta), 0) AS economia_bruta_total,
                COALESCE(SUM(economia_liquida_mes), 0) AS economia_liquida_total,
                COALESCE(SUM(investimento_unico_mes), 0) AS investimento_unico_total,
                COALESCE(SUM(custo_recorrente_mes), 0) AS custo_recorrente_total,
                COALESCE(SUM(custo_recursos_compartilhados_mes), 0)
                    AS custo_recursos_compartilhados_total,
                COALESCE(SUM(
                    COALESCE(investimento_unico_mes, 0)
                  + COALESCE(custo_recorrente_mes, 0)
                  + COALESCE(custo_recursos_compartilhados_mes, 0)
                ), 0) AS investimento_total,
                COALESCE(SUM(horas_economizadas_mes), 0) AS horas_economizadas_total
            FROM proc_lvl
            """,
            tuple(full_params),
        ) or {}

    def query_evolucao(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        # Média por instância: filtro de escopo no grão de linha, soma dos processos por
        # competência (cada processo já contribui com a média das suas instâncias ativas).
        where_sql, params = self._row_where(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        cte = _instance_average_cte(where_sql)

        return self.fetch_all(
            f"""
            {cte}
            SELECT
                competencia,
                COALESCE(SUM(economia_bruta), 0) AS economia_bruta,
                COALESCE(SUM(investimento_unico_mes), 0) AS investimento_unico_mes,
                COALESCE(SUM(custo_recorrente_mes), 0) AS custo_recorrente_mes,
                COALESCE(SUM(custo_recursos_compartilhados_mes), 0)
                    AS custo_recursos_compartilhados_mes,
                COALESCE(SUM(
                    COALESCE(investimento_unico_mes, 0)
                  + COALESCE(custo_recorrente_mes, 0)
                  + COALESCE(custo_recursos_compartilhados_mes, 0)
                ), 0) AS investimento_total_mes,
                COALESCE(SUM(economia_liquida_mes), 0) AS economia_liquida_mes
            FROM proc_lvl
            GROUP BY competencia
            ORDER BY competencia ASC
            """,
            tuple(params),
        )

    def query_instancias_operacionais(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        self._append_scope_filters(
            clauses,
            params,
            table_alias="ios",
            filial_id=filial_id,
            setor_id=setor_id,
        )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        return self.fetch_all(
            f"""
            SELECT
                ios.instancia_id,
                ios.processo_id,
                ios.codigo_processo,
                ios.nome_processo,
                ios.status_processo,
                ios.todas_filiais_ativas,
                ios.codigo_filial AS filial_id,
                ios.nome_filial,
                ios.setor_id,
                ios.competencia_referencia,
                ios.economia_diaria,
                ios.payback_meses,
                ios.data_implantacao
            FROM transformometro.instancia_operacional_snapshot ios
            {where_sql}
            ORDER BY ios.nome_processo ASC, ios.codigo_filial ASC NULLS LAST
            LIMIT %s
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
        """Ranking legado sobre cache SQL. Preferir ``DashboardLiveService`` (calc_rules)."""
        if competencia:
            extra_clauses = ["d.competencia = %s"]
            extra_params: list[Any] = [competencia]
        else:
            extra_clauses = [
                "d.competencia = (SELECT MAX(competencia) FROM transformometro.dashboard_calculos)"
            ]
            extra_params = []

        where_sql, params = self._row_where(
            filial_id=filial_id,
            setor_id=setor_id,
            extra_clauses=extra_clauses,
            extra_params=extra_params,
        )
        cte = _instance_average_cte(where_sql)
        params = list(params) + [limit]

        # ``pl`` já traz a média por instância (grão processo × competência);
        # o ranking soma as competências do recorte por processo.
        return self.fetch_all(
            f"""
            {cte}
            SELECT
                p.processo_id,
                p.codigo_processo,
                p.nome_processo,
                MAX(pl.codigo_filial) AS filial_id,
                MAX(pl.codigo_setor) AS setor_id,
                SUM(pl.economia_liquida_mes) AS economia_liquida_mes,
                SUM(pl.economia_bruta) AS economia_bruta,
                SUM(pl.investimento_unico_mes) AS investimento_unico_mes,
                SUM(pl.custo_recorrente_mes) AS custo_recorrente_mes,
                SUM(pl.custo_recursos_compartilhados_mes) AS custo_recursos_compartilhados_mes,
                SUM(
                    COALESCE(pl.investimento_unico_mes, 0)
                  + COALESCE(pl.custo_recorrente_mes, 0)
                  + COALESCE(pl.custo_recursos_compartilhados_mes, 0)
                ) AS investimento_total_mes,
                SUM(pl.economia_bruta) / NULLIF(
                    EXTRACT(
                        DAY FROM (
                            (MAX(pl.competencia) || '-01')::date
                            + INTERVAL '1 month' - INTERVAL '1 day'
                        )
                    ),
                    0
                ) AS economia_diaria,
                SUM(pl.horas_economizadas_mes) / NULLIF(
                    EXTRACT(
                        DAY FROM (
                            (MAX(pl.competencia) || '-01')::date
                            + INTERVAL '1 month' - INTERVAL '1 day'
                        )
                    ),
                    0
                ) AS horas_diaria
            FROM proc_lvl pl
            JOIN transformometro.processos p ON p.processo_id = pl.processo_id
            GROUP BY
                p.processo_id,
                p.codigo_processo,
                p.nome_processo
            ORDER BY economia_diaria DESC
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
        where_sql, params = self._row_where(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        cte = _instance_average_cte(where_sql)

        familia_clause = ""
        full_params = list(params)
        if familia_processo:
            familia_clause = "WHERE p.familia_processo = %s"
            full_params.append(familia_processo)

        # ``pl.economia_liquida_mes`` já é a média das instâncias ativas no mês.
        return self.fetch_all(
            f"""
            {cte}
            SELECT
                pl.processo_id,
                p.codigo_processo,
                p.nome_processo,
                pl.codigo_filial AS filial_id,
                pl.codigo_setor AS setor_id,
                p.familia_processo,
                p.agrupador_ferramenta,
                pl.competencia,
                pl.economia_liquida_mes AS economia_liquida_mes
            FROM proc_lvl pl
            JOIN transformometro.processos p ON p.processo_id = pl.processo_id
            {familia_clause}
            ORDER BY pl.processo_id, pl.competencia
            """,
            tuple(full_params),
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

        self._append_scope_filters(
            clauses, params, filial_id=filial_id, setor_id=setor_id
        )
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
                d.codigo_filial AS filial_id,
                d.codigo_setor AS setor_id,
                d.competencia,
                d.cenario_tipo,
                d.economia_bruta,
                d.economia_liquida_mes,
                d.investimento_unico_mes,
                d.custo_recorrente_mes,
                d.custo_recursos_compartilhados_mes,
                (
                    COALESCE(d.investimento_unico_mes, 0)
                  + COALESCE(d.custo_recorrente_mes, 0)
                  + COALESCE(d.custo_recursos_compartilhados_mes, 0)
                ) AS investimento_total_mes,
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
        where_sql, params = self._row_where(
            filial_id=filial_id,
            setor_id=None,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        cte = _instance_average_cte(where_sql)

        # Cada processo contribui com a soma (no recorte) das suas médias por competência.
        return self.fetch_all(
            f"""
            {cte}
            SELECT
                p.familia_processo,
                COUNT(DISTINCT pl.processo_id) AS processos,
                COALESCE(SUM(pl.economia_bruta), 0) AS economia_bruta,
                COALESCE(SUM(pl.economia_liquida_mes), 0) AS economia_liquida_mes
            FROM proc_lvl pl
            JOIN transformometro.processos p ON p.processo_id = pl.processo_id
            WHERE p.familia_processo IS NOT NULL AND p.familia_processo <> ''
            GROUP BY p.familia_processo
            ORDER BY economia_liquida_mes DESC
            """,
            tuple(params),
        )
