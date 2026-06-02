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

        # Apply date range proration if filtering by partial months
        monthly_breakdown = self._apply_date_range_proration(
            monthly_breakdown=monthly_breakdown,
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

        total_net_savings = sum(item["economia_liquida_mes"] for item in monthly_breakdown)
        total_hours_saved = sum(row["horas_economizadas_mes"] for row in calculation_rows)
        total_gross_savings = sum(item["economia_bruta"] for item in monthly_breakdown)
        total_recurring = sum(item["custo_recorrente_mes"] for item in monthly_breakdown)
        total_unique = sum(item["investimento_unico_mes"] for item in monthly_breakdown)
        average_roi = self._calculate_average_roi(calculation_rows)

        range_summary = self._build_range_summary(
            start_date=start_date,
            end_date=end_date,
            monthly_breakdown=monthly_breakdown,
        )

        return {
            "solucoes_implementadas": implemented_solutions_count,
            "economia_liquida_total": self._round_final(total_net_savings),
            "economia_bruta_total": self._round_final(total_gross_savings),
            "horas_economizadas_total": self._round_final(total_hours_saved),
            "investimento_unico_total": self._round_final(total_unique),
            "custo_recorrente_total": self._round_final(total_recurring),
            "roi_medio": self._round_final(average_roi),
            "evolucao_mensal": monthly_breakdown,
            "periodo": range_summary,
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
                    economia_liquida_mes += row["economia_liquida_mes"]
                    calculation_rows.append(row)

            monthly_items.append(
                {
                    "competencia": cursor.strftime("%Y-%m"),
                    "economia_bruta": self._round_final(economia_bruta_mes),
                    "investimento_unico_mes": self._round_final(investimento_unico_mes),
                    "custo_recorrente_mes": self._round_final(custo_recorrente_mes),
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

        economia_liquida_mes = savings["economia_bruta"] - custo_recorrente_mes

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

        custo_recorrente_mes = self._calculate_recurring_investment_month(
            investments=context.investimentos_by_revisao.get(review_id, []),
            competencia_date=current_month,
        )

        economia_liquida_mes = savings["economia_bruta"] - custo_recorrente_mes
        return economia_liquida_mes / 30.0

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

        economia_liquida_mes = savings["economia_bruta"] - custo_recorrente_mes
        if economia_liquida_mes <= 0:
            return None

        return total_unique_investment / economia_liquida_mes

    def _calculate_average_roi(self, calculation_rows: List[dict]) -> float:
        grouped: Dict[str, dict] = {}

        for row in calculation_rows:
            if row["cenario_tipo"] not in self.COMPARABLE_SCENARIOS:
                continue

            revisao_id = row["revisao_id"]
            grouped.setdefault(
                revisao_id,
                {
                    "economia_liquida_acumulada": 0.0,
                    "investimento_unico_acumulado": 0.0,
                },
            )
            grouped[revisao_id]["economia_liquida_acumulada"] += row["economia_liquida_mes"]
            grouped[revisao_id]["investimento_unico_acumulado"] += row["investimento_unico_mes"]

        rois: List[float] = []

        for values in grouped.values():
            investment = values["investimento_unico_acumulado"]
            if investment <= 0:
                continue

            roi = (
                values["economia_liquida_acumulada"] - investment
            ) / investment
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
            and not self._is_deleted(review)
        ]
        if baseline_reviews:
            return self._sort_reviews(baseline_reviews)[0]

        active_reviews = [review for review in reviews if not self._is_deleted(review)]
        if not active_reviews:
            return None

        return self._sort_reviews(active_reviews)[0]

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

    def _apply_date_range_proration(
        self,
        monthly_breakdown: List[dict],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[dict]:
        """
        Apply temporal proration to monthly breakdown when filtering by a date range.
        If the user filters by specific days (e.g., 2026-06-01 to 2026-06-02),
        this prorates the monthly values to reflect only the filtered period.
        
        E.g., if filtering 2 days of a 30-day month, multiply monthly values by 2/30.
        """
        # Only apply proration if we have specific day-level dates (YYYY-MM-DD format)
        if not start_date or not end_date or len(start_date) < 10 or len(end_date) < 10:
            return monthly_breakdown

        try:
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
        except (ValueError, TypeError):
            return monthly_breakdown

        if not start_date_obj or not end_date_obj:
            return monthly_breakdown

        prorated_breakdown: List[dict] = []

        for item in monthly_breakdown:
            competencia_str = item.get("competencia", "")
            try:
                # Parse competencia (YYYY-MM) to get month boundaries
                competencia_date = datetime.strptime(competencia_str, "%Y-%m").date()
                year = competencia_date.year
                month = competencia_date.month
                first_day = date(year, month, 1)
                last_day = date(year, month, calendar.monthrange(year, month)[1])

                # Calculate the overlap between filtered range and this month
                effective_start = max(first_day, start_date_obj)
                effective_end = min(last_day, end_date_obj)

                # If no overlap, skip this item
                if effective_end < effective_start:
                    continue

                # Calculate proration factor
                days_in_range = (effective_end - effective_start).days + 1
                days_in_month = (last_day - first_day).days + 1
                proration_factor = days_in_range / days_in_month

                # Apply proration to all monetary values
                prorated_item = dict(item)
                for key in ["economia_bruta", "investimento_unico_mes", 
                           "custo_recorrente_mes", "economia_liquida_mes"]:
                    if key in prorated_item and prorated_item[key] is not None:
                        original_value = float(prorated_item[key])
                        prorated_item[key] = original_value * proration_factor

                prorated_breakdown.append(prorated_item)

            except (ValueError, TypeError):
                # If we can't parse the competencia, keep the original item
                prorated_breakdown.append(item)

        return prorated_breakdown

    def _build_range_summary(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        monthly_breakdown: List[dict],
    ) -> dict:
        if not start_date and not end_date:
            accumulated = sum(item["economia_liquida_mes"] for item in monthly_breakdown)
            return {
                "competencia_inicio": None,
                "competencia_fim": None,
                "economia_liquida_acumulada": self._round_final(accumulated),
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
            "economia_liquida_acumulada": self._round_final(accumulated),
        }

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