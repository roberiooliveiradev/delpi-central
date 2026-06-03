from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.recurso_custo_resolver import resolve_recurso_valor_mensal


@dataclass(frozen=True)
class CalculationContext:
    processos_by_id: Dict[str, dict]
    revisoes_by_processo: Dict[str, List[dict]]
    medicoes_by_revisao: Dict[str, dict]
    investimentos_by_revisao: Dict[str, List[dict]]
    recursos_by_id: Dict[str, dict]
    vinculos_by_revisao: Dict[str, List[dict]]
    custos_by_recurso: Dict[str, List[dict]]


class DashboardCalculatorService:
    COMPARABLE_SCENARIOS = {"melhoria", "automacao", "correcao"}

    def build_process_list(self, raw: TransformometroRawData) -> List[dict]:
        context = self._build_context(raw)
        items: List[dict] = []

        for process_row in raw.processos:
            process_id = self._empty_to_none(process_row.get("processo_id"))
            if not process_id:
                continue

            revisoes = context.revisoes_by_processo.get(process_id, [])
            process_active = self._is_process_active(revisoes)
            display_review = self._pick_display_review(revisoes) if process_active else None
            implementation_review = self._pick_first_non_baseline_review(revisoes)
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
            if implementation_review:
                implementation_date = self._format_display_date(
                    implementation_review.get("data_implantacao")
                    or implementation_review.get("data_inicio_vigencia")
                )

            items.append(
                {
                    "processo_id": process_id,
                    "codigo_processo": self._empty_to_none(process_row.get("codigo_processo")),
                    "nome_processo": self._empty_to_none(process_row.get("nome_processo")) or "",
                    "filial_id": self._empty_to_none(process_row.get("filial_id")),
                    "setor_id": self._empty_to_none(process_row.get("setor_id")),
                    "economia_diaria": self._round_final(daily_savings),
                    "payback_meses": self._round_final(payback_months),
                    "status_processo": self._empty_to_none(process_row.get("status_processo")),
                    "data_implantacao": implementation_date,
                }
            )

        return items

    def build_dashboard_rows(self, raw: TransformometroRawData) -> List[dict]:
        context = self._build_context(raw)
        _, calculation_rows = self._calculate_monthly_series(
            context=context,
            start_date=None,
            end_date=None,
        )
        return calculation_rows

    def build_summary(
        self,
        raw: TransformometroRawData,
        filial_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> dict:
        filtered_raw = self.filter_raw(raw=raw, filial_id=filial_id)
        context = self._build_context(filtered_raw)

        monthly_breakdown, calculation_rows = self._calculate_monthly_series(
            context=context,
            start_date=start_date,
            end_date=end_date,
        )

        implemented_solutions_count = len(
            {
                row["revisao_id"]
                for row in calculation_rows
                if row["cenario_tipo"] in self.COMPARABLE_SCENARIOS
            }
        )

        # Get base monthly totals (no proration for individual months)
        total_net_savings = sum(item["economia_liquida_mes"] for item in monthly_breakdown)
        total_hours_saved = sum(row["horas_economizadas_mes"] for row in calculation_rows)
        total_gross_savings = sum(item["economia_bruta"] for item in monthly_breakdown)
        total_recurring = sum(item["custo_recorrente_mes"] for item in monthly_breakdown)
        total_unique = sum(item["investimento_unico_mes"] for item in monthly_breakdown)
        total_shared_resources = sum(
            item["custo_recursos_compartilhados_mes"] for item in monthly_breakdown
        )
        total_investment = sum(item["investimento_total_mes"] for item in monthly_breakdown)
        average_roi = self._calculate_average_roi(calculation_rows)

        # Cards principais: competências mensais cheias no recorte (sem fator global de prorrata).
        # Proporcionalidade por dias aplica-se apenas a recursos com base_competencia proporcional_dias.
        proration_factor = 1.0

        range_summary = self._build_range_summary(
            start_date=start_date,
            end_date=end_date,
            monthly_breakdown=monthly_breakdown,
            proration_factor=proration_factor,
        )

        return {
            "solucoes_implementadas": implemented_solutions_count,
            "economia_liquida_total": self._round_final(total_net_savings),
            "economia_bruta_total": self._round_final(total_gross_savings),
            "horas_economizadas_total": self._round_final(total_hours_saved),
            "investimento_unico_total": self._round_final(total_unique),
            "custo_recorrente_total": self._round_final(total_recurring),
            "custo_recursos_compartilhados_total": self._round_final(total_shared_resources),
            "investimento_total": self._round_final(total_investment),
            "roi_medio": self._round_final(average_roi),
            "evolucao_mensal": monthly_breakdown,  # Keep original monthly values
            "periodo": range_summary,
            "_debug": {
                "calculation_rows_count": len(calculation_rows),
                "comparable_rows": len([r for r in calculation_rows if r["cenario_tipo"] in self.COMPARABLE_SCENARIOS]),
                "revisoes_with_investment": len([r for r in calculation_rows if r["investimento_unico_mes"] > 0]),
                "total_investment_acumulated": self._round_final(total_unique),
                "total_economy_acumulated": self._round_final(total_net_savings),
            }
        }

    def filter_raw(
        self,
        raw: TransformometroRawData,
        *,
        filial_id: Optional[str] = None,
        setor_id: Optional[str] = None,
        familia_processo: Optional[str] = None,
    ) -> TransformometroRawData:
        processos_filtrados = list(raw.processos)
        filial = self._empty_to_none(filial_id)
        if filial:
            processos_filtrados = [
                processo
                for processo in processos_filtrados
                if (self._empty_to_none(processo.get("filial_id")) or "").lower() == filial.lower()
            ]
        setor = self._empty_to_none(setor_id)
        if setor:
            processos_filtrados = [
                processo
                for processo in processos_filtrados
                if (self._empty_to_none(processo.get("setor_id")) or "").lower() == setor.lower()
            ]
        familia = self._empty_to_none(familia_processo)
        if familia:
            processos_filtrados = [
                processo
                for processo in processos_filtrados
                if (self._empty_to_none(processo.get("familia_processo")) or "").lower()
                == familia.lower()
            ]

        if not (filial or setor or familia):
            return raw

        return self._narrow_raw_to_processos(raw, processos_filtrados)

    def _filter_raw_by_filial(
        self,
        raw: TransformometroRawData,
        filial_id: Optional[str],
    ) -> TransformometroRawData:
        return self.filter_raw(raw, filial_id=filial_id)

    def _narrow_raw_to_processos(
        self,
        raw: TransformometroRawData,
        processos_filtrados: list[dict],
    ) -> TransformometroRawData:
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

        custos_filtrados = [
            custo
            for custo in raw.recurso_custos
            if self._empty_to_none(custo.get("recurso_compartilhado_id")) in recurso_ids
        ]

        return TransformometroRawData(
            processos=processos_filtrados,
            revisoes=revisoes_filtradas,
            medicoes=medicoes_filtradas,
            investimentos=investimentos_filtrados,
            recursos_compartilhados=recursos_filtrados,
            revisao_recursos_compartilhados=vinculos_filtrados,
            recurso_custos=custos_filtrados,
        )

    def _build_context(self, raw: TransformometroRawData) -> CalculationContext:
        return CalculationContext(
            processos_by_id=self._index_by(raw.processos, "processo_id"),
            revisoes_by_processo=self._group_by(raw.revisoes, "processo_id"),
            medicoes_by_revisao=self._group_first_by(raw.medicoes, "revisao_id"),
            investimentos_by_revisao=self._group_by(raw.investimentos, "revisao_id"),
            recursos_by_id=self._index_by(raw.recursos_compartilhados, "recurso_compartilhado_id"),
            vinculos_by_revisao=self._group_by(raw.revisao_recursos_compartilhados, "revisao_id"),
            custos_by_recurso=self._group_by(raw.recurso_custos, "recurso_compartilhado_id"),
        )

    def _calculate_monthly_series(
        self,
        context: CalculationContext,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> tuple[List[dict], List[dict]]:
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
                        investimento_unico_mes + custo_recorrente_mes + custo_recursos_compartilhados_mes
                    ),
                    "custo_recursos_compartilhados_mes": self._round_final(custo_recursos_compartilhados_mes),
                    "economia_liquida_mes": self._round_final(economia_liquida_mes),
                }
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

        savings = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
            baseline_shared_cost=baseline_shared_cost,
            current_shared_cost=current_shared_cost,
        )

        if not self._is_comparable_review(review):
            savings = {
                "economia_tempo": 0.0,
                "economia_retrabalho": 0.0,
                "economia_erros": 0.0,
                "economia_outros": 0.0,
                "economia_recursos_compartilhados": 0.0,
                "economia_bruta": 0.0,
            }

        investimento_unico_mes = self._calculate_unique_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=competencia_date,
        )
        custo_recorrente_mes = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=competencia_date,
        )

        investimento_total_mes = (
            investimento_unico_mes + custo_recorrente_mes + current_shared_cost
        )
        economia_liquida_mes = savings["economia_bruta"] - investimento_total_mes

        horas_economizadas_mes = 0.0
        if self._is_comparable_review(review):
            horas_economizadas_mes = self._calculate_hours_saved_month(
                baseline_measurement=baseline_measurement,
                current_measurement=current_measurement,
                review=review,
                competencia_date=competencia_date,
            )

        competencia = competencia_date.strftime("%Y-%m")
        processo_id = self._empty_to_none(process_row.get("processo_id")) or ""

        return {
            "dashboard_calculo_id": f"{review_id}::{competencia}",
            "revisao_id": review_id,
            "processo_id": processo_id,
            "competencia": competencia,
            "filial_id": self._empty_to_none(process_row.get("filial_id")),
            "setor_id": self._empty_to_none(process_row.get("setor_id")),
            "cenario_tipo": (self._empty_to_none(review.get("cenario_tipo")) or "").lower(),
            "revisao_ativa": self._is_true(review.get("revisao_ativa")),
            "economia_tempo": savings["economia_tempo"],
            "economia_retrabalho": savings["economia_retrabalho"],
            "economia_erros": savings["economia_erros"],
            "economia_outros": savings["economia_outros"],
            "economia_recursos_compartilhados": savings["economia_recursos_compartilhados"],
            "economia_bruta": savings["economia_bruta"],
            "investimento_unico_mes": investimento_unico_mes,
            "custo_recorrente_mes": custo_recorrente_mes,
            "investimento_total_mes": investimento_total_mes,
            "economia_liquida_mes": economia_liquida_mes,
            "custo_recursos_compartilhados_mes": current_shared_cost,
            "horas_economizadas_mes": horas_economizadas_mes,
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

        savings = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
            baseline_shared_cost=baseline_shared_cost,
            current_shared_cost=current_shared_cost,
        )

        days_in_month = calendar.monthrange(current_month.year, current_month.month)[1]
        if days_in_month <= 0:
            return None

        return savings["economia_bruta"] / days_in_month

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

        savings = self._calculate_gross_savings_from_breakdown(
            baseline_breakdown=baseline_breakdown,
            current_breakdown=current_breakdown,
            baseline_shared_cost=baseline_shared_cost,
            current_shared_cost=current_shared_cost,
        )

        custo_recorrente_mes = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=current_month,
        )

        economia_operacional_mes = (
            savings["economia_bruta"] - custo_recorrente_mes - current_shared_cost
        )
        if economia_operacional_mes <= 0:
            return None

        return total_unique_investment / economia_operacional_mes

    def _calculate_average_roi(self, calculation_rows: List[dict]) -> float:
        """ROI medio por revisao: liquida acumulada / investimento total acumulado."""
        grouped: Dict[str, dict[str, float]] = {}

        for row in calculation_rows:
            if row["cenario_tipo"] not in self.COMPARABLE_SCENARIOS:
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
        baseline_shared_cost: float,
        current_shared_cost: float,
    ) -> dict:
        economia_tempo = max(
            0.0, baseline_breakdown["custo_tempo"] - current_breakdown["custo_tempo"]
        )
        economia_retrabalho = max(
            0.0,
            baseline_breakdown["custo_retrabalho"] - current_breakdown["custo_retrabalho"],
        )
        economia_erros = max(
            0.0, baseline_breakdown["custo_erro"] - current_breakdown["custo_erro"]
        )
        economia_outros = max(
            0.0, baseline_breakdown["custo_outros"] - current_breakdown["custo_outros"]
        )
        economia_recursos = max(0.0, baseline_shared_cost - current_shared_cost)

        economia_bruta = (
            economia_tempo
            + economia_retrabalho
            + economia_erros
            + economia_outros
            + economia_recursos
        )

        return {
            "economia_tempo": economia_tempo,
            "economia_retrabalho": economia_retrabalho,
            "economia_erros": economia_erros,
            "economia_outros": economia_outros,
            "economia_recursos_compartilhados": economia_recursos,
            "economia_bruta": economia_bruta,
        }

    def _resource_link_competence_factor(
        self,
        resource: dict,
        link: dict,
        competencia_date: date,
    ) -> float:
        """Fator de reconhecimento do recurso na competência (mensal cheio ou proporcional)."""
        base_competencia = (
            self._empty_to_none(resource.get("base_competencia")) or "mensal_cheio"
        ).lower()
        if base_competencia != "proporcional_dias":
            return 1.0

        month_start = self._month_start(competencia_date)
        month_end = date(
            month_start.year,
            month_start.month,
            calendar.monthrange(month_start.year, month_start.month)[1],
        )

        start_candidates = [month_start]
        for raw_date in (
            link.get("data_inicio_uso"),
            resource.get("data_inicio_vigencia"),
        ):
            parsed = self._parse_date(raw_date)
            if parsed:
                start_candidates.append(parsed)

        end_candidates = [month_end]
        for raw_date in (
            link.get("data_fim_uso"),
            resource.get("data_fim_vigencia"),
        ):
            parsed = self._parse_date(raw_date)
            if parsed:
                end_candidates.append(parsed)

        effective_start = max(start_candidates)
        effective_end = min(end_candidates)

        if effective_end < effective_start:
            return 0.0

        active_days = (effective_end - effective_start).days + 1
        total_days = (month_end - month_start).days + 1
        if total_days <= 0:
            return 0.0

        return max(0.0, min(1.0, active_days / total_days))

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

            custos = context.custos_by_recurso.get(resource_id or "", [])
            total_value = resolve_recurso_valor_mensal(resource, custos, competencia_date)
            if total_value <= 0:
                continue

            allocation_criteria = (
                self._empty_to_none(resource.get("criterio_rateio")) or "igualitario"
            ).lower()

            eligible_links = self._get_eligible_links_for_resource(
                resource_id=resource_id or "",
                vinculos_by_revisao=context.vinculos_by_revisao,
                competencia_date=competencia_date,
            )

            if not eligible_links:
                continue

            current_factor = self._resource_link_competence_factor(
                resource,
                link,
                competencia_date,
            )
            if current_factor <= 0:
                continue

            if allocation_criteria == "por_peso":
                total_weight = sum(
                    (self._to_float(item.get("peso_rateio")) or 1.0)
                    for item in eligible_links
                )
                current_weight = self._to_float(link.get("peso_rateio")) or 1.0
                if total_weight > 0:
                    total += total_value * (current_weight / total_weight) * current_factor
                continue

            if allocation_criteria == "por_revisoes_ativas":
                eligible_review_ids = {
                    self._empty_to_none(item.get("revisao_id"))
                    for item in eligible_links
                    if self._empty_to_none(item.get("revisao_id"))
                }
                divisor = max(len(eligible_review_ids), 1)
                total += (total_value / divisor) * current_factor
                continue

            total += (total_value / max(len(eligible_links), 1)) * current_factor

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
        """
        Calculate recurring (monthly/annual) investment costs for a specific month.
        
        Recurring costs are divided by their recurrence period:
        - Mensal (monthly): valor_total per month
        - Trimestral (quarterly): valor_total / 3
        - Semestral (semi-annual): valor_total / 6
        - Anual (annual): valor_total / 12
        
        Only includes costs active during the month (within data_investimento + meses_vigencia).
        
        Args:
            investments: List of investment/cost records
            competencia_date: The month to calculate costs for
            
        Returns:
            Total recurring investment cost for the month
        """
        total = 0.0

        for item in investments:
            # Skip deleted or invalid investments
            if self._is_deleted(item):
                continue

            recurrence = (self._empty_to_none(item.get("recorrencia")) or "").lower()
            
            # Only process recurring investments (not one-time)
            if recurrence not in {"mensal", "trimestral", "semestral", "anual"}:
                continue

            # Check if investment is active during this month
            if not self._is_investment_active_in_month(item, competencia_date):
                continue

            value = self._to_float(item.get("valor_total")) or 0.0
            if value <= 0:
                continue

            # Distribute value based on recurrence period
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
        """
        Calculate unique (one-time) investments allocated to a specific month.
        
        A one-time investment is allocated to the month it was made (data_investimento).
        If an investment spans multiple months via "meses_vigencia", it distributes
        across that period.
        
        Args:
            investments: List of investment records
            competencia_date: The month to calculate investments for
            
        Returns:
            Total unique investment value for the month
        """
        total = 0.0
        current_month = self._month_start(competencia_date)

        for item in investments:
            # Skip deleted or invalid investments
            if self._is_deleted(item):
                continue

            recurrence = (self._empty_to_none(item.get("recorrencia")) or "unico").lower()
            if recurrence != "unico":
                continue

            # Get the investment date
            investment_date = self._parse_date(item.get("data_investimento"))
            if investment_date is None:
                continue

            investment_month = self._month_start(investment_date)
            
            # Check if meses_vigencia extends the investment across multiple months
            meses_vigencia = self._to_int(item.get("meses_vigencia"))
            
            # If investment is allocated to only one month
            if meses_vigencia is None or meses_vigencia <= 0:
                # Allocate full investment to the investment month
                if investment_month == current_month:
                    total += self._to_float(item.get("valor_total")) or 0.0
            else:
                # Investment spans multiple months - distribute evenly
                investment_value = self._to_float(item.get("valor_total")) or 0.0
                if investment_value <= 0:
                    continue
                    
                end_month = self._add_months(investment_month, meses_vigencia - 1)
                
                # Check if current month is within the investment period
                if investment_month <= current_month <= end_month:
                    # Distribute investment across vigencia months
                    monthly_allocation = investment_value / max(meses_vigencia, 1)
                    total += monthly_allocation

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
            and not self._is_deleted(review)
        ]
        if baseline_reviews:
            return self._sort_reviews(baseline_reviews)[0]

        active_reviews = [review for review in reviews if not self._is_deleted(review)]
        if not active_reviews:
            return None

        return self._sort_reviews(active_reviews)[0]

    def _pick_first_non_baseline_review(self, reviews: List[dict]) -> Optional[dict]:
        """Return the earliest review that is not a baseline and is not deleted.

        This is used as the project's implementation reference for filtering: if
        there are multiple improvements the first (earliest) non-baseline review
        should be considered the implementation date rather than the latest.
        """
        if not reviews:
            return None

        sorted_reviews = sorted(reviews, key=self._implementation_sort_key)
        for rev in sorted_reviews:
            cenario = (self._empty_to_none(rev.get("cenario_tipo")) or "").lower()
            if cenario != "baseline" and not self._is_deleted(rev):
                return rev

        return None

    def _implementation_sort_key(self, review: dict) -> Tuple[date, date, str]:
        implementation_date = self._review_implementation_date(review) or date.max
        start_date = self._parse_date(review.get("data_inicio_vigencia")) or date.max
        version = self._empty_to_none(review.get("versao_revisao")) or ""
        return (implementation_date, start_date, version)

    def _review_implementation_date(self, review: Optional[dict]) -> Optional[date]:
        if not review:
            return None
        return (
            self._parse_date(review.get("data_implantacao"))
            or self._parse_date(review.get("data_inicio_vigencia"))
        )

    def _select_reviews_for_month(self, reviews: List[dict], competencia_date: date) -> List[dict]:
        valid_reviews = [
            review for review in reviews
            if self._is_comparable_review(review)
            and self._is_review_valid_for_month(review, competencia_date)
        ]

        active_reviews = [
            review for review in valid_reviews
            if self._is_true(review.get("revisao_ativa"))
        ]

        if active_reviews:
            return active_reviews

        return valid_reviews

    def _is_process_active(self, reviews: List[dict]) -> bool:
        return any(
            not self._is_deleted(review) and self._is_true(review.get("revisao_ativa"))
            for review in reviews
        )

    def _is_review_valid_for_month(self, review: dict, competencia_date: date) -> bool:
        if self._is_deleted(review):
            return False

        start_date = self._review_calculation_start_date(review)
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

    def _review_calculation_start_date(self, review: dict) -> Optional[date]:
        start_date = self._parse_date(review.get("data_inicio_vigencia"))
        implementation_date = self._parse_date(review.get("data_implantacao"))

        if not self._is_comparable_review(review):
            return start_date or implementation_date

        if start_date and implementation_date:
            return max(start_date, implementation_date)

        return implementation_date or start_date

    def _determine_timeline_start(
        self,
        processos_by_id: Dict[str, dict],
        revisoes_by_processo: Dict[str, List[dict]],
    ) -> Optional[date]:
        candidates: List[date] = []

        for process_id, process_row in processos_by_id.items():
            created = self._parse_date(process_row.get("created_at"))
            if created:
                candidates.append(created)

            for review in revisoes_by_processo.get(process_id, []):
                if self._is_deleted(review):
                    continue

                start_date = self._parse_date(review.get("data_inicio_vigencia"))
                implementation_date = self._parse_date(review.get("data_implantacao"))

                if start_date:
                    candidates.append(start_date)
                elif implementation_date:
                    candidates.append(implementation_date)

        return min(candidates) if candidates else None

    def _calculate_date_range_proration_factor(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        monthly_breakdown: List[dict],
    ) -> float:
        """
        Calculate proration for totals when filtering by a partial date range.
        
        Only applies proration when BOTH conditions are true:
        1. Using YYYY-MM-DD format (not YYYY-MM)
        2. The filtered range spans partial months (not starting day 1 or not ending on last day)
        
        Returns:
        - 1.0 if no special filtering needed
        - < 1.0 if the period has partial months at start/end
        """
        # Only apply proration if we have specific day-level dates (YYYY-MM-DD format)
        if not start_date or not end_date or len(start_date) < 10 or len(end_date) < 10:
            return 1.0

        try:
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
        except (ValueError, TypeError):
            return 1.0

        if not start_date_obj or not end_date_obj:
            return 1.0

        # If monthly breakdown is empty, no proration needed
        if not monthly_breakdown:
            return 1.0

        # Get the first and last months in the breakdown
        first_competencia = monthly_breakdown[0].get("competencia", "")
        last_competencia = monthly_breakdown[-1].get("competencia", "")

        try:
            first_month_date = datetime.strptime(first_competencia, "%Y-%m").date()
            last_month_date = datetime.strptime(last_competencia, "%Y-%m").date()
        except (ValueError, TypeError):
            return 1.0

        # Calculate days in first month
        first_month_days = calendar.monthrange(first_month_date.year, first_month_date.month)[1]
        
        # Calculate days in last month
        last_month_days = calendar.monthrange(last_month_date.year, last_month_date.month)[1]

        # Determine effective first and last days
        first_day_in_month = start_date_obj.day
        last_day_in_month = end_date_obj.day

        # If start is not on day 1, prorate the first month
        if first_day_in_month > 1:
            first_days_in_range = first_month_days - first_day_in_month + 1
            proration_from_first = first_days_in_range / first_month_days
        else:
            proration_from_first = 1.0

        # If end is not on last day of month, prorate the last month
        if last_day_in_month < last_month_days:
            proration_from_last = last_day_in_month / last_month_days
        else:
            proration_from_last = 1.0

        # Count total months in breakdown
        total_months = len(monthly_breakdown)

        # If only 1 month, apply both prorations (it's the same month)
        if total_months == 1 and first_competencia == last_competencia:
            # Both are in the same month
            effective_days = 0
            for day in range(first_day_in_month, last_day_in_month + 1):
                effective_days += 1
            return effective_days / first_month_days

        # If 2+ months, average the partial proration
        # (first month partial, middle months full, last month partial)
        if proration_from_first < 1.0 or proration_from_last < 1.0:
            # Average the reduction across all months
            total_reduction = (1.0 - proration_from_first) + (1.0 - proration_from_last)
            avg_reduction = total_reduction / total_months
            return 1.0 - avg_reduction

        return 1.0

    def _build_range_summary(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        monthly_breakdown: List[dict],
        proration_factor: float = 1.0,
    ) -> dict:
        if not start_date and not end_date:
            accumulated = sum(item["economia_liquida_mes"] for item in monthly_breakdown)
            return {
                "competencia_inicio": None,
                "competencia_fim": None,
                "economia_liquida_acumulada": self._round_final(accumulated * proration_factor),
            }

        start_month = self._month_start(self._parse_date(start_date)) if start_date else None
        end_month = self._month_start(self._parse_date(end_date)) if end_date else None

        accumulated = 0.0

        for item in monthly_breakdown:
            month_date = datetime.strptime(item["competencia"], "%Y-%m").date()

            if start_month and month_date < start_month:
                continue
            if end_month and month_date > end_month:
                continue

            accumulated += item["economia_liquida_mes"]

        return {
            "competencia_inicio": start_date,
            "competencia_fim": end_date,
            "economia_liquida_acumulada": self._round_final(accumulated * proration_factor),
        }

    def _sort_reviews(self, reviews: List[dict]) -> List[dict]:
        def sort_key(item: dict) -> Tuple[date, date, str]:
            updated_at = self._parse_date(item.get("updated_at")) or date.min
            start_date = self._parse_date(item.get("data_inicio_vigencia")) or date.min
            version = self._empty_to_none(item.get("versao_revisao")) or ""
            return (updated_at, start_date, version)

        return sorted(reviews, key=sort_key)

    def _active_fraction_in_month(self, review: dict, month_date: date) -> float:
        start_date = self._review_calculation_start_date(review)
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
        """
        Determine if an investment is active during a given month.
        
        Rules:
        - For one-time (unico): active only in the investment month
        - For recurring: active from investment month through (investment_month + meses_vigencia - 1)
        - If no end date specified, assumes indefinite vigency
        
        Args:
            item: Investment record
            competencia_date: Month to check
            
        Returns:
            True if investment is active during the month
        """
        if self._is_deleted(item):
            return False

        # Parse investment start date
        investment_date = self._parse_date(item.get("data_investimento"))
        if investment_date is None:
            return False

        recurrence = (self._empty_to_none(item.get("recorrencia")) or "unico").lower()
        current_month = self._month_start(competencia_date)
        start_month = self._month_start(investment_date)

        # For one-time investments, only active in investment month
        if recurrence == "unico":
            return current_month == start_month

        # For recurring investments, check vigency
        if current_month < start_month:
            return False

        # If no vigency period specified, assumes it continues indefinitely
        meses_vigencia = self._to_int(item.get("meses_vigencia"))
        if meses_vigencia is None or meses_vigencia <= 0:
            # No end date, still active
            return True

        # Check if within vigency period
        end_month = self._add_months(start_month, meses_vigencia - 1)
        return current_month <= end_month

    def _is_comparable_review(self, review: dict) -> bool:
        cenario_tipo = (self._empty_to_none(review.get("cenario_tipo")) or "").lower()
        return cenario_tipo in self.COMPARABLE_SCENARIOS

    def _is_deleted(self, row: dict) -> bool:
        deleted = row.get("deletado")
        if isinstance(deleted, bool):
            return deleted
        raw = self._empty_to_none(deleted)
        return (raw or "").upper() in {"TRUE", "1", "SIM", "YES"}

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

    def _parse_date(self, value) -> Optional[date]:
        if value is None:
            return None

        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        if isinstance(value, datetime):
            return value.date()

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
