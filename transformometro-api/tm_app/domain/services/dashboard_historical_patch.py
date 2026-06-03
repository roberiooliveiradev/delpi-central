from __future__ import annotations

from datetime import date
from typing import List, Optional

from tm_app.domain.services.dashboard_calculator import (
    CalculationContext,
    DashboardCalculatorService,
)

_ORIGINAL_MONTH_RESULT = DashboardCalculatorService._calculate_review_month_result


def _calculate_review_month_result_net_after_investments(
    self: DashboardCalculatorService,
    process_row: dict,
    review: dict,
    baseline_review: dict,
    baseline_measurement: dict,
    context: CalculationContext,
    competencia_date: date,
) -> dict | None:
    row = _ORIGINAL_MONTH_RESULT(
        self,
        process_row=process_row,
        review=review,
        baseline_review=baseline_review,
        baseline_measurement=baseline_measurement,
        context=context,
        competencia_date=competencia_date,
    )
    if row is None:
        return None

    investimento_total_mes = (
        float(row.get("investimento_unico_mes") or 0)
        + float(row.get("custo_recorrente_mes") or 0)
        + float(row.get("custo_recursos_compartilhados_mes") or 0)
    )
    row["investimento_total_mes"] = investimento_total_mes
    row["economia_liquida_mes"] = float(row.get("economia_bruta") or 0) - investimento_total_mes
    return row


def _calculate_average_roi_from_net_rows(
    self: DashboardCalculatorService,
    calculation_rows: List[dict],
) -> float:
    """Calcula ROI medio sem descontar investimento duas vezes.

    As linhas calculadas ja trazem ``economia_liquida_mes`` como:

        economia_bruta - investimento_unico - custo_recorrente - recursos

    Portanto o ROI da revisao deve ser a economia liquida acumulada dividida
    pelo investimento total acumulado, e nao ``(liquida - investimento)``.
    """
    grouped: dict[str, dict[str, float]] = {}

    for row in calculation_rows:
        if row.get("cenario_tipo") not in self.COMPARABLE_SCENARIOS:
            continue

        revisao_id = str(row.get("revisao_id") or "")
        if not revisao_id:
            continue

        bucket = grouped.setdefault(
            revisao_id,
            {
                "economia_liquida_acumulada": 0.0,
                "investimento_total_acumulado": 0.0,
            },
        )
        bucket["economia_liquida_acumulada"] += float(row.get("economia_liquida_mes") or 0)
        bucket["investimento_total_acumulado"] += float(row.get("investimento_total_mes") or 0)

    rois: List[float] = []
    for values in grouped.values():
        investment = values["investimento_total_acumulado"]
        if investment <= 0:
            continue
        rois.append(values["economia_liquida_acumulada"] / investment)

    if not rois:
        return 0.0

    return sum(rois) / len(rois)


def _calculate_consolidated_roi_from_net(summary: dict) -> float:
    """ROI consolidado usando liquida ja descontada.

    Mantem a chave publica ``roi_medio`` por compatibilidade com o frontend.
    """
    total_net_savings = float(summary.get("economia_liquida_total") or 0)
    total_investment = float(summary.get("investimento_total") or 0)
    if total_investment <= 0:
        return 0.0
    return total_net_savings / total_investment


def _calculate_monthly_series_historical(
    self: DashboardCalculatorService,
    context: CalculationContext,
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[List[dict], List[dict]]:
    """Calcula historico por vigencia da revisao, nao pelo status ativo atual."""
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
    DashboardCalculatorService._calculate_review_month_result = _calculate_review_month_result_net_after_investments
    DashboardCalculatorService._calculate_monthly_series = _calculate_monthly_series_historical
    DashboardCalculatorService._calculate_average_roi = _calculate_average_roi_from_net_rows

    try:
        from tm_app.application.services.dashboard_live_service import DashboardLiveService

        DashboardLiveService._calculate_consolidated_roi = staticmethod(
            _calculate_consolidated_roi_from_net
        )
    except ImportError:
        # Evita ciclo de importacao quando o patch for carregado antes da camada application.
        pass
