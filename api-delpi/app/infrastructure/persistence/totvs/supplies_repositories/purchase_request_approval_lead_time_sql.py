"""Read-only SCR010 approval lead time. HD #1004 / SUP-004.

SC1010 supplies the request issue date and current item statuses ONLY.
The *sole* approval-event authority is SCR010 (CR_TIPO=SC, CR_STATUS=03).
Never infer an approval timestamp from C1_APROV or polling snapshots.
"""

from __future__ import annotations

from datetime import date

from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
MAX_WINDOW_DAYS = 366


def normalize_lead_time_filters(
    *,
    branches: list[str] | None,
    date_from: str | None,
    date_to: str | None,
    request_number: str | None = None,
) -> tuple[list[str], str, str, str | None]:
    """Fail closed on missing/invalid unit, dates and document numbers."""
    if not branches:
        raise ValueError("Selecione ao menos uma filial (01 ou 02).")
    requested = {str(value or "").strip() for value in branches}
    if not requested or not requested.issubset(set(PROTHEUS_BRANCH_CODES)):
        raise ValueError("Filial inválida; use somente 01 e/ou 02.")
    normalized = [code for code in PROTHEUS_BRANCH_CODES if code in requested]
    today = date.today()
    try:
        start = date.fromisoformat(date_from) if date_from else date(today.year, 1, 1)
        end = date.fromisoformat(date_to) if date_to else today
    except (ValueError, TypeError) as exc:
        raise ValueError("Datas inválidas. Use AAAA-MM-DD.") from exc
    if start > end or (end - start).days > MAX_WINDOW_DAYS:
        raise ValueError("O período deve ser crescente e ter no máximo 367 dias.")
    number = (request_number or "").strip() or None
    if number is not None and (not number.isdigit() or len(number) > 16):
        raise ValueError("Número da SC inválido.")
    return normalized, start.isoformat(), end.isoformat(), number


def build_lead_time_filter(
    *,
    branches: list[str],
    date_from: str,
    date_to: str,
    request_number: str | None = None,
) -> tuple[str, list[str]]:
    placeholders = ", ".join("?" for _ in branches)
    clause = (
        f"SC1.C1_FILIAL IN ({placeholders}) "
        "AND SC1.C1_EMISSAO >= ? AND SC1.C1_EMISSAO <= ? "
        "AND SC1.D_E_L_E_T_ = ''"
    )
    params = [*branches, date_from.replace("-", ""), date_to.replace("-", "")]
    if request_number:
        clause += " AND RTRIM(SC1.C1_NUM) = ?"
        params.append(request_number)
    return clause, params


def _eligible_cte(where_clause: str) -> str:
    """One row per (branch, SC); duplicate group entries never multiply KPIs."""
    return f"""
WITH request_headers AS (
    SELECT
        RTRIM(SC1.C1_FILIAL) AS branch,
        RTRIM(SC1.C1_NUM) AS request_number,
        MIN(TRY_CONVERT(date, NULLIF(RTRIM(SC1.C1_EMISSAO), ''), 112)) AS issue_date,
        MIN(NULLIF(RTRIM(SC1.C1_SOLICIT), '')) AS requester_name,
        MIN(NULLIF(RTRIM(SC1.C1_USER), '')) AS requester_user_id,
        COUNT(*) AS item_count,
        SUM(CASE WHEN RTRIM(SC1.C1_APROV) = 'L' THEN 0 ELSE 1 END) AS unapproved_items,
        SUM(CASE WHEN TRY_CONVERT(date, NULLIF(RTRIM(SC1.C1_EMISSAO), ''), 112)
                      IS NULL THEN 1 ELSE 0 END) AS invalid_issue_items
    FROM SC1010 SC1 WITH (NOLOCK)
    WHERE {where_clause}
    GROUP BY RTRIM(SC1.C1_FILIAL), RTRIM(SC1.C1_NUM)
),
approval_history AS (
    SELECT
        RTRIM(SCR.CR_FILIAL) AS branch,
        RTRIM(SCR.CR_NUM) AS request_number,
        MAX(CASE WHEN RTRIM(SCR.CR_STATUS) = '03'
                 THEN TRY_CONVERT(date, NULLIF(RTRIM(SCR.CR_DATALIB), ''), 112)
                 END) AS final_approval_date,
        COUNT(DISTINCT CASE WHEN RTRIM(SCR.CR_STATUS) = '03'
                            THEN RTRIM(SCR.CR_NIVEL) END) AS approval_levels,
        SUM(CASE WHEN RTRIM(SCR.CR_STATUS) = '03'
                  AND TRY_CONVERT(date, NULLIF(RTRIM(SCR.CR_DATALIB), ''), 112) IS NOT NULL
                  AND NULLIF(RTRIM(SCR.CR_USERLIB), '') IS NOT NULL
                  AND NULLIF(RTRIM(SCR.CR_LIBAPRO), '') IS NOT NULL
                 THEN 0 ELSE 1 END) AS unproven_entries
    FROM SCR010 SCR WITH (NOLOCK)
    WHERE SCR.D_E_L_E_T_ = '' AND SCR.CR_TIPO = 'SC'
    GROUP BY RTRIM(SCR.CR_FILIAL), RTRIM(SCR.CR_NUM)
),
eligible AS (
    SELECT
        SC.branch,
        SC.request_number,
        SC.issue_date,
        SC.requester_name,
        SC.requester_user_id,
        SC.item_count,
        AP.final_approval_date,
        AP.approval_levels,
        DATEDIFF(day, SC.issue_date, AP.final_approval_date) AS lead_days
    FROM request_headers SC
    JOIN approval_history AP
      ON AP.branch = SC.branch AND AP.request_number = SC.request_number
    WHERE SC.unapproved_items = 0
      AND SC.invalid_issue_items = 0
      AND AP.unproven_entries = 0
      AND AP.approval_levels > 0
      AND AP.final_approval_date >= SC.issue_date
)
"""


