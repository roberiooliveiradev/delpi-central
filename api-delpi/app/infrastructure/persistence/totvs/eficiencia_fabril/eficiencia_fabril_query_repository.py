from __future__ import annotations

from datetime import date
from typing import Any, Tuple

from app.application.dto.eficiencia_fabril.eficiencia_fabril_dashboard_response import (
    EficienciaFabrilCharts,
    EficienciaFabrilDashboardItem,
    EficienciaFabrilDashboardResponse,
    EficienciaFabrilPagination,
    EficienciaFabrilSummary,
)
from app.application.dto.eficiencia_fabril.get_eficiencia_fabril_dashboard_request import (
    GetEficienciaFabrilDashboardRequest,
)
from app.domain.ports.eficiencia_fabril.eficiencia_fabril_query_repository_port import (
    EficienciaFabrilQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.eficiencia_fabril.eficiencia_fabril_query_settings import (
    EficienciaFabrilQuerySettings,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class EficienciaFabrilQueryRepository(BaseRepository, EficienciaFabrilQueryRepositoryPort):

    def __init__(self, settings: EficienciaFabrilQuerySettings | None = None):
        super().__init__()
        self.settings = settings or EficienciaFabrilQuerySettings()

    def get_dashboard(
        self,
        request: GetEficienciaFabrilDashboardRequest,
    ) -> EficienciaFabrilDashboardResponse:
        # Regra de sanidade:
        # - registros com eficiência acima do limite NÃO entram em cálculos (eficiência/MOD/horas)
        # - mas devem continuar aparecendo na tabela para conferência do líder
        base_where, base_params = self._build_filters(
            request,
            status_ok_only=None,
            efficiency_cap_pct=self.settings.max_efficiency_indicator_pct,
        )
        items_where, items_params = self._build_filters(
            request,
            status_ok_only=request.status_ok_only,
            efficiency_cap_pct=None,
        )

        view = self.settings.view_name
        offset = (request.page - 1) * request.page_size

        with self:
            summary_row = self.execute_one(
                f"""
                SELECT
                    COUNT(*) AS appointment_count,
                    ROUND(AVG(EFICIENCIA_PERCENTUAL), 2) AS weighted_efficiency_pct,
                    ROUND(SUM(RESULTADO_MOD), 2) AS total_mod_result,
                    ROUND(SUM(LUCRO_MOD), 2) AS total_mod_profit,
                    ROUND(SUM(PREJUIZO_MOD), 2) AS total_mod_loss,
                    ROUND(SUM(TEMPO_GANHO_PERDIDO_HORAS), 6) AS total_hours_gained_lost
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO = ?
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            invalid_row = self.execute_one(
                f"""
                SELECT COUNT(*) AS invalid_record_count
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO <> ?
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            efficiency_by_day = self.execute_query(
                f"""
                SELECT
                    DATA_PRODUCAO AS [date],
                    ROUND(AVG(EFICIENCIA_PERCENTUAL), 2) AS efficiency_pct,
                    COUNT(*) AS appointment_count
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO = ?
                GROUP BY DATA_PRODUCAO
                ORDER BY DATA_PRODUCAO
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            mod_result_by_day = self.execute_query(
                f"""
                SELECT
                    DATA_PRODUCAO AS [date],
                    ROUND(SUM(LUCRO_MOD), 2) AS profit,
                    ROUND(SUM(PREJUIZO_MOD), 2) AS loss,
                    ROUND(SUM(RESULTADO_MOD), 2) AS net_result
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO = ?
                GROUP BY DATA_PRODUCAO
                ORDER BY DATA_PRODUCAO
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            efficiency_by_operator = self.execute_query(
                f"""
                SELECT TOP {self.settings.top_operators_limit}
                    NOME_OPERADOR AS operator_name,
                    COD_OPERADOR AS operator_code,
                    LOGIN_OPERADOR AS operator_login,
                    ROUND(AVG(EFICIENCIA_PERCENTUAL), 2) AS efficiency_pct,
                    COUNT(*) AS appointment_count,
                    ROUND(SUM(RESULTADO_MOD), 2) AS mod_result
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO = ?
                GROUP BY NOME_OPERADOR, COD_OPERADOR, LOGIN_OPERADOR
                ORDER BY COUNT(*) DESC, NOME_OPERADOR
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            hours_by_work_center = self.execute_query(
                f"""
                SELECT TOP {self.settings.top_work_centers_limit}
                    CENTRO_TRABALHO AS work_center,
                    ROUND(SUM(TEMPO_REAL_HORAS), 4) AS real_hours,
                    ROUND(SUM(TEMPO_PREVISTO_HORAS), 4) AS planned_hours,
                    COUNT(*) AS appointment_count
                FROM {view}
                WHERE {base_where}
                  AND STATUS_REGISTRO = ?
                GROUP BY CENTRO_TRABALHO
                ORDER BY SUM(TEMPO_REAL_HORAS) DESC, CENTRO_TRABALHO
                """,
                base_params + (self.settings.status_registro_ok,),
            )

            total_items = int(
                self.execute_scalar(
                    f"""
                    SELECT COUNT(*)
                    FROM {view}
                    WHERE {items_where}
                    """,
                    items_params,
                )
                or 0
            )

            item_rows = self.execute_query(
                f"""
                SELECT
                    FILIAL,
                    OP,
                    PRODUTO,
                    CENTRO_TRABALHO,
                    OPERACAO,
                    COD_OPERADOR,
                    LOGIN_OPERADOR,
                    NOME_OPERADOR,
                    DATA_PRODUCAO,
                    HORA_INICIO,
                    HORA_FINAL,
                    QTD_APONTADA,
                    TEMPO_REAL_HORAS,
                    TEMPO_PREVISTO_HORAS,
                    EFICIENCIA_PERCENTUAL,
                    VALOR_MOD_HORA,
                    TEMPO_GANHO_PERDIDO_HORAS,
                    RESULTADO_MOD,
                    LUCRO_MOD,
                    PREJUIZO_MOD,
                    STATUS_RESULTADO_MOD,
                    STATUS_REGISTRO
                FROM {view}
                WHERE {items_where}
                ORDER BY
                    DATA_PRODUCAO DESC,
                    HORA_INICIO DESC,
                    HORA_FINAL DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """,
                items_params + (offset, request.page_size),
            )

        summary = self._map_summary(summary_row, invalid_row)
        items = [self._map_item(row) for row in item_rows]

        return EficienciaFabrilDashboardResponse(
            summary=summary,
            charts=EficienciaFabrilCharts(
                efficiency_by_day=self._serialize_chart_rows(efficiency_by_day),
                mod_result_by_day=self._serialize_chart_rows(mod_result_by_day),
                efficiency_by_operator=self._serialize_chart_rows(efficiency_by_operator),
                hours_by_work_center=self._serialize_chart_rows(hours_by_work_center),
            ),
            items=items,
            pagination=EficienciaFabrilPagination(
                page=request.page,
                page_size=request.page_size,
                total=total_items,
            ),
        )

    def get_appointments(
        self,
        request: GetEficienciaFabrilDashboardRequest,
        *,
        status_ok_only: bool,
    ) -> list[EficienciaFabrilDashboardItem]:
        where, params = self._build_filters(
            request,
            status_ok_only=status_ok_only,
            efficiency_cap_pct=None,
        )

        view = self.settings.view_name
        with self:
            rows = self.execute_query(
                f"""
                SELECT
                    FILIAL,
                    OP,
                    PRODUTO,
                    CENTRO_TRABALHO,
                    OPERACAO,
                    COD_OPERADOR,
                    LOGIN_OPERADOR,
                    NOME_OPERADOR,
                    DATA_PRODUCAO,
                    HORA_INICIO,
                    HORA_FINAL,
                    QTD_APONTADA,
                    TEMPO_REAL_HORAS,
                    TEMPO_PREVISTO_HORAS,
                    EFICIENCIA_PERCENTUAL,
                    VALOR_MOD_HORA,
                    TEMPO_GANHO_PERDIDO_HORAS,
                    RESULTADO_MOD,
                    LUCRO_MOD,
                    PREJUIZO_MOD,
                    STATUS_RESULTADO_MOD,
                    STATUS_REGISTRO
                FROM {view}
                WHERE {where}
                ORDER BY
                    DATA_PRODUCAO DESC,
                    HORA_INICIO DESC,
                    HORA_FINAL DESC
                """,
                params,
            )

        return [self._map_item(row) for row in rows]

    def _build_filters(
        self,
        request: GetEficienciaFabrilDashboardRequest,
        *,
        status_ok_only: bool | None,
        efficiency_cap_pct: int | None = None,
    ) -> Tuple[str, tuple]:
        qb = QueryBuilder()
        qb.gte("DATA_PRODUCAO", request.date_start.isoformat())
        qb.lte("DATA_PRODUCAO", request.date_end.isoformat())

        if request.branch:
            qb.eq("FILIAL", request.branch)
        else:
            qb.in_list("FILIAL", self.settings.branches)

        qb.raw("LTRIM(RTRIM(ISNULL(FILIAL, ''))) <> ''")

        excluded_work_centers = ("CT-00", "CT-70", "CT-16A", "CT-99")

        if request.op:
            # Busca parcial (contains) por número de OP.
            # Ex.: "24546" deve retornar "24546401001", "24546401005", ...
            qb.like("OP", request.op)

        if request.work_center:
            work_center = request.work_center.strip()
            if work_center in excluded_work_centers:
                qb.raw("1=0")
            else:
                qb.eq("CENTRO_TRABALHO", work_center)
        else:
            # TOTVS pode retornar CENTRO_TRABALHO com espaços à direita
            for wc in excluded_work_centers:
                qb.raw("LTRIM(RTRIM(CENTRO_TRABALHO)) <> ?")
                qb._params.append(wc)

        if request.employee:
            # Busca por nome do operador (contains)
            qb.like("NOME_OPERADOR", request.employee, case_insensitive=True)

        if efficiency_cap_pct is not None:
            # Sanidade: eficiência muito alta é erro de apontamento.
            # Importante: esse cap deve afetar apenas agregações (summary/charts),
            # mantendo esses registros visíveis na tabela para conferência.
            qb.raw("(EFICIENCIA_PERCENTUAL IS NULL OR EFICIENCIA_PERCENTUAL <= ?)")
            qb._params.append(efficiency_cap_pct)

        effective_status_ok = (
            request.status_ok_only if status_ok_only is None else status_ok_only
        )
        if effective_status_ok:
            qb.eq("STATUS_REGISTRO", self.settings.status_registro_ok)

        return qb.build()

    @staticmethod
    def _map_summary(
        summary_row: dict | None,
        invalid_row: dict | None,
    ) -> EficienciaFabrilSummary:
        row = summary_row or {}
        invalid_count = int((invalid_row or {}).get("invalid_record_count") or 0)
        return EficienciaFabrilSummary(
            weighted_efficiency_pct=_to_float(row.get("weighted_efficiency_pct")),
            total_mod_result=_to_float(row.get("total_mod_result")),
            total_mod_profit=_to_float(row.get("total_mod_profit")),
            total_mod_loss=_to_float(row.get("total_mod_loss")),
            total_hours_gained_lost=_to_float(row.get("total_hours_gained_lost")),
            appointment_count=int(row.get("appointment_count") or 0),
            invalid_record_count=invalid_count,
        )

    @staticmethod
    def _map_item(row: dict) -> EficienciaFabrilDashboardItem:
        data_producao = row.get("DATA_PRODUCAO")
        if isinstance(data_producao, date):
            data_producao = data_producao.isoformat()

        return EficienciaFabrilDashboardItem(
            filial=row.get("FILIAL"),
            op=row.get("OP"),
            produto=row.get("PRODUTO"),
            centro_trabalho=row.get("CENTRO_TRABALHO"),
            operacao=row.get("OPERACAO"),
            cod_operador=row.get("COD_OPERADOR"),
            login_operador=row.get("LOGIN_OPERADOR"),
            nome_operador=row.get("NOME_OPERADOR"),
            data_producao=data_producao,
            hora_inicio=row.get("HORA_INICIO"),
            hora_final=row.get("HORA_FINAL"),
            qtd_apontada=_to_float(row.get("QTD_APONTADA")),
            tempo_real_horas=_to_float(row.get("TEMPO_REAL_HORAS")),
            tempo_previsto_horas=_to_float(row.get("TEMPO_PREVISTO_HORAS")),
            eficiencia_percentual=_to_float(row.get("EFICIENCIA_PERCENTUAL")),
            valor_mod_hora=_to_float(row.get("VALOR_MOD_HORA")),
            tempo_ganho_perdido_horas=_to_float(row.get("TEMPO_GANHO_PERDIDO_HORAS")),
            resultado_mod=_to_float(row.get("RESULTADO_MOD")),
            lucro_mod=_to_float(row.get("LUCRO_MOD")),
            prejuizo_mod=_to_float(row.get("PREJUIZO_MOD")),
            status_resultado_mod=row.get("STATUS_RESULTADO_MOD"),
            status_registro=row.get("STATUS_REGISTRO"),
        )

    @staticmethod
    def _serialize_chart_rows(rows: list[dict]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {}
            for key, value in row.items():
                if isinstance(value, date):
                    item[key] = value.isoformat()
                else:
                    item[key] = value
            serialized.append(item)
        return serialized


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
