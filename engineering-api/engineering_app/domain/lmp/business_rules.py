"""Regras R01–R06 do domínio LMP — owner: Engineering API (doc 33 §2).

Portado de `api-delpi/app/application/services/lmp_business_rules.py`
conforme `lmp_semantics.v1.yaml` (R01–R05 `reference_only` → aqui viram a
execução oficial; R06 = interpretação de `engineering_status` no uso).

Não usar em payload HTTP sem serialização na borda — `data_limite` é
emita em YYYYMMDD por paridade com o contrato legado do dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from engineering_app.domain.lmp.dates import (
    add_business_days,
    business_days_between,
    format_date_ymd,
    parse_date,
)

SLA_BY_LEVEL = {
    "Nível 1": 4,
    "Nível 2": 8,
    "Nível 3": 20,
}

HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY * 60
SLA_TOLERANCE_DAYS = 1

ENGINEERING_STATUS_FINISHED = "FINALIZADA"
ENGINEERING_STATUS_IN_PROGRESS = "EM_ANDAMENTO"
ENGINEERING_STATUS_PARTIAL = "PARCIAL"
ENGINEERING_STATUS_RETURNED = "RETORNADA"

DASHBOARD_STATUS_ON_TIME = "Pontual"
DASHBOARD_STATUS_LATE = "Atrasado"
DASHBOARD_STATUS_IN_PROGRESS = "Andamento"
DASHBOARD_STATUS_RETURNED = "Retornada"

DASHBOARD_STATUS_VALUES = (
    DASHBOARD_STATUS_ON_TIME,
    DASHBOARD_STATUS_LATE,
    DASHBOARD_STATUS_IN_PROGRESS,
    DASHBOARD_STATUS_RETURNED,
)


def normalize_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def get_level(qtd_pi: Optional[int]) -> str:
    """R02 — proxy de complexidade por contagem de PI."""
    value = qtd_pi or 0
    if value <= 10:
        return "Nível 1"
    if value <= 20:
        return "Nível 2"
    return "Nível 3"


def get_sla_days(level: str) -> int:
    """R01 — SLA em dias úteis por nível."""
    return SLA_BY_LEVEL[level]


def get_sla_minutes(level: str) -> int:
    return get_sla_days(level) * MINUTES_PER_DAY


def get_sla_limit_minutes(level: str) -> int:
    """R03 — SLA + 1 dia útil de tolerância, em minutos."""
    return get_sla_minutes(level) + SLA_TOLERANCE_DAYS * MINUTES_PER_DAY


def get_sla_limit_date(start_date: Optional[date], level: str) -> Optional[date]:
    """R01+R03+R05 — data limite com tolerância em dias úteis."""
    if not start_date:
        return None
    base_limit = add_business_days(start_date, get_sla_days(level))
    return add_business_days(base_limit, SLA_TOLERANCE_DAYS)


def is_engineering_finished(engineering_status: Optional[str]) -> bool:
    return normalize_string(engineering_status) == ENGINEERING_STATUS_FINISHED


def is_engineering_returned(engineering_status: Optional[str]) -> bool:
    return normalize_string(engineering_status) == ENGINEERING_STATUS_RETURNED


def is_engineering_in_progress(engineering_status: Optional[str]) -> bool:
    return normalize_string(engineering_status) in {
        ENGINEERING_STATUS_IN_PROGRESS,
        "ABERTA",
    }


def is_engineering_partial(engineering_status: Optional[str]) -> bool:
    return normalize_string(engineering_status) == ENGINEERING_STATUS_PARTIAL


def matches_engineering_status_filter(
    engineering_status: Optional[str],
    filter_status: Optional[str],
) -> bool:
    normalized_status = normalize_string(engineering_status)
    normalized_filter = normalize_string(filter_status)
    if not normalized_filter:
        return True
    return normalized_status == normalized_filter


def resolve_dashboard_status(
    *,
    start_date_str: object,
    end_date_str: object,
    qtd_pi: Optional[int],
    engineering_status: Optional[str] = None,
    engineering_total_minutes: Optional[int] = None,
) -> str:
    """R04 — classificação Pontual/Atrasado/Andamento/Retornada.

    Pontualidade por `OR` data×minutos (semântica sutil da spec):
    FINALIZADA é Pontual se `end_date <= limite+tolerância` OU
    `engineering_total_minutes <= limite_minutos+tolerância`.
    """
    if is_engineering_returned(engineering_status):
        return DASHBOARD_STATUS_RETURNED

    if not is_engineering_finished(engineering_status):
        return DASHBOARD_STATUS_IN_PROGRESS

    level = get_level(qtd_pi)
    sla_limit_minutes = get_sla_limit_minutes(level)
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    limit_with_tolerance = get_sla_limit_date(start_date, level)
    total_minutes = int(engineering_total_minutes or 0)

    within_date_limit = (
        end_date is not None
        and limit_with_tolerance is not None
        and end_date <= limit_with_tolerance
    )
    within_minutes_limit = total_minutes <= sla_limit_minutes

    return (
        DASHBOARD_STATUS_ON_TIME
        if (within_date_limit or within_minutes_limit)
        else DASHBOARD_STATUS_LATE
    )


@dataclass(frozen=True)
class DashboardComputedFields:
    """R08 — campos calculados do item de dashboard (paridade legada)."""

    level: str
    sla_days: int
    sla_minutes: int
    data_limite: Optional[str]  # YYYYMMDD — contrato legado
    lead_time_util: Optional[int]
    status: str


def compute_dashboard_fields(
    *,
    start_date_str: object,
    end_date_str: object,
    qtd_pi: Optional[int],
    engineering_status: Optional[str] = None,
    engineering_total_minutes: Optional[int] = None,
) -> DashboardComputedFields:
    """Composição R01–R05 equivalente a `get_dashboard_status` legada."""
    level = get_level(qtd_pi)
    sla_days = get_sla_days(level)
    sla_minutes = get_sla_minutes(level)

    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)

    data_limite = add_business_days(start_date, sla_days) if start_date else None
    lead_time_util = (
        business_days_between(start_date, end_date)
        if start_date and end_date
        else None
    )
    status = resolve_dashboard_status(
        start_date_str=start_date_str,
        end_date_str=end_date_str,
        qtd_pi=qtd_pi,
        engineering_status=engineering_status,
        engineering_total_minutes=engineering_total_minutes,
    )

    return DashboardComputedFields(
        level=level,
        sla_days=sla_days,
        sla_minutes=sla_minutes,
        data_limite=format_date_ymd(data_limite),
        lead_time_util=lead_time_util,
        status=status,
    )
