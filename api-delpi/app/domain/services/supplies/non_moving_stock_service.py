"""Domínio — matérias-primas sem giro (GLPI #1197, ratificações R-01/R-02/R-03).

Responsabilidades:
- resolver a janela de análise de consumo (padrão: 12 meses móveis até hoje);
- classificar cada produto×filial em WITH_CONSUMPTION / NO_CONSUMPTION_12M /
  NO_CONSUMPTION_IN_PERIOD / INSUFFICIENT_HISTORY;
- calcular denominadores e percentuais sem ocultar exclusões.

A decisão de "o que é utilização efetiva" fica no módulo canônico
`app/domain/totvs/protheus_internal_movements.py` (spec SQL compartilhada).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

STATUS_WITH_CONSUMPTION = "WITH_CONSUMPTION"
STATUS_NO_CONSUMPTION_12M = "NO_CONSUMPTION_12M"
STATUS_NO_CONSUMPTION_IN_PERIOD = "NO_CONSUMPTION_IN_PERIOD"
STATUS_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"

NO_CONSUMPTION_STATUSES = (
    STATUS_NO_CONSUMPTION_12M,
    STATUS_NO_CONSUMPTION_IN_PERIOD,
)

WINDOW_KIND_ROLLING_12M = "rolling_12m"
WINDOW_KIND_CUSTOM = "custom_period"

REASON_NO_ELIGIBLE_STOCK = "no_eligible_stock"
REASON_NO_EVALUABLE_STOCK = "no_evaluable_stock"

DEFAULT_ROLLING_MONTHS = 12

# Escopo aprovado (auditoria GLPI #1197): armazéns onde reside MP avaliável.
APPROVED_WAREHOUSE_SCOPE = ("01", "99")


def _sub_months(day: date, months: int) -> date:
    month = day.month - months
    year = day.year
    while month <= 0:
        month += 12
        year -= 1
    last_day = _days_in_month(year, month)
    return date(year, month, min(day.day, last_day))


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - timedelta(days=1)).day


@dataclass(frozen=True)
class ConsumptionWindow:
    """Janela de análise de consumo — limites inclusivos em YYYYMMDD."""

    start: str
    end: str
    kind: str  # WINDOW_KIND_ROLLING_12M | WINDOW_KIND_CUSTOM

    @property
    def no_consumption_status(self) -> str:
        if self.kind == WINDOW_KIND_ROLLING_12M:
            return STATUS_NO_CONSUMPTION_12M
        return STATUS_NO_CONSUMPTION_IN_PERIOD


def resolve_consumption_window(
    *,
    start_date: str | None,
    end_date: str | None,
    today: date | None = None,
) -> ConsumptionWindow:
    """Janela de consumo — R-03: padrão é 12 meses móveis até a data atual.

    Quando o usuário informa start_date/end_date, a janela é custom e o
    status sem giro usa a forma semântica coerente com a janela
    (NO_CONSUMPTION_IN_PERIOD em vez de NO_CONSUMPTION_12M).
    """
    ref = today or date.today()
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")
        return ConsumptionWindow(
            start=start_date, end=end_date, kind=WINDOW_KIND_CUSTOM
        )
    if start_date or end_date:
        raise ValueError(
            "start_date and end_date must be provided together"
        )
    start = _sub_months(ref, DEFAULT_ROLLING_MONTHS)
    return ConsumptionWindow(
        start=start.strftime("%Y%m%d"),
        end=ref.strftime("%Y%m%d"),
        kind=WINDOW_KIND_ROLLING_12M,
    )


def classify_product(
    *,
    coverage_start: str | None,
    last_utilization_in_window: str | None,
    window: ConsumptionWindow,
) -> str:
    """Status de giro por produto×filial.

    - WITH_CONSUMPTION: utilização efetiva comprovada dentro da janela —
      fato observado que não depende de cobertura completa.
    - INSUFFICIENT_HISTORY: sem utilização na janela e sem evidência de
      existência (fechamento SB9 ou SD3) até o início da janela — não é
      possível distinguir "parado" de "ainda não existia".
    - NO_CONSUMPTION_*: cobertura completa e nenhuma utilização na janela.
    """
    if last_utilization_in_window is not None:
        return STATUS_WITH_CONSUMPTION
    if coverage_start is None or coverage_start > window.start:
        return STATUS_INSUFFICIENT_HISTORY
    return window.no_consumption_status


def summarize_availability(
    *,
    eligible_stock_value: float,
    evaluable_stock_value: float,
) -> tuple[str, str | None]:
    """Estado de disponibilidade do indicador (fail-closed)."""
    if eligible_stock_value <= 0:
        return "unavailable", REASON_NO_ELIGIBLE_STOCK
    if evaluable_stock_value <= 0:
        return "unavailable", REASON_NO_EVALUABLE_STOCK
    return "ok", None


def percentage(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole <= 0:
        return None
    return round(part * 100.0 / whole, 2)
