"""GLPI #635: dias entre liberação comprovada da SC e emissão do primeiro PC.

SCR010 é a fonte do último evento válido de aprovação. SC1010 prova o estado
atual da solicitação; SC7010 vincula os PCs pelos itens da SC.
"""

from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_sql import (
    normalize_lead_time_filters,
)

PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def build_conversion_cohort(
    *, branches: list[str] | None, date_from: str | None,
    date_to: str | None, request_number: str | None = None,
) -> tuple[str, list[str], dict]:
    codes, start, end, number = normalize_lead_time_filters(
        branches=branches, date_from=date_from,
        date_to=date_to, request_number=request_number,
    )
    placeholders = ", ".join("?" for _ in codes)
    # Restrict the cohort at the indexed approval ledger before reading SC/PC.
    # Without this filter, a 2026 request may join the ENTIRE historical SC/SCR
    # population and repeat the expensive work for summary + page.
    filters = "SC1.D_E_L_E_T_ = '' AND SC1.C1_EMISSAO <= ?"
    params = [*codes, start.replace("-", ""), end.replace("-", ""),
              end.replace("-", "")]
    if number:
        filters += " AND SC1.C1_NUM = ?"
        params.append(number)
    # Final date guard is mandatory: a later reapproval must not leak into a
    # prior reporting period just because one earlier approval matched.
    params += [start.replace("-", ""), end.replace("-", "")]
    sql = f"""
WITH release_candidates AS (
    SELECT SCR.CR_FILIAL AS branch, SCR.CR_NUM AS request_number
    FROM SCR010 SCR WITH (NOLOCK)
    WHERE SCR.D_E_L_E_T_ = '' AND SCR.CR_TIPO = 'SC'
      AND SCR.CR_STATUS = '03'
      AND SCR.CR_FILIAL IN ({placeholders})
      AND SCR.CR_DATALIB >= ? AND SCR.CR_DATALIB <= ?
    GROUP BY SCR.CR_FILIAL, SCR.CR_NUM
),
request_headers AS (
    SELECT RTRIM(SC1.C1_FILIAL) AS branch,
           RTRIM(SC1.C1_NUM) AS request_number,
           MIN(TRY_CONVERT(date, NULLIF(RTRIM(SC1.C1_EMISSAO), ''), 112)) AS issue_date,
           COUNT(*) AS item_count,
           SUM(CASE WHEN RTRIM(SC1.C1_APROV) = 'L' THEN 0 ELSE 1 END) AS unapproved_items,
           SUM(CASE WHEN TRY_CONVERT(date, NULLIF(RTRIM(SC1.C1_EMISSAO), ''), 112)
                         IS NULL THEN 1 ELSE 0 END) AS invalid_issue_items
    FROM release_candidates C
    INNER JOIN SC1010 SC1 WITH (NOLOCK)
      ON SC1.C1_FILIAL = C.branch AND SC1.C1_NUM = C.request_number
    WHERE {filters}
    GROUP BY RTRIM(SC1.C1_FILIAL), RTRIM(SC1.C1_NUM)
),
approval_history AS (
    SELECT H.branch, H.request_number,
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
    INNER JOIN request_headers H
      ON SCR.CR_FILIAL = H.branch
     AND SCR.CR_NUM = H.request_number
    WHERE SCR.D_E_L_E_T_ = '' AND SCR.CR_TIPO = 'SC'
    GROUP BY H.branch, H.request_number
),
eligible_approved AS (
    SELECT H.branch, H.request_number, H.issue_date, H.item_count,
           AP.final_approval_date, AP.approval_levels
    FROM request_headers H
    INNER JOIN approval_history AP
      ON AP.branch = H.branch AND AP.request_number = H.request_number
    WHERE H.unapproved_items = 0 AND H.invalid_issue_items = 0
      AND AP.unproven_entries = 0 AND AP.approval_levels > 0
      AND AP.final_approval_date >= H.issue_date
      AND AP.final_approval_date BETWEEN
          TRY_CONVERT(date, ?, 112) AND TRY_CONVERT(date, ?, 112)
),
linked_orders AS (
    SELECT E.branch, E.request_number,
           NULLIF(RTRIM(C7.C7_NUM), '') AS order_number,
           TRY_CONVERT(date, NULLIF(RTRIM(C7.C7_EMISSAO), ''), 112) AS order_date
    FROM eligible_approved E
    INNER JOIN SC7010 C7 WITH (NOLOCK)
      ON C7.C7_FILIAL = E.branch
     AND C7.C7_NUMSC = E.request_number
     AND C7.D_E_L_E_T_ = ''
    WHERE EXISTS (
        SELECT 1 FROM SC1010 SC1 WITH (NOLOCK)
        WHERE SC1.D_E_L_E_T_ = ''
          AND SC1.C1_FILIAL = E.branch
          AND SC1.C1_NUM = E.request_number
          AND SC1.C1_ITEM = C7.C7_ITEMSC
    )
),
order_rollup AS (
    SELECT branch, request_number,
           COUNT(*) AS linked_lines,
           COUNT(DISTINCT order_number) AS linked_order_count,
           MIN(order_date) AS first_order_date,
           SUM(CASE WHEN order_date IS NULL OR order_number IS NULL
                    THEN 1 ELSE 0 END) AS invalid_order_lines
    FROM linked_orders
    GROUP BY branch, request_number
),
first_order AS (
    SELECT branch, request_number, order_number, order_date,
           ROW_NUMBER() OVER (
             PARTITION BY branch, request_number ORDER BY order_date, order_number
           ) AS rn
    FROM (
        SELECT DISTINCT branch, request_number, order_number, order_date
        FROM linked_orders
        WHERE order_date IS NOT NULL AND order_number IS NOT NULL
    ) D
),
assessed AS (
    SELECT E.branch, E.request_number, E.issue_date, E.item_count,
           E.final_approval_date, E.approval_levels,
           R.first_order_date, F.order_number AS first_order_number,
           COALESCE(R.linked_order_count, 0) AS linked_order_count,
           CASE WHEN R.linked_lines IS NULL THEN 'pending'
                WHEN R.invalid_order_lines > 0 OR R.first_order_date IS NULL
                  THEN 'invalid_order_date'
                WHEN R.first_order_date < E.final_approval_date
                  THEN 'order_before_release'
                ELSE 'converted' END AS conversion_status
    FROM eligible_approved E
    LEFT JOIN order_rollup R
      ON R.branch = E.branch AND R.request_number = E.request_number
    LEFT JOIN first_order F
      ON F.branch = E.branch AND F.request_number = E.request_number AND F.rn = 1
),
measured AS (
    SELECT A.*,
           CASE WHEN A.conversion_status = 'converted'
                THEN DATEDIFF(day, A.final_approval_date, A.first_order_date)
                ELSE NULL END AS conversion_days
    FROM assessed A
)
"""
    return sql, params, {
        "branches": codes, "date_from": start,
        "date_to": end, "request_number": number,
    }


