"""Domínio — acuracidade do inventário físico (GLPI #1197 / GATE 4.2).

Semântica oficial (Protheus MATA270):
- Evento = (B7_FILIAL, B7_COD, B7_LOCAL, B7_DATA); contagens físicas de um
  mesmo evento agregam por SUM(B7_QUANT).
- B7_STATUS = '2' → contagem processada pelo MATA270 (veredito oficial).
- B7_STATUS = '1'/'' → pendente de processamento → fora do denominador
  avaliável (exclusão auditável, não descarte silencioso).
- Contagem processada sem ajuste SD3 INVENT = veredito oficial "correta";
  com ajuste INVENT = "divergente". Ausência de ajuste não prova igualdade
  física — prova a decisão oficial do Protheus dentro de sua tolerância.
- Saldo teórico exibido por evento deriva da decisão oficial:
  teórico = contado + furo_RE0 - sobra_DE0 (a autoridade é o ajuste SD3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

OUTCOME_ACCURATE = "accurate"
OUTCOME_DIVERGENT = "divergent"
OUTCOME_EXCLUDED = "excluded"

REASON_PENDING_PROCESSING = "pending_processing"

STATUS_PROCESSED = "2"
STATUS_PENDING = {"1", ""}

REASON_NO_COUNTS = "no_official_counts"
REASON_NO_EVALUABLE = "no_evaluable_counts"


def normalize_month(value: str | None) -> str | None:
    """Competência YYYY-MM → (period_start, period_end_exclusive) em YYYYMMDD."""
    if value is None:
        return None
    text = str(value).strip().replace("/", "-")
    if len(text) != 7 or text[4] != "-":
        raise ValueError("month must use the YYYY-MM format")
    year, month = text[:4], text[5:]
    if not (year.isdigit() and month.isdigit()):
        raise ValueError("month must use the YYYY-MM format")
    m = int(month)
    if m < 1 or m > 12:
        raise ValueError("month must use the YYYY-MM format")
    return f"{year}{month}"


def month_period(competence: str) -> tuple[str, str, str]:
    """'2026-09' → ('20260901', '20261001', '2026-09')."""
    yyyymm = normalize_month(competence)
    if yyyymm is None:
        raise ValueError("month must use the YYYY-MM format")
    year, month = int(yyyymm[:4]), int(yyyymm[4:])
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return (
        date(year, month, 1).strftime("%Y%m%d"),
        end.strftime("%Y%m%d"),
        f"{year:04d}-{month:02d}",
    )


def month_from_closing(closing_date: str) -> str:
    """'20260930' → '2026-09'."""
    return f"{closing_date[:4]}-{closing_date[4:6]}"


@dataclass(frozen=True)
class AccuracyPeriod:
    period_start: str  # YYYYMMDD inclusive
    period_end_exclusive: str  # YYYYMMDD exclusive
    reference_month: str | None  # 'YYYY-MM' quando período = mês calendário
    kind: str  # 'last_closed_month' | 'month' | 'custom_period'
    closed: bool


def resolve_accuracy_period(
    *,
    month: str | None,
    start_date: str | None,
    end_date: str | None,
    last_closing_date: str | None,
) -> AccuracyPeriod:
    """Período de referência — padrão: último mês calendário fechado (SB9).

    month=YYYY-MM → mês calendário. start/end custom → intervalo
    [start, end] inclusive. Sem parâmetros → mês do último fechamento SB9.
    """
    if month:
        start, end, ref = month_period(month)
        closed = (
            last_closing_date is not None and last_closing_date >= end
        ) or False
        return AccuracyPeriod(start, end, ref, "month", closed)
    if start_date or end_date:
        if not (start_date and end_date):
            raise ValueError(
                "start_date and end_date must be provided together"
            )
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")
        end_ex = _next_day(end_date)
        return AccuracyPeriod(
            start_date, end_ex, None, "custom_period",
            closed=(last_closing_date is not None
                    and last_closing_date >= end_ex),
        )
    if last_closing_date:
        start, end, ref = month_period(month_from_closing(last_closing_date))
        return AccuracyPeriod(start, end, ref, "last_closed_month", True)
    raise ValueError("no closed inventory period available")


def _next_day(yyyymmdd: str) -> str:
    d = date(int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
    return d.fromordinal(d.toordinal() + 1).strftime("%Y%m%d")


def classify_event(
    *,
    count_status: str | None,
    has_adjustment: bool,
) -> tuple[str, str | None]:
    """(outcome, exclusion_reason) por evento de contagem."""
    st = (count_status or "").strip()
    if st != STATUS_PROCESSED:
        return OUTCOME_EXCLUDED, REASON_PENDING_PROCESSING
    if has_adjustment:
        return OUTCOME_DIVERGENT, None
    return OUTCOME_ACCURATE, None


def theoretical_quantity(
    *,
    counted: float,
    shortage_quantity: float,
    surplus_quantity: float,
) -> float:
    """teórico = contado + furo(RE0) - sobra(DE0)."""
    return counted + shortage_quantity - surplus_quantity


def accuracy_percentage(accurate: int, evaluable: int) -> float | None:
    if evaluable <= 0:
        return None
    return round(accurate * 100.0 / evaluable, 2)


def summarize_availability(
    *, valid_count: int, evaluable_count: int
) -> tuple[str, str | None]:
    if valid_count <= 0:
        return "unavailable", REASON_NO_COUNTS
    if evaluable_count <= 0:
        return "unavailable", REASON_NO_EVALUABLE
    return "ok", None
