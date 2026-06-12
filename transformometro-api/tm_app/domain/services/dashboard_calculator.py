from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from tm_app.core.business_days import (
    business_days_in_month,
    business_month_calendar_factor,
    business_days_overlap_in_competencia,
    count_business_days,
)
from tm_app.domain import calc_rules
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.recurso_custo_resolver import resolve_recurso_valor_mensal
from tm_app.domain.services.dashboard_cache_denorm_service import (
    resolve_cache_scope_for_review,
)
from tm_app.domain.services.shared_resource_scope_service import filter_rateio_pool


@dataclass(frozen=True)
class CalculationContext:
    processos_by_id: Dict[str, dict]
    revisoes_by_id: Dict[str, dict]
    instancias_by_id: Dict[str, dict]
    revisoes_by_processo: Dict[str, List[dict]]
    medicoes_by_revisao: Dict[str, dict]
    investimentos_by_revisao: Dict[str, List[dict]]
    recursos_by_id: Dict[str, dict]
    vinculos_by_revisao: Dict[str, List[dict]]
    custos_by_recurso: Dict[str, List[dict]]


class DashboardCalculatorService:
    COMPARABLE_SCENARIOS = set(calc_rules.COMPARABLE_SCENARIOS)

    def build_process_list(self, raw: TransformometroRawData) -> List[dict]:
        return self.build_instancia_list(raw)

    def build_instancia_list(self, raw: TransformometroRawData) -> List[dict]:
        context = self._build_context(raw)
        items: List[dict] = []
        for inst_row in self._instancias_for_list(raw):
            item = self._build_instancia_list_item(inst_row, context)
            if item:
                items.append(item)
        return items

    def _instancias_for_list(self, raw: TransformometroRawData) -> List[dict]:
        if raw.processo_instancias:
            return list(raw.processo_instancias)
        synth: List[dict] = []
        for process_row in raw.processos:
            process_id = self._empty_to_none(process_row.get("processo_id"))
            if not process_id:
                continue
            synth.append(
                {
                    "instancia_id": process_id,
                    "processo_id": process_id,
                    "codigo_filial": process_row.get("filial_id"),
                    "codigo_setor": process_row.get("setor_id"),
                }
            )
        return synth

    def _revisoes_for_instancia(
        self,
        context: CalculationContext,
        *,
        instancia_id: str,
        process_id: str,
    ) -> List[dict]:
        all_revisoes = context.revisoes_by_processo.get(process_id, [])
        scoped = [
            revisao
            for revisao in all_revisoes
            if str(revisao.get("instancia_id") or "") == instancia_id
        ]
        if scoped:
            return scoped
        if not any(revisao.get("instancia_id") for revisao in all_revisoes):
            return all_revisoes
        return []

    def _build_instancia_list_item(
        self,
        inst_row: dict,
        context: CalculationContext,
    ) -> dict | None:
        process_id = self._empty_to_none(inst_row.get("processo_id"))
        instancia_id = self._empty_to_none(inst_row.get("instancia_id"))
        if not process_id or not instancia_id:
            return None

        process_row = context.processos_by_id.get(process_id, {})
        revisoes = self._revisoes_for_instancia(
            context,
            instancia_id=str(instancia_id),
            process_id=str(process_id),
        )
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

        filial_codigo = self._empty_to_none(inst_row.get("codigo_filial")) or self._empty_to_none(
            process_row.get("filial_id")
        )
        setor_codigo = self._empty_to_none(inst_row.get("codigo_setor")) or self._empty_to_none(
            process_row.get("setor_id")
        )

        return {
            "instancia_id": str(instancia_id),
            "processo_id": str(process_id),
            "codigo_processo": self._empty_to_none(process_row.get("codigo_processo")),
            "nome_processo": self._empty_to_none(process_row.get("nome_processo")) or "",
            "filial_id": filial_codigo,
            "setor_id": setor_codigo,
            "economia_diaria": self._round_final(daily_savings),
            "payback_meses": self._round_final(payback_months),
            "status_processo": self._empty_to_none(process_row.get("status_processo")),
            "data_implantacao": implementation_date,
        }

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

        monthly_for_totals = self._monthly_breakdown_for_period(
            monthly_breakdown,
            calculation_rows,
            start_date=start_date,
            end_date=end_date,
        )

        period_totals = self._aggregate_period_from_rows(
            calculation_rows,
            start_date=start_date,
            end_date=end_date,
        )

        total_net_savings = period_totals["economia_liquida_mes"]
        total_gross_savings = period_totals["economia_bruta"]
        total_recurring = period_totals["custo_recorrente_mes"]
        total_unique = period_totals["investimento_unico_mes"]
        total_shared_resources = period_totals["custo_recursos_compartilhados_mes"]
        total_investment = period_totals["investimento_total_mes"]
        total_hours_saved = period_totals["horas_economizadas_mes"]

        implemented_solutions_count = len(
            {
                row["revisao_id"]
                for row in calculation_rows
                if row["cenario_tipo"] in self.COMPARABLE_SCENARIOS
                and self.competencia_day_fraction_in_range(
                    str(row.get("competencia") or ""),
                    start_date,
                    end_date,
                )
                > 0
                and float(row.get("economia_bruta") or 0) > 0
            }
        )

        consolidated_roi = (
            total_net_savings / total_investment if total_investment > 0 else 0.0
        )

        range_summary = self._build_range_summary(
            start_date=start_date,
            end_date=end_date,
            monthly_breakdown=monthly_for_totals,
            proration_factor=1.0,
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
            "roi_medio": self._round_final(consolidated_roi),
            "evolucao_mensal": monthly_for_totals,
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

        instancias_filtradas = [
            instancia
            for instancia in raw.processo_instancias
            if self._empty_to_none(instancia.get("processo_id")) in processo_ids
        ]

        return TransformometroRawData(
            processos=processos_filtrados,
            processo_instancias=instancias_filtradas,
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
            revisoes_by_id=self._index_by(raw.revisoes, "revisao_id"),
            instancias_by_id=self._index_by(raw.processo_instancias, "instancia_id"),
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

        start_date = self._normalize_date_filter(start_date)
        end_date = self._normalize_date_filter(end_date)

        start_month = (
            self._resolve_filter_month_start(start_date, timeline_start)
            if start_date
            else self._month_start(timeline_start)
        )
        end_month = (
            self._resolve_filter_month_start(end_date, date.today())
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
            horas_economizadas_mes = 0.0

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
                    horas_economizadas_mes += float(row.get("horas_economizadas_mes") or 0)
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
                    "horas_economizadas_mes": self._round_final(horas_economizadas_mes),
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

        horas_economizadas_mes = 0.0
        if self._is_comparable_review(review):
            horas_economizadas_mes = self._calculate_hours_saved_month(
                baseline_measurement=baseline_measurement,
                current_measurement=current_measurement,
                review=review,
                competencia_date=competencia_date,
            )

        if self._is_comparable_review(review):
            bd_factor = business_month_calendar_factor(
                competencia_date.year, competencia_date.month
            )
            if bd_factor != 1.0:
                for key in (
                    "economia_tempo",
                    "economia_retrabalho",
                    "economia_erros",
                    "economia_outros",
                    "economia_recursos_compartilhados",
                    "economia_bruta",
                ):
                    savings[key] = float(savings.get(key) or 0) * bd_factor
                horas_economizadas_mes *= bd_factor

        investimento_total_mes = (
            investimento_unico_mes + custo_recorrente_mes + current_shared_cost
        )
        economia_liquida_mes = savings["economia_bruta"] - investimento_total_mes

        competencia = competencia_date.strftime("%Y-%m")
        processo_id = self._empty_to_none(process_row.get("processo_id")) or ""
        scope = resolve_cache_scope_for_review(
            review,
            process_row,
            instancias_by_id=context.instancias_by_id,
        )

        return {
            "revisao_id": review_id,
            "processo_id": processo_id,
            "instancia_id": scope.get("instancia_id"),
            "competencia": competencia,
            "filial_id": scope.get("filial_id"),
            "setor_id": scope.get("setor_id"),
            "codigo_filial": scope.get("codigo_filial"),
            "codigo_setor": scope.get("codigo_setor"),
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

        business_days = business_days_in_month(current_month.year, current_month.month)
        if business_days <= 0:
            return None

        return savings["economia_bruta"] / business_days

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
        return calc_rules.hours_saved_in_competencia_month(
            baseline_measurement,
            current_measurement,
            review,
            competencia_date,
        )

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

        active_days = count_business_days(effective_start, effective_end)
        total_days = count_business_days(month_start, month_end)
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
                resource=resource,
                anchor_revisao_id=review_id,
                context=context,
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
        resource: dict,
        anchor_revisao_id: str,
        context: CalculationContext,
        competencia_date: date,
    ) -> List[dict]:
        result: List[dict] = []

        for revisao_id, review_links in context.vinculos_by_revisao.items():
            for link in review_links:
                if self._empty_to_none(link.get("recurso_compartilhado_id")) != resource_id:
                    continue
                if not self._is_link_eligible(link, competencia_date):
                    continue
                enriched = dict(link)
                enriched.setdefault("revisao_id", revisao_id)
                result.append(enriched)

        return filter_rateio_pool(
            resource,
            result,
            anchor_revisao_id=anchor_revisao_id,
            revisoes_by_id=context.revisoes_by_id,
            instancias_by_id=context.instancias_by_id,
            processos_by_id=context.processos_by_id,
        )

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
        return calc_rules.review_calculation_start_date(review)

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

    def _uses_day_level_date_filter(
        self, start_date: Optional[str], end_date: Optional[str]
    ) -> bool:
        return calc_rules.uses_day_level_date_filter(start_date, end_date)

    def competencia_day_fraction_in_range(
        self,
        competencia: str,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> float:
        return calc_rules.competencia_day_fraction_in_range(
            competencia, start_date, end_date
        )

    def _prorate_row_metrics_for_period(
        self,
        row: dict,
        *,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[dict[str, float]]:
        return calc_rules.prorate_dashboard_row_for_period(
            row,
            start_date=start_date,
            end_date=end_date,
        )

    def _aggregate_period_from_rows(
        self,
        calculation_rows: List[dict],
        *,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> dict[str, float]:
        totals = calc_rules.aggregate_period_from_rows(
            calculation_rows,
            start_date=start_date,
            end_date=end_date,
        )
        return {key: self._round_final(value) for key, value in totals.items()}

    def _monthly_breakdown_for_period(
        self,
        monthly_breakdown: List[dict],
        calculation_rows: List[dict],
        *,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[dict]:
        if not self._uses_day_level_date_filter(start_date, end_date):
            return monthly_breakdown

        by_competencia: Dict[str, dict[str, float]] = {}
        for row in calculation_rows:
            prorated = self._prorate_row_metrics_for_period(
                row,
                start_date=start_date,
                end_date=end_date,
            )
            if prorated is None:
                continue

            competencia = str(row.get("competencia") or "")
            bucket = by_competencia.setdefault(
                competencia,
                {
                    "competencia": competencia,
                    "economia_bruta": 0.0,
                    "economia_liquida_mes": 0.0,
                    "investimento_unico_mes": 0.0,
                    "custo_recorrente_mes": 0.0,
                    "custo_recursos_compartilhados_mes": 0.0,
                    "investimento_total_mes": 0.0,
                    "horas_economizadas_mes": 0.0,
                },
            )
            for key, value in prorated.items():
                bucket[key] += value

        return [
            {
                "competencia": competencia,
                "economia_bruta": self._round_final(values["economia_bruta"]),
                "investimento_unico_mes": self._round_final(values["investimento_unico_mes"]),
                "custo_recorrente_mes": self._round_final(values["custo_recorrente_mes"]),
                "investimento_total_mes": self._round_final(values["investimento_total_mes"]),
                "custo_recursos_compartilhados_mes": self._round_final(
                    values["custo_recursos_compartilhados_mes"]
                ),
                "economia_liquida_mes": self._round_final(values["economia_liquida_mes"]),
                "horas_economizadas_mes": self._round_final(values["horas_economizadas_mes"]),
            }
            for competencia, values in sorted(by_competencia.items())
        ]

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

        first_month_business_days = business_days_in_month(
            first_month_date.year, first_month_date.month
        )
        last_month_business_days = business_days_in_month(
            last_month_date.year, last_month_date.month
        )

        first_day_in_month = start_date_obj.day
        last_day_in_month = end_date_obj.day
        first_calendar_days = calendar.monthrange(
            first_month_date.year, first_month_date.month
        )[1]
        last_calendar_days = calendar.monthrange(
            last_month_date.year, last_month_date.month
        )[1]

        first_overlap = business_days_overlap_in_competencia(
            first_competencia, start_date_obj, end_date_obj
        )
        if first_day_in_month > 1:
            proration_from_first = (
                first_overlap / first_month_business_days
                if first_month_business_days > 0
                else 1.0
            )
        else:
            proration_from_first = 1.0

        if last_day_in_month < last_calendar_days:
            last_overlap = business_days_overlap_in_competencia(
                last_competencia, start_date_obj, end_date_obj
            )
            proration_from_last = (
                last_overlap / last_month_business_days
                if last_month_business_days > 0
                else 1.0
            )
        else:
            proration_from_last = 1.0

        total_months = len(monthly_breakdown)

        if total_months == 1 and first_competencia == last_competencia:
            if first_month_business_days <= 0:
                return 1.0
            return first_overlap / first_month_business_days

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

        start_input = self._normalize_date_filter(start_date)
        end_input = self._normalize_date_filter(end_date)
        start_month = self._parse_month_start_or_none(start_input) if start_input else None
        end_month = self._parse_month_start_or_none(end_input) if end_input else None

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
        return calc_rules.review_vigencia_fraction_in_month(review, month_date)

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

    def _normalize_date_filter(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw or raw.lower() in {"null", "undefined", "invalid", "nan"}:
            return None
        return raw

    def _resolve_filter_month_start(self, value: Optional[str], fallback: date) -> date:
        parsed = self._parse_date(value)
        if parsed is None:
            return self._month_start(fallback)
        return self._month_start(parsed)

    def _parse_month_start_or_none(self, value: Optional[str]) -> Optional[date]:
        parsed = self._parse_date(value)
        if parsed is None:
            return None
        return self._month_start(parsed)

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

        if "T" in raw:
            iso_raw = raw.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(iso_raw).date()
            except ValueError:
                pass

        try:
            return date.fromisoformat(raw[:10] if len(raw) >= 10 and raw[4] == "-" else raw)
        except ValueError:
            pass

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