def build_lead_time_summary_sql(where_clause: str) -> str:
    return _eligible_cte(where_clause) + """
SELECT
    COUNT(*) AS total_requests,
    CAST(AVG(CAST(lead_days AS decimal(18, 2))) AS decimal(12, 2)) AS avg_lead_days,
    SUM(CASE WHEN lead_days = 0 THEN 1 ELSE 0 END) AS same_day,
    SUM(CASE WHEN lead_days BETWEEN 1 AND 2 THEN 1 ELSE 0 END) AS one_to_two_days,
    SUM(CASE WHEN lead_days BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS three_to_five_days,
    SUM(CASE WHEN lead_days > 10 THEN 1 ELSE 0 END) AS over_10_days,
    SUM(CASE WHEN approval_levels > 1 THEN 1 ELSE 0 END) AS multi_level
FROM eligible
"""


def build_lead_time_page_sql(where_clause: str) -> str:
    return _eligible_cte(where_clause) + """
SELECT
    branch, request_number,
    CONVERT(varchar(10), issue_date, 23) AS issue_date,
    requester_name, requester_user_id, item_count,
    CONVERT(varchar(10), final_approval_date, 23) AS final_approval_date,
    approval_levels, lead_days
FROM eligible
ORDER BY final_approval_date DESC, branch, request_number DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


def build_lead_time_events_sql(
    keys: list[tuple[str, str]],
) -> tuple[str, list[str]]:
    """Batch details for the page only, deduplicated across SCR groups."""
    if not keys or len(keys) > MAX_PAGE_SIZE:
        raise ValueError("Página sem SCs ou maior que o limite permitido.")
    clauses = ["(RTRIM(SCR.CR_FILIAL) = ? AND RTRIM(SCR.CR_NUM) = ?)" for _ in keys]
    params = [value for key in keys for value in key]
    sql = f"""
SELECT DISTINCT
    RTRIM(SCR.CR_FILIAL) AS branch,
    RTRIM(SCR.CR_NUM) AS request_number,
    RTRIM(SCR.CR_NIVEL) AS level,
    CONVERT(varchar(10), TRY_CONVERT(date, SCR.CR_DATALIB, 112), 23) AS approved_at,
    RTRIM(SCR.CR_USERLIB) AS action_user_code,
    RTRIM(SCR.CR_LIBAPRO) AS approver_code
FROM SCR010 SCR WITH (NOLOCK)
WHERE SCR.D_E_L_E_T_ = ''
  AND SCR.CR_TIPO = 'SC'
  AND SCR.CR_STATUS = '03'
  AND ({' OR '.join(clauses)})
ORDER BY branch, request_number, level, approved_at, approver_code
"""
    return sql, params
