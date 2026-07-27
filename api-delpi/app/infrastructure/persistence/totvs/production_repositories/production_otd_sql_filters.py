"""Predicados SQL canônicos do OTD de produção (SC2010).

Universo:
- OP finalizada (C2_DATRF preenchido), ou
- OP em andamento já atrasada (C2_DATRF vazio e C2_DATPRF < hoje).

Assim o indicador não mascara atraso enquanto a OP não é apontada como finalizada.
"""

from __future__ import annotations


def sc2_finish_date_empty_sql(alias: str = "OP") -> str:
    col = f"{alias}.C2_DATRF" if alias else "C2_DATRF"
    return f"({col} IS NULL OR LTRIM(RTRIM({col})) = '')"


def sc2_finish_date_filled_sql(alias: str = "OP") -> str:
    col = f"{alias}.C2_DATRF" if alias else "C2_DATRF"
    return f"({col} IS NOT NULL AND LTRIM(RTRIM({col})) <> '')"


def sc2_due_date_col(alias: str = "OP") -> str:
    return f"{alias}.C2_DATPRF" if alias else "C2_DATPRF"


def sc2_finish_date_col(alias: str = "OP") -> str:
    return f"{alias}.C2_DATRF" if alias else "C2_DATRF"


def sc2_open_overdue_sql(alias: str = "OP") -> str:
    due = sc2_due_date_col(alias)
    return f"""(
    {sc2_finish_date_empty_sql(alias)}
    AND CONVERT(DATE, {due}, 112) < CONVERT(DATE, GETDATE())
)"""


def sc2_otd_universe_sql(alias: str = "OP") -> str:
    """Finalizada OU em andamento com due date já vencida."""
    return f"""(
    {sc2_finish_date_filled_sql(alias)}
    OR {sc2_open_overdue_sql(alias)}
)"""


def sc2_otd_on_time_sql(alias: str = "OP") -> str:
    due = sc2_due_date_col(alias)
    finish = sc2_finish_date_col(alias)
    return f"""(
    {sc2_finish_date_filled_sql(alias)}
    AND CONVERT(DATE, {finish}, 112) <= CONVERT(DATE, {due}, 112)
)"""


def sc2_otd_late_sql(alias: str = "OP") -> str:
    """Atraso: finalizada após o due date, ou aberta com due já vencido."""
    return f"(NOT {sc2_otd_on_time_sql(alias)})"


def sc2_otd_status_case_sql(alias: str = "OP") -> str:
    """Classificação: on_time | late | open (aberta ainda dentro do prazo)."""
    due = sc2_due_date_col(alias)
    finish = sc2_finish_date_col(alias)
    return f"""CASE
    WHEN {sc2_finish_date_empty_sql(alias)}
         AND CONVERT(DATE, {due}, 112) < CONVERT(DATE, GETDATE())
    THEN 'late'
    WHEN {sc2_finish_date_empty_sql(alias)}
    THEN 'open'
    WHEN CONVERT(DATE, {finish}, 112) <= CONVERT(DATE, {due}, 112)
    THEN 'on_time'
    ELSE 'late'
END"""


def sc2_otd_finish_date_select_sql(alias: str = "OP") -> str:
    finish = sc2_finish_date_col(alias)
    return f"""CASE
    WHEN {sc2_finish_date_empty_sql(alias)}
    THEN NULL
    ELSE CONVERT(VARCHAR(10), CONVERT(DATE, {finish}, 112), 23)
END"""


def sc2_otd_days_diff_select_sql(alias: str = "OP") -> str:
    """Dias de atraso/adiantamento; OP aberta usa hoje como referência."""
    due = sc2_due_date_col(alias)
    finish = sc2_finish_date_col(alias)
    return f"""CASE
    WHEN {sc2_finish_date_empty_sql(alias)}
    THEN DATEDIFF(DAY, CONVERT(DATE, {due}, 112), CONVERT(DATE, GETDATE()))
    ELSE DATEDIFF(DAY, CONVERT(DATE, {due}, 112), CONVERT(DATE, {finish}, 112))
END"""
