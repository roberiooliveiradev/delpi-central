"""Regras centralizadas de cálculo do Transformômetro (dashboard e rankings).

Toda prorrata por recorte, vigência mensal de revisão, horas economizadas e
médias diárias deve passar por este módulo. Serviços (`DashboardCalculatorService`,
`DashboardLiveService`) delegam aqui para evitar divergência.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Optional

from tm_app.core.business_days import (
    business_day_fraction_in_competencia_range,
    count_business_days,
    total_business_days_for_competencias,
)

COMPARABLE_SCENARIOS = frozenset({"melhoria", "automacao", "correcao"})

# Validade da revisão: a economia só é contabilizada por 12 meses a partir do
# início do cálculo (implantação / vigência). A partir da data de aniversário a
# revisão deixa de contar, salvo se uma nova revisão implantada assumir o cálculo.
REVIEW_VALIDITY_MONTHS = 12
# Janela de acompanhamento de revisões prestes a vencer (dashboard).
REVIEW_EXPIRY_ALERT_DAYS = 90

PERIOD_TOTAL_KEYS = (
    "economia_bruta",
    "economia_liquida_mes",
    "investimento_unico_mes",
    "custo_recorrente_mes",
    "custo_recursos_compartilhados_mes",
    "investimento_total_mes",
    "horas_economizadas_mes",
)

PRORATABLE_BY_DAY_KEYS = (
    "economia_bruta",
    "custo_recorrente_mes",
    "custo_recursos_compartilhados_mes",
    "horas_economizadas_mes",
)


def parse_date(value: Any) -> Optional[date]:
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


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_period_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def clamp_period_to_elapsed_days(
    start_date: Optional[str],
    end_date: Optional[str],
    *,
    today: Optional[date] = None,
) -> tuple[Optional[str], Optional[str], bool]:
    """Limita o recorte a dias já percorridos (não projeta ganhos futuros).

    Retorna ``(start, end, is_entirely_future)``. Quando o período inteiro é
    futuro, o caller deve zerar economia/ganhos.
    """
    ref = today or date.today()
    start = parse_date(start_date)
    end = parse_date(end_date)

    if start is None and end is None:
        return start_date, end_date, False

    if start is None:
        start = end
    if end is None:
        end = start
    if start is None or end is None:
        return start_date, end_date, False

    if start > ref:
        return start_date, end_date, True

    if end > ref:
        end = ref

    if end < start:
        end = start

    return format_period_date(start), format_period_date(end), False


def uses_day_level_date_filter(
    start_date: Optional[str],
    end_date: Optional[str],
) -> bool:
    return bool(
        start_date
        and end_date
        and len(str(start_date)) >= 10
        and len(str(end_date)) >= 10
    )


def competencia_day_fraction_in_range(
    competencia: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> float:
    """Fração dos dias do mês civil incluída no recorte YYYY-MM-DD … YYYY-MM-DD."""
    return business_day_fraction_in_competencia_range(
        competencia,
        start_date,
        end_date,
        uses_day_level_filter=uses_day_level_date_filter(start_date, end_date),
    )


def is_comparable_scenario(cenario_tipo: Optional[str]) -> bool:
    return (cenario_tipo or "").lower() in COMPARABLE_SCENARIOS


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "t", "yes", "sim"}


def _is_deleted(row: dict[str, Any]) -> bool:
    return _is_truthy(row.get("deletado"))


def count_active_implemented_improvements(
    *,
    instancias: list[dict[str, Any]],
    revisoes: list[dict[str, Any]],
) -> int:
    """Conta melhorias (instâncias) com revisão comparável ativa no cadastro.

    Snapshot do estado atual — independente do recorte de competência do dashboard.
    """
    allowed_instancias = {
        str(row.get("instancia_id"))
        for row in instancias
        if row.get("instancia_id") and not _is_deleted(row)
    }
    active: set[str] = set()
    for review in revisoes:
        if _is_deleted(review):
            continue
        if not _is_truthy(review.get("revisao_ativa")):
            continue
        if not is_comparable_scenario(review.get("cenario_tipo")):
            continue
        instancia_id = str(review.get("instancia_id") or "")
        if instancia_id in allowed_instancias:
            active.add(instancia_id)
    return len(active)


def review_calculation_start_date(review: dict) -> Optional[date]:
    start_date = parse_date(review.get("data_inicio_vigencia"))
    implementation_date = parse_date(review.get("data_implantacao"))
    cenario = (review.get("cenario_tipo") or "").lower()

    if cenario not in COMPARABLE_SCENARIOS:
        return start_date or implementation_date

    if start_date and implementation_date:
        return max(start_date, implementation_date)
    return implementation_date or start_date


def add_months(base: date, months: int) -> date:
    """Soma ``months`` a ``base`` preservando o fim de mês (ex.: 31/01 + 1m = 28/02)."""
    total = base.month - 1 + months
    year = base.year + total // 12
    month = total % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(base.day, last_day))


def review_validity_end_date(review: dict) -> Optional[date]:
    """Data de aniversário (exclusiva) da revisão comparável: ``início + 12 meses``.

    A economia é contabilizada em ``[início, aniversário)``; a partir do aniversário a
    revisão não conta mais. Revisões não comparáveis (baseline) não têm validade.
    """
    if not is_comparable_scenario(review.get("cenario_tipo")):
        return None
    start_date = review_calculation_start_date(review)
    if start_date is None:
        return None
    return add_months(start_date, REVIEW_VALIDITY_MONTHS)


def review_effective_end_date(review: dict) -> Optional[date]:
    """Último dia efetivo de contabilização: ``min(data_fim_vigencia, aniversário-1dia)``.

    ``None`` quando a revisão não tem fim de vigência nem validade (sem teto).
    """
    ends: list[date] = []
    parsed_end = parse_date(review.get("data_fim_vigencia"))
    if parsed_end is not None:
        ends.append(parsed_end)
    anniversary = review_validity_end_date(review)
    if anniversary is not None:
        ends.append(anniversary - timedelta(days=1))
    return min(ends) if ends else None


def review_vigencia_fraction_in_month(review: dict, month_date: date) -> float:
    """Fração de dias da competência em que a revisão está vigente.

    Revisão sem fim (`data_fim_vigencia`) nem validade usa o mês civil inteiro (não
    ``date.today()``). A validade de 12 meses limita o fim efetivo (`review_effective_end_date`),
    zerando a contribuição a partir do aniversário. O filtro YYYY-MM-DD do dashboard
    prorrata depois na agregação do recorte.
    """
    start_date = review_calculation_start_date(review)
    if start_date is None:
        return 0.0

    year = month_date.year
    month = month_date.month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    effective_end_review = review_effective_end_date(review)
    end_date = effective_end_review if effective_end_review is not None else last_day

    effective_start = max(first_day, start_date)
    effective_end = min(last_day, end_date)
    if effective_end < effective_start:
        return 0.0

    active_days = count_business_days(effective_start, effective_end)
    total_days = count_business_days(first_day, last_day)
    if total_days <= 0:
        return 0.0
    return active_days / total_days


def total_minutes_saved_month(
    baseline_measurement: dict,
    current_measurement: dict,
) -> float:
    baseline_time = to_float(baseline_measurement.get("tempo_medio_execucao_min")) or 0.0
    current_time = to_float(current_measurement.get("tempo_medio_execucao_min")) or 0.0
    baseline_volume = to_float(baseline_measurement.get("volume_mensal")) or 0.0
    current_volume = to_float(current_measurement.get("volume_mensal")) or 0.0
    return max(
        0.0,
        (baseline_time * baseline_volume) - (current_time * current_volume),
    )


def hours_saved_in_competencia_month(
    baseline_measurement: dict,
    current_measurement: dict,
    review: dict,
    competencia_date: date,
) -> float:
    minutes_saved = total_minutes_saved_month(baseline_measurement, current_measurement)
    if minutes_saved <= 0:
        return 0.0
    fraction = review_vigencia_fraction_in_month(review, competencia_date)
    return (minutes_saved * fraction) / 60.0


def prorate_dashboard_row_for_period(
    row: dict,
    *,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Optional[dict[str, float]]:
    """Prorrata métricas mensais pelo recorte; investimento único permanece integral.

    Instâncias ativas do processo **somam** no consolidado — cada linha já traz o valor
    integral da instância/revisão; ``instancias_ativas_mes`` é só metadado informativo.
    """
    day_fraction = competencia_day_fraction_in_range(
        str(row.get("competencia") or ""),
        start_date,
        end_date,
    )
    if day_fraction <= 0:
        return None

    scale = day_fraction

    economia_bruta = float(row.get("economia_bruta") or 0) * scale
    custo_recorrente_mes = float(row.get("custo_recorrente_mes") or 0) * scale
    custo_recursos_compartilhados_mes = (
        float(row.get("custo_recursos_compartilhados_mes") or 0) * scale
    )
    investimento_unico_mes = float(row.get("investimento_unico_mes") or 0)
    investimento_total_mes = (
        investimento_unico_mes + custo_recorrente_mes + custo_recursos_compartilhados_mes
    )
    economia_liquida_mes = economia_bruta - investimento_total_mes
    horas_economizadas_mes = float(row.get("horas_economizadas_mes") or 0) * scale

    return {
        "economia_bruta": economia_bruta,
        "economia_liquida_mes": economia_liquida_mes,
        "investimento_unico_mes": investimento_unico_mes,
        "custo_recorrente_mes": custo_recorrente_mes,
        "custo_recursos_compartilhados_mes": custo_recursos_compartilhados_mes,
        "investimento_total_mes": investimento_total_mes,
        "horas_economizadas_mes": horas_economizadas_mes,
    }


def empty_period_totals() -> dict[str, float]:
    return {key: 0.0 for key in PERIOD_TOTAL_KEYS}


def merge_period_totals(target: dict[str, float], prorated: dict[str, float]) -> None:
    for key in PERIOD_TOTAL_KEYS:
        target[key] += float(prorated.get(key) or 0)


def aggregate_period_from_rows(
    calculation_rows: list[dict],
    *,
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict[str, float]:
    totals = empty_period_totals()
    for row in calculation_rows:
        prorated = prorate_dashboard_row_for_period(
            row,
            start_date=start_date,
            end_date=end_date,
        )
        if prorated is None:
            continue
        merge_period_totals(totals, prorated)
    return totals


def period_days_denominator(
    competencias: set[str] | list[str],
    *,
    start_date: Optional[str],
    end_date: Optional[str],
) -> float:
    days = total_business_days_for_competencias(
        competencias,
        start_date=start_date,
        end_date=end_date,
        uses_day_level_filter=uses_day_level_date_filter(start_date, end_date),
    )
    return max(days, 1.0)


def daily_averages_from_period_totals(
    totals: dict[str, float],
    competencias: set[str] | list[str],
    *,
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict[str, float]:
    """Médias diárias de economia bruta e horas no recorte (ranking e cards)."""
    days = period_days_denominator(
        competencias,
        start_date=start_date,
        end_date=end_date,
    )
    bruta = float(totals.get("economia_bruta") or 0)
    horas = float(totals.get("horas_economizadas_mes") or 0)
    return {
        "economia_diaria": round(bruta / days, 2),
        "horas_diaria": round(horas / days, 2),
    }


@dataclass
class ProcessPeriodBucket:
    economia_liquida_mes: float = 0.0
    economia_bruta: float = 0.0
    investimento_unico_mes: float = 0.0
    custo_recorrente_mes: float = 0.0
    custo_recursos_compartilhados_mes: float = 0.0
    investimento_total_mes: float = 0.0
    horas_economizadas_mes: float = 0.0
    competencias: set[str] = field(default_factory=set)

    def merge_prorated(self, prorated: dict[str, float], competencia: str) -> None:
        self.economia_liquida_mes += prorated["economia_liquida_mes"]
        self.economia_bruta += prorated["economia_bruta"]
        self.investimento_unico_mes += prorated["investimento_unico_mes"]
        self.custo_recorrente_mes += prorated["custo_recorrente_mes"]
        self.custo_recursos_compartilhados_mes += prorated["custo_recursos_compartilhados_mes"]
        self.investimento_total_mes += prorated["investimento_total_mes"]
        self.horas_economizadas_mes += prorated["horas_economizadas_mes"]
        if competencia:
            self.competencias.add(competencia)

    def as_totals_dict(self) -> dict[str, float]:
        return {
            "economia_liquida_mes": self.economia_liquida_mes,
            "economia_bruta": self.economia_bruta,
            "investimento_unico_mes": self.investimento_unico_mes,
            "custo_recorrente_mes": self.custo_recorrente_mes,
            "custo_recursos_compartilhados_mes": self.custo_recursos_compartilhados_mes,
            "investimento_total_mes": self.investimento_total_mes,
            "horas_economizadas_mes": self.horas_economizadas_mes,
        }


def horas_diaria_fallback_from_bruta(
    *,
    economia_bruta: float,
    economia_diaria: float,
    horas_economizadas_mes: float,
) -> float:
    """Fallback proporcional (frontend legado) — preferir ``horas_diaria`` da API."""
    if economia_bruta <= 0 or economia_diaria <= 0 or horas_economizadas_mes <= 0:
        return 0.0
    return (horas_economizadas_mes / economia_bruta) * economia_diaria
