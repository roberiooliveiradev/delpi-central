from __future__ import annotations

from datetime import date
from typing import List, Optional

from tm_app.domain.services.dashboard_calculator import (
    CalculationContext,
    DashboardCalculatorService,
)


def _calculate_monthly_series_historical(
    self: DashboardCalculatorService,
    context: CalculationContext,
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[List[dict], List[dict]]:
    """Calcula historico por vigencia da revisao, nao pelo status ativo atual.

    Uma revisao descontinuada hoje ainda deve gerar linhas nos meses em que ficou
    vigente. O status ``revisao_ativa`` representa a situacao operacional atual,
    mas o dashboard filtrado por periodo precisa respeitar ``data_inicio`` /
    ``data_implantacao`` / ``data_fim_vigencia``.
    """
    timeline_start = self._determine_timeline_start(
        processos_by_id=context.processos_by_id,
        revisoes_by_processo=context.revisoes_by_processo,
    )
    if timeline_start is None:
        return [], []

    start_month = (
        self._month_start(self._parse_date(start_date))
        if start_date
        else self._month_start(timeline_start)
    )
    end_month = (
        self._month_start(self._parse_date(end_date))
        if end_date
        else self._month_start(date.today())
    )

    monthly_items: List[dict] = []
    calculation_rows: List[dict] = []

    cursor = start_month
    while cursor <= end_month:
        economia_bruta_mes = 0.0
        investimento_unico_mes = 0.0
        custo_recorrente_mes = 0.0
        custo_recursos_compartilhados_mes = 0.0
        economia_liquida_mes = 0.0

        for process_id, process_row in context.processos_by_id.items():
            revisoes = context.revisoes_by_processo.get(process_id, [])

            baseline_review = self._pick_baseline_review(revisoes)
            baseline_id = (
                self._empty_to_none(baseline_review.get("revisao_id"))
                if baseline_review
                else None
            )
            baseline_measurement = (
                context.medicoes_by_revisao.get(baseline_id)
                if baseline_id
                else None
            )

            if not baseline_review or not baseline_measurement:
                continue

            selected_reviews = self._select_reviews_for_month(revisoes, cursor)
            if not selected_reviews:
                continue

            for review in selected_reviews:
                row = self._calculate_review_month_result(
                    process_row=process_row,
                    review=review,
                    baseline_review=baseline_review,
                    baseline_measurement=baseline_measurement,
                    context=context,
                    competencia_date=cursor,
                )
                if row is None:
                    continue

                economia_bruta_mes += row["economia_bruta"]
                investimento_unico_mes += row["investimento_unico_mes"]
                custo_recorrente_mes += row["custo_recorrente_mes"]
                custo_recursos_compartilhados_mes += row["custo_recursos_compartilhados_mes"]
                economia_liquida_mes += row["economia_liquida_mes"]
                calculation_rows.append(row)

        monthly_items.append(
            {
                "competencia": cursor.strftime("%Y-%m"),
                "economia_bruta": self._round_final(economia_bruta_mes),
                "investimento_unico_mes": self._round_final(investimento_unico_mes),
                "custo_recorrente_mes": self._round_final(custo_recorrente_mes),
                "investimento_total_mes": self._round_final(
                    investimento_unico_mes
                    + custo_recorrente_mes
                    + custo_recursos_compartilhados_mes
                ),
                "custo_recursos_compartilhados_mes": self._round_final(
                    custo_recursos_compartilhados_mes
                ),
                "economia_liquida_mes": self._round_final(economia_liquida_mes),
            }
        )
        cursor = self._next_month(cursor)

    return monthly_items, calculation_rows


def apply_historical_revision_patch() -> None:
    DashboardCalculatorService._calculate_monthly_series = _calculate_monthly_series_historical
