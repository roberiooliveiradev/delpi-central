from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from si_app.application.dto.transforma_mais.process_summary_response import (
    MonthlySummaryItem,
    ProcessSummaryResponse,
    RangeSummary,
)
from si_app.application.dto.transforma_mais.raw_data import TransformaMaisRawData
from si_app.domain.entities.transforma_mais.process import Process


@dataclass(frozen=True)
class CalculationContext:
    processos_by_id: Dict[str, dict]
    revisoes_by_processo: Dict[str, List[dict]]
    medicoes_by_revisao: Dict[str, dict]
    investimentos_by_revisao: Dict[str, List[dict]]
    recursos_by_id: Dict[str, dict]
    vinculos_by_revisao: Dict[str, List[dict]]


class ProcessSummaryCalculator:
    COMPARABLE_SCENARIOS = {"melhoria", "automacao", "correcao"}

    def build_process_list(self, raw: TransformaMaisRawData) -> List[Process]:
        context = self._build_context(raw)
        items: List[Process] = []

        for process_row in raw.processos:
            process_id = self._empty_to_none(process_row.get("processo_id"))
            if not process_id:
                continue

            revisoes = context.revisoes_by_processo.get(process_id, [])
            display_review = self._pick_display_review(revisoes)
            baseline_review = self._pick_baseline_review(revisoes)

            daily_savings = self._calculate_process_daily_savings(
                display_review=display_review,
                baseline_review=baseline_review,
                context=context,
            )

            payback_months = self._calculate_review_payback_months(
                review=display_review,
                baseline_review=baseline_review,
                context=context,
            )

            implementation_date = None
            if display_review:
                implementation_date = self._format_display_date(
                    display_review.get("data_implantacao")
                    or display_review.get("data_inicio_vigencia")
                )

            items.append(
                Process(
                    id=process_id,
                    name_process=self._empty_to_none(process_row.get("nome_processo")) or "",
                    filial_id=self._empty_to_none(process_row.get("filial_id")),
                    sector_name=self._empty_to_none(process_row.get("setor_id")),
                    daily_savings=self._round_final(daily_savings),
                    payback_months=self._round_final(payback_months),
                    status=self._empty_to_none(process_row.get("status_processo")),
                    implementetion_date=implementation_date,
                )
            )

        return items

    def build_summary(
        self,
        raw: TransformaMaisRawData,
        filial_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> ProcessSummaryResponse:
        filtered_raw = self._filter_raw_by_filial(raw=raw, filial_id=filial_id)
        context = self._build_context(filtered_raw)

        monthly_breakdown, calculation_rows = self._calculate_monthly_series(
            context=context,
            start_date=start_date,
            end_date=end_date,
        )

        implemented_solutions_count = len(
            {
                row["review_id"]
                for row in calculation_rows
                if row["scenario_type"] in self.COMPARABLE_SCENARIOS
            }
        )

        total_net_savings_until_now = sum(item.net_savings_month for item in monthly_breakdown)
        total_hours_saved_until_now = sum(row["hours_saved_month"] for row in calculation_rows)
        total_gross_costs_until_now = sum(row["gross_costs_month"] for row in calculation_rows)
        total_gross_savings_in_period = sum(
            item.gross_savings_month for item in monthly_breakdown
        )
        average_roi = self._calculate_average_roi(calculation_rows)

        range_summary = self._build_range_summary(
            start_date=start_date,
            end_date=end_date,
            monthly_breakdown=monthly_breakdown,
        )

        return ProcessSummaryResponse(
            implemented_solutions_count=implemented_solutions_count,
            total_net_savings_until_now=self._round_final(total_net_savings_until_now),
            total_hours_saved_until_now=self._round_final(total_hours_saved_until_now),
            total_gross_costs_until_now=self._round_final(total_gross_costs_until_now),
            total_gross_savings_in_period=self._round_final(total_gross_savings_in_period),
            average_roi=self._round_final(average_roi),
            monthly_breakdown=monthly_breakdown,
            range_summary=range_summary,
        )

    def _filter_raw_by_filial(
        self,
        raw: TransformaMaisRawData,
        filial_id: Optional[str],
    ) -> TransformaMaisRawData:
        filial = self._empty_to_none(filial_id)
        if not filial:
            return raw

        processos_filtrados = [
            processo
            for processo in raw.processos
            if (self._empty_to_none(processo.get("filial_id")) or "").lower() == filial.lower()
        ]

        processo_ids = {
            self._empty_to_none(processo.get("processo_id"))
            for processo in processos_filtrados
            if self._empty_to_none(processo.get("processo_id"))
        }

        revisoes_filtradas = [
            revisao
            for revisao in raw.revisoes
            if self._empty_to_none(revisao.get("processo_id")) in processo_ids
        ]

        revisao_ids = {
            self._empty_to_none(revisao.get("revisao_id"))
            for revisao in revisoes_filtradas
            if self._empty_to_none(revisao.get("revisao_id"))
        }

        medicoes_filtradas = [
            medicao
            for medicao in raw.medicoes
            if self._empty_to_none(medicao.get("revisao_id")) in revisao_ids
        ]

        investimentos_filtrados = [
            investimento
            for investimento in raw.investimentos
            if self._empty_to_none(investimento.get("revisao_id")) in revisao_ids
        ]

        vinculos_filtrados = [
            vinculo
            for vinculo in raw.revisao_recursos_compartilhados
            if self._empty_to_none(vinculo.get("revisao_id")) in revisao_ids
        ]

        recurso_ids = {
            self._empty_to_none(vinculo.get("recurso_compartilhado_id"))
            for vinculo in vinculos_filtrados
            if self._empty_to_none(vinculo.get("recurso_compartilhado_id"))
        }

        recursos_filtrados = [
            recurso
            for recurso in raw.recursos_compartilhados
            if self._empty_to_none(recurso.get("recurso_compartilhado_id")) in recurso_ids
        ]

        return TransformaMaisRawData(
            processos=processos_filtrados,
            revisoes=revisoes_filtradas,
            medicoes=medicoes_filtradas,
            investimentos=investimentos_filtrados,
            recursos_compartilhados=recursos_filtrados,
            revisao_recursos_compartilhados=vinculos_filtrados,
        )

    def _build_context(self, raw: TransformaMaisRawData) -> CalculationContext:
        return CalculationContext(
            processos_by_id=self._index_by(raw.processos, "processo_id"),
            revisoes_by_processo=self._group_by(raw.revisoes, "processo_id"),
            medicoes_by_revisao=self._group_first_by(raw.medicoes, "revisao_id"),
            investimentos_by_revisao=self._group_by(raw.investimentos, "revisao_id"),
            recursos_by_id=self._index_by(raw.recursos_compartilhados, "recurso_compartilhado_id"),
            vinculos_by_revisao=self._group_by(raw.revisao_recursos_compartilhados, "revisao_id"),
        )

    def _calculate_monthly_series(
        self,
        context: CalculationContext,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> tuple[List[MonthlySummaryItem], List[dict]]:
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

        monthly_items: List[MonthlySummaryItem] = []
        calculation_rows: List[dict] = []

        cursor = start_month
        while cursor <= end_month:
            gross_savings_month = 0.0
            gross_costs_month = 0.0
            gross_investment_month = 0.0
            gross_recurring_investment_month = 0.0
            shared_resource_cost_month = 0.0
            net_savings_month = 0.0

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

                for review in selected_reviews:
                    if not self._is_comparable_review(review):
                        continue

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

                    gross_savings_month += row["gross_savings_month"]
                    gross_costs_month += row["gross_costs_month"]
                    gross_investment_month += row["gross_investment_month"]
                    gross_recurring_investment_month += row["gross_recurring_investment_month"]
                    shared_resource_cost_month += row["shared_resource_cost_month"]
                    net_savings_month += row["net_savings_month"]
                    calculation_rows.append(row)

            monthly_items.append(
                MonthlySummaryItem(
                    month=cursor.strftime("%Y-%m"),
                    gross_savings_month=self._round_final(gross_savings_month),
                    gross_costs_month=self._round_final(gross_costs_month),
                    gross_investment_month=self._round_final(gross_investment_month),
                    gross_recurring_investment_month=self._round_final(gross_recurring_investment_month),
                    shared_resource_cost_month=self._round_final(shared_resource_cost_month),
                    net_savings_month=self._round_final(net_savings_month),
                )
            )
            cursor = self._next_month(cursor)

        return monthly_items, calculation_rows

    def _calculate_review_month_result(
        self,
        process_row: dict,
        review: dict,
        baseline_review: dict,
        baseline_measurement: dict,
        context: CalculationContext,
        competencia_date: date,
    ) -> Optional[dict]:
        review_id = self._empty_to_none(review.get("revisao_id"))
        if not review_id:
            return None

        current_measurement = context.medicoes_by_revisao.get(review_id)
        if not current_measurement:
            return None

        baseline_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=baseline_review,
            context=context,
            competencia_date=competencia_date,
        )
        current_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=review,
            context=context,
            competencia_date=competencia_date,
        )

        baseline_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=baseline_measurement,
            shared_resource_cost=baseline_shared_cost,
        )
        current_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=current_measurement,
            shared_resource_cost=current_shared_cost,
        )

        gross_savings_month = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
        )

        gross_investment_month = self._calculate_unique_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=competencia_date,
        )
        gross_recurring_investment_month = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=competencia_date,
        )

        review_shared_resource_cost_month = current_shared_cost

        gross_costs_month = (
            gross_investment_month
            + gross_recurring_investment_month
            + review_shared_resource_cost_month
        )

        net_savings_month = gross_savings_month - gross_costs_month

        hours_saved_month = self._calculate_hours_saved_month(
            baseline_measurement=baseline_measurement,
            current_measurement=current_measurement,
            review=review,
            competencia_date=competencia_date,
        )

        return {
            "competencia": competencia_date.strftime("%Y-%m"),
            "process_id": self._empty_to_none(process_row.get("processo_id")) or "",
            "review_id": review_id,
            "scenario_type": (self._empty_to_none(review.get("cenario_tipo")) or "").lower(),
            "gross_savings_month": gross_savings_month,
            "gross_costs_month": gross_costs_month,
            "gross_investment_month": gross_investment_month,
            "gross_recurring_investment_month": gross_recurring_investment_month,
            "shared_resource_cost_month": review_shared_resource_cost_month,
            "net_savings_month": net_savings_month,
            "hours_saved_month": hours_saved_month,
        }

    def _calculate_process_daily_savings(
        self,
        display_review: Optional[dict],
        baseline_review: Optional[dict],
        context: CalculationContext,
    ) -> Optional[float]:
        if not display_review or not self._is_comparable_review(display_review):
            return None

        review_id = self._empty_to_none(display_review.get("revisao_id"))
        baseline_id = (
            self._empty_to_none(baseline_review.get("revisao_id"))
            if baseline_review
            else None
        )
        if not review_id or not baseline_id:
            return None

        current_measurement = context.medicoes_by_revisao.get(review_id)
        baseline_measurement = context.medicoes_by_revisao.get(baseline_id)
        if not current_measurement or not baseline_measurement:
            return None

        current_month = self._month_start(date.today())

        baseline_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=baseline_review,
            context=context,
            competencia_date=current_month,
        )
        current_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=display_review,
            context=context,
            competencia_date=current_month,
        )

        baseline_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=baseline_measurement,
            shared_resource_cost=baseline_shared_cost,
        )
        current_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=current_measurement,
            shared_resource_cost=current_shared_cost,
        )

        gross_savings_month = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
        )

        gross_recurring_investment_month = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=current_month,
        )

        gross_costs_month = gross_recurring_investment_month + current_shared_cost
        net_savings_month = gross_savings_month - gross_costs_month

        return net_savings_month / 30.0

    def _calculate_review_payback_months(
        self,
        review: Optional[dict],
        baseline_review: Optional[dict],
        context: CalculationContext,
    ) -> Optional[float]:
        if not review or not self._is_comparable_review(review):
            return None

        review_id = self._empty_to_none(review.get("revisao_id"))
        baseline_id = (
            self._empty_to_none(baseline_review.get("revisao_id"))
            if baseline_review
            else None
        )
        if not review_id or not baseline_id:
            return None

        current_measurement = context.medicoes_by_revisao.get(review_id)
        baseline_measurement = context.medicoes_by_revisao.get(baseline_id)
        if not current_measurement or not baseline_measurement:
            return None

        total_unique_investment = sum(
            self._to_float(item.get("valor_total")) or 0.0
            for item in context.investimentos_by_revisao.get(review_id, [])
            if not self._is_deleted(item)
            and (self._empty_to_none(item.get("recorrencia")) or "unico").lower() == "unico"
        )
        if total_unique_investment <= 0:
            return None

        current_month = self._month_start(date.today())

        baseline_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=baseline_review,
            context=context,
            competencia_date=current_month,
        )
        current_shared_cost = self._calculate_shared_resource_cost_for_review(
            review=review,
            context=context,
            competencia_date=current_month,
        )

        baseline_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=baseline_measurement,
            shared_resource_cost=baseline_shared_cost,
        )
        current_breakdown = self._calculate_measurement_cost_breakdown(
            measurement=current_measurement,
            shared_resource_cost=current_shared_cost,
        )

        gross_savings_month = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
        )

        gross_recurring_investment_month = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=current_month,
        )

        gross_costs_month = gross_recurring_investment_month + current_shared_cost
        net_savings_month = gross_savings_month - gross_costs_month
        if net_savings_month <= 0:
            return None

        return total_unique_investment / net_savings_month

    def _calculate_average_roi(self, calculation_rows: List[dict]) -> float:
        grouped: Dict[str, dict] = {}

        for row in calculation_rows:
            review_id = row["review_id"]
            grouped.setdefault(
                review_id,
                {
                    "net_savings_accumulated": 0.0,
                    "gross_investment_accumulated": 0.0,
                },
            )
            grouped[review_id]["net_savings_accumulated"] += row["net_savings_month"]
            grouped[review_id]["gross_investment_accumulated"] += row["gross_investment_month"]

        rois: List[float] = []

        for values in grouped.values():
            investment = values["gross_investment_accumulated"]
            if investment <= 0:
                continue

            roi = (values["net_savings_accumulated"] - investment) / investment
            rois.append(roi)

        if not rois:
            return 0.0

        return sum(rois) / len(rois)

    def _calculate_hours_saved_month(
        self,
        baseline_measurement: dict,
        current_measurement: dict,
        review: dict,
        competencia_date: date,
    ) -> float:
        current_time = self._to_float(current_measurement.get("tempo_medio_execucao_min")) or 0.0
        baseline_time = self._to_float(baseline_measurement.get("tempo_medio_execucao_min")) or 0.0
        volume = self._to_float(current_measurement.get("volume_mensal")) or 0.0

        minutes_saved_full_month = (baseline_time - current_time) * volume
        if minutes_saved_full_month <= 0:
            return 0.0

        fraction = self._active_fraction_in_month(review, competencia_date)
        return (minutes_saved_full_month * fraction) / 60.0

    def _calculate_measurement_cost_breakdown(
        self,
        measurement: Optional[dict],
        shared_resource_cost: float = 0.0,
    ) -> dict:
        if measurement is None:
            return {
                "custo_tempo": 0.0,
                "custo_retrabalho": 0.0,
                "custo_erro": 0.0,
                "custo_outros": 0.0,
                "custo_recursos_compartilhados": shared_resource_cost,
                "custo_operacional": shared_resource_cost,
            }

        volume_mensal = self._to_float(measurement.get("volume_mensal")) or 0.0
        tempo_medio_execucao_min = self._to_float(measurement.get("tempo_medio_execucao_min")) or 0.0
        tempo_retrabalho_min = self._to_float(measurement.get("tempo_retrabalho_min")) or 0.0
        percentual_retrabalho = self._to_float(measurement.get("percentual_retrabalho")) or 0.0
        quantidade_erros_mes = self._to_float(measurement.get("quantidade_erros_mes")) or 0.0
        custo_hora_mao_obra = self._to_float(measurement.get("custo_hora_mao_obra")) or 0.0
        custo_unitario_erro = self._to_float(measurement.get("custo_unitario_erro")) or 0.0
        custo_unitario_retrabalho = self._to_float(measurement.get("custo_unitario_retrabalho")) or 0.0
        custo_outros_desperdicios = self._to_float(measurement.get("custo_outros_desperdicios")) or 0.0

        custo_tempo = volume_mensal * (tempo_medio_execucao_min / 60.0) * custo_hora_mao_obra

        if custo_unitario_retrabalho > 0:
            custo_retrabalho = volume_mensal * percentual_retrabalho * custo_unitario_retrabalho
        else:
            custo_retrabalho = (
                volume_mensal
                * percentual_retrabalho
                * (tempo_retrabalho_min / 60.0)
                * custo_hora_mao_obra
            )

        custo_erro = quantidade_erros_mes * custo_unitario_erro if custo_unitario_erro > 0 else 0.0
        custo_outros = custo_outros_desperdicios
        custo_recursos_compartilhados = shared_resource_cost

        custo_operacional = (
            custo_tempo
            + custo_retrabalho
            + custo_erro
            + custo_outros
            + custo_recursos_compartilhados
        )

        return {
            "custo_tempo": custo_tempo,
            "custo_retrabalho": custo_retrabalho,
            "custo_erro": custo_erro,
            "custo_outros": custo_outros,
            "custo_recursos_compartilhados": custo_recursos_compartilhados,
            "custo_operacional": custo_operacional,
        }

    def _calculate_gross_savings_from_breakdown(
        self,
        baseline_breakdown: dict,
        current_breakdown: dict,
    ) -> float:
        savings_time = baseline_breakdown["custo_tempo"] - current_breakdown["custo_tempo"]
        savings_rework = baseline_breakdown["custo_retrabalho"] - current_breakdown["custo_retrabalho"]
        savings_errors = baseline_breakdown["custo_erro"] - current_breakdown["custo_erro"]
        savings_other = baseline_breakdown["custo_outros"] - current_breakdown["custo_outros"]

        return (
            savings_time
            + savings_rework
            + savings_errors
            + savings_other
        )

    def _calculate_shared_resource_cost_for_review(
        self,
        review: Optional[dict],
        context: CalculationContext,
        competencia_date: date,
    ) -> float:
        if not review:
            return 0.0

        review_id = self._empty_to_none(review.get("revisao_id"))
        if not review_id:
            return 0.0

        total = 0.0
        current_links = context.vinculos_by_revisao.get(review_id, [])

        for link in current_links:
            if not self._is_link_eligible(link, competencia_date):
                continue

            resource_id = self._empty_to_none(link.get("recurso_compartilhado_id"))
            resource = context.recursos_by_id.get(resource_id or "")
            if not resource or not self._is_resource_eligible(resource, competencia_date):
                continue

            total_value = self._to_float(resource.get("valor_total_recorrente")) or 0.0
            allocation_criteria = (self._empty_to_none(resource.get("criterio_rateio")) or "igualitario").lower()

            eligible_links = self._get_eligible_links_for_resource(
                resource_id=resource_id or "",
                vinculos_by_revisao=context.vinculos_by_revisao,
                competencia_date=competencia_date,
            )

            if not eligible_links:
                continue

            if allocation_criteria == "por_peso":
                total_weight = sum(
                    (self._to_float(item.get("peso_rateio")) or 1.0)
                    for item in eligible_links
                )
                current_weight = self._to_float(link.get("peso_rateio")) or 1.0
                if total_weight > 0:
                    total += total_value * (current_weight / total_weight)
                continue

            if allocation_criteria == "por_revisoes_ativas":
                eligible_review_ids = {
                    self._empty_to_none(item.get("revisao_id"))
                    for item in eligible_links
                    if self._empty_to_none(item.get("revisao_id"))
                }
                divisor = max(len(eligible_review_ids), 1)
                total += total_value / divisor
                continue

            total += total_value / max(len(eligible_links), 1)

        return total

    def _get_eligible_links_for_resource(
        self,
        resource_id: str,
        vinculos_by_revisao: Dict[str, List[dict]],
        competencia_date: date,
    ) -> List[dict]:
        result: List[dict] = []

        for review_links in vinculos_by_revisao.values():
            for link in review_links:
                if self._empty_to_none(link.get("recurso_compartilhado_id")) != resource_id:
                    continue
                if self._is_link_eligible(link, competencia_date):
                    result.append(link)

        return result

    def _calculate_recurring_investment_month(
        self,
        investments: List[dict],
        competencia_date: date,
    ) -> float:
        total = 0.0

        for item in investments:
            if self._is_deleted(item):
                continue

            recurrence = (self._empty_to_none(item.get("recorrencia")) or "").lower()
            if recurrence not in {"mensal", "anual"}:
                continue

            if not self._is_investment_active_in_month(item, competencia_date):
                continue

            value = self._to_float(item.get("valor_total")) or 0.0

            if recurrence == "mensal":
                total += value
            elif recurrence == "trimestral":
                total += value / 3.0
            elif recurrence == "semestral":
                total += value / 6.0
            elif recurrence == "anual":
                total += value / 12.0

        return total

    def _calculate_unique_investment_month(
        self,
        investments: List[dict],
        competencia_date: date,
    ) -> float:
        total = 0.0
        current_month = self._month_start(competencia_date)

        for item in investments:
            if self._is_deleted(item):
                continue

            recurrence = (self._empty_to_none(item.get("recorrencia")) or "unico").lower()
            if recurrence != "unico":
                continue

            investment_date = self._parse_date(item.get("data_investimento"))
            if investment_date is None:
                continue

            if self._month_start(investment_date) != current_month:
                continue

            total += self._to_float(item.get("valor_total")) or 0.0

        return total

    def _pick_display_review(self, reviews: List[dict]) -> Optional[dict]:
        if not reviews:
            return None

        active_comparable = [
            review for review in reviews
            if self._is_comparable_review(review) and self._is_true(review.get("revisao_ativa"))
        ]
        if active_comparable:
            return self._sort_reviews(active_comparable)[-1]

        comparable = [review for review in reviews if self._is_comparable_review(review)]
        if comparable:
            return self._sort_reviews(comparable)[-1]

        active_baseline = [
            review for review in reviews
            if (self._empty_to_none(review.get("cenario_tipo")) or "").lower() == "baseline"
            and self._is_true(review.get("revisao_ativa"))
        ]
        if active_baseline:
            return self._sort_reviews(active_baseline)[-1]

        return self._sort_reviews(reviews)[-1]

    def _pick_baseline_review(self, reviews: List[dict]) -> Optional[dict]:
        baseline_reviews = [
            review for review in reviews
            if (self._empty_to_none(review.get("cenario_tipo")) or "").lower() == "baseline"
        ]
        if baseline_reviews:
            return self._sort_reviews(baseline_reviews)[0]
        return None

    def _select_reviews_for_month(self, reviews: List[dict], competencia_date: date) -> List[dict]:
        valid_reviews = [
            review for review in reviews
            if self._is_review_valid_for_month(review, competencia_date)
        ]

        active_reviews = [
            review for review in valid_reviews
            if self._is_true(review.get("revisao_ativa"))
        ]

        if active_reviews:
            return active_reviews

        return valid_reviews

    def _is_review_valid_for_month(self, review: dict, competencia_date: date) -> bool:
        if self._is_deleted(review):
            return False

        start_date = (
            self._parse_date(review.get("data_inicio_vigencia"))
            or self._parse_date(review.get("data_implantacao"))
        )
        end_date = self._parse_date(review.get("data_fim_vigencia"))

        if start_date is None:
            return False

        current_month = self._month_start(competencia_date)
        start_month = self._month_start(start_date)

        if current_month < start_month:
            return False

        if end_date is not None and current_month > self._month_start(end_date):
            return False

        return True

    def _determine_timeline_start(
        self,
        processos_by_id: Dict[str, dict],
        revisoes_by_processo: Dict[str, List[dict]],
    ) -> Optional[date]:
        candidates: List[date] = []

        for process_id in processos_by_id.keys():
            for review in revisoes_by_processo.get(process_id, []):
                if not self._is_comparable_review(review):
                    continue

                start_date = self._parse_date(review.get("data_inicio_vigencia"))
                implementation_date = self._parse_date(review.get("data_implantacao"))

                if start_date:
                    candidates.append(start_date)
                elif implementation_date:
                    candidates.append(implementation_date)

        return min(candidates) if candidates else None

    def _build_range_summary(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        monthly_breakdown: List[MonthlySummaryItem],
    ) -> RangeSummary:
        if not start_date and not end_date:
            accumulated = sum(item.net_savings_month for item in monthly_breakdown)
            return RangeSummary(
                start_date=None,
                end_date=None,
                accumulated_net_savings_until_now=self._round_final(accumulated),
            )

        start_month = self._month_start(self._parse_date(start_date)) if start_date else None
        end_month = self._month_start(self._parse_date(end_date)) if end_date else None

        accumulated = 0.0

        for item in monthly_breakdown:
            month_date = datetime.strptime(item.month, "%Y-%m").date()

            if start_month and month_date < start_month:
                continue
            if end_month and month_date > end_month:
                continue

            accumulated += item.net_savings_month

        return RangeSummary(
            start_date=start_date,
            end_date=end_date,
            accumulated_net_savings_until_now=self._round_final(accumulated),
        )

    def _sort_reviews(self, reviews: List[dict]) -> List[dict]:
        def sort_key(item: dict) -> Tuple[date, date, str]:
            updated_at = self._parse_date(item.get("updated_at")) or date.min
            start_date = self._parse_date(item.get("data_inicio_vigencia")) or date.min
            version = self._empty_to_none(item.get("versao_revisao")) or ""
            return (updated_at, start_date, version)

        return sorted(reviews, key=sort_key)

    def _active_fraction_in_month(self, review: dict, month_date: date) -> float:
        start_date = (
            self._parse_date(review.get("data_inicio_vigencia"))
            or self._parse_date(review.get("data_implantacao"))
        )
        end_date = self._parse_date(review.get("data_fim_vigencia")) or date.today()

        if start_date is None:
            return 0.0

        year = month_date.year
        month = month_date.month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        effective_start = max(first_day, start_date)
        effective_end = min(last_day, end_date)

        if effective_end < effective_start:
            return 0.0

        active_days = (effective_end - effective_start).days + 1
        total_days = (last_day - first_day).days + 1

        return active_days / total_days

    def _is_link_eligible(self, link: dict, competencia_date: date) -> bool:
        if self._is_deleted(link):
            return False

        if not self._is_true(link.get("ativo")):
            return False

        start_date = self._parse_date(link.get("data_inicio_uso"))
        end_date = self._parse_date(link.get("data_fim_uso"))

        return self._is_date_in_optional_range(competencia_date, start_date, end_date)

    def _is_resource_eligible(self, resource: dict, competencia_date: date) -> bool:
        if self._is_deleted(resource):
            return False

        status = (self._empty_to_none(resource.get("status_recurso")) or "").lower()
        if status != "ativo":
            return False

        start_date = self._parse_date(resource.get("data_inicio_vigencia"))
        end_date = self._parse_date(resource.get("data_fim_vigencia"))

        return self._is_date_in_optional_range(competencia_date, start_date, end_date)

    def _is_date_in_optional_range(
        self,
        competencia_date: date,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> bool:
        month_value = self._month_start(competencia_date)

        if start_date and month_value < self._month_start(start_date):
            return False

        if end_date and month_value > self._month_start(end_date):
            return False

        return True

    def _is_investment_active_in_month(self, item: dict, competencia_date: date) -> bool:
        if self._is_deleted(item):
            return False

        investment_date = self._parse_date(item.get("data_investimento"))
        if investment_date is None:
            return False

        recurrence = (self._empty_to_none(item.get("recorrencia")) or "unico").lower()
        current_month = self._month_start(competencia_date)
        start_month = self._month_start(investment_date)

        if recurrence == "unico":
            return current_month == start_month

        if current_month < start_month:
            return False

        meses_vigencia = self._to_int(item.get("meses_vigencia"))
        if meses_vigencia is None or meses_vigencia <= 0:
            return True

        end_month = self._add_months(start_month, meses_vigencia - 1)
        return current_month <= end_month

    def _is_comparable_review(self, review: dict) -> bool:
        cenario_tipo = (self._empty_to_none(review.get("cenario_tipo")) or "").lower()
        return cenario_tipo in self.COMPARABLE_SCENARIOS

    def _is_deleted(self, row: dict) -> bool:
        deleted = self._empty_to_none(row.get("deletado"))
        return (deleted or "").upper() == "TRUE"

    def _group_by(self, rows: List[dict], key: str) -> Dict[str, List[dict]]:
        result: Dict[str, List[dict]] = {}
        for row in rows:
            value = self._empty_to_none(row.get(key))
            if not value:
                continue
            result.setdefault(value, []).append(row)
        return result

    def _group_first_by(self, rows: List[dict], key: str) -> Dict[str, dict]:
        result: Dict[str, dict] = {}
        for row in rows:
            value = self._empty_to_none(row.get(key))
            if not value:
                continue
            if value not in result:
                result[value] = row
        return result

    def _index_by(self, rows: List[dict], key: str) -> Dict[str, dict]:
        result: Dict[str, dict] = {}
        for row in rows:
            value = self._empty_to_none(row.get(key))
            if not value:
                continue
            result[value] = row
        return result

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        if value is None:
            return None

        raw = str(value).strip()
        if not raw:
            return None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(raw, fmt).date()
                if fmt == "%Y-%m":
                    return parsed.replace(day=1)
                return parsed
            except ValueError:
                continue

        return None

    def _format_display_date(self, value: Optional[str]) -> Optional[str]:
        parsed = self._parse_date(value)
        if not parsed:
            return None
        return parsed.strftime("%d/%m/%Y")

    def _month_start(self, value: date) -> date:
        return value.replace(day=1)

    def _next_month(self, value: date) -> date:
        if value.month == 12:
            return date(value.year + 1, 1, 1)
        return date(value.year, value.month + 1, 1)

    def _add_months(self, value: date, months: int) -> date:
        year = value.year + ((value.month - 1 + months) // 12)
        month = ((value.month - 1 + months) % 12) + 1
        return date(year, month, 1)

    def _to_float(self, value) -> Optional[float]:
        if value is None or str(value).strip() == "":
            return None

        raw = str(value).strip()
        raw = raw.replace("R$", "").replace("%", "").replace(" ", "")

        if raw in {"-", "—"}:
            return None

        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")

        try:
            return float(raw)
        except ValueError:
            return None

    def _to_int(self, value) -> Optional[int]:
        number = self._to_float(value)
        if number is None:
            return None
        return int(number)

    def _is_true(self, value) -> bool:
        raw = (self._empty_to_none(value) or "").strip().lower()
        return raw in {"true", "1", "sim", "yes"}

    def _empty_to_none(self, value) -> Optional[str]:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _round_final(self, value: Optional[float], places: int = 2) -> Optional[float]:
        if value is None:
            return None
        return round(value, places)