def build_conversion_summary_sql(cte: str) -> str:
    return cte + """
SELECT CASE WHEN GROUPING(branch) = 1 THEN NULL ELSE branch END AS branch,
       COUNT(*) AS approved_requests,
       SUM(CASE WHEN conversion_status = 'converted' THEN 1 ELSE 0 END) AS converted_requests,
       SUM(CASE WHEN conversion_status = 'pending' THEN 1 ELSE 0 END) AS pending_requests,
       SUM(CASE WHEN conversion_status = 'order_before_release' THEN 1 ELSE 0 END) AS before_release,
       SUM(CASE WHEN conversion_status = 'invalid_order_date' THEN 1 ELSE 0 END) AS invalid_order_dates,
       CAST(AVG(CAST(conversion_days AS decimal(18, 2))) AS decimal(12, 2)) AS avg_days,
       SUM(CASE WHEN conversion_status = 'converted' THEN conversion_days ELSE 0 END) AS sum_conversion_days,
       SUM(CASE WHEN conversion_days = 0 THEN 1 ELSE 0 END) AS same_day,
       SUM(CASE WHEN conversion_days BETWEEN 1 AND 2 THEN 1 ELSE 0 END) AS one_to_two_days,
       SUM(CASE WHEN conversion_days BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS three_to_five_days,
       SUM(CASE WHEN conversion_days BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS six_to_ten_days,
       SUM(CASE WHEN conversion_days > 10 THEN 1 ELSE 0 END) AS over_ten_days
FROM measured
GROUP BY ROLLUP(branch)
"""


def build_conversion_page_sql(cte: str) -> str:
    return cte + """
SELECT branch, request_number,
       CONVERT(varchar(10), issue_date, 23) AS issue_date,
       CONVERT(varchar(10), final_approval_date, 23) AS final_approval_date,
       CONVERT(varchar(10), first_order_date, 23) AS first_order_date,
       first_order_number, linked_order_count, approval_levels, item_count,
       conversion_status, conversion_days
FROM measured
ORDER BY final_approval_date DESC, branch, request_number DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


def build_conversion_batch_sql(cte: str) -> str:
    """One SQL execution materializes the release cohort ONCE in a temp table.

    Only a session-local #temp table is created in tempdb, never ERP tables.
    Summary and page query that same materialization. SET NOCOUNT suppresses
    intermediate row-count resultsets for the existing pyodbc reader.
    """
    summary = build_conversion_summary_sql("").replace(
        "FROM measured", "FROM #sc_pc_conversion"
    )
    page = build_conversion_page_sql("").replace(
        "FROM measured", "FROM #sc_pc_conversion"
    )
    return (
        "SET NOCOUNT ON;\n"
        + cte
        + "\nSELECT * INTO #sc_pc_conversion FROM measured;\n"
        + summary
        + ";\n"
        + page
        + ";\nDROP TABLE #sc_pc_conversion;\n"
    )

