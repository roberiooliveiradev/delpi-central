"""SQL da série de faturamento da carteira — bucket conforme granularidade."""

from __future__ import annotations

BILLING_SERIES_GRANULARITIES = ("day", "week", "month", "year")

_ISSUE_YYYYMMDD = "LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 8)"
_ISSUE_DATE = f"CONVERT(DATE, {_ISSUE_YYYYMMDD}, 112)"


def billing_series_period_expr(granularity: str) -> str:
    """Expressão SQL Server do bucket (YYYYMMDD / YYYYMM / YYYY)."""
    grain = (granularity or "month").strip().lower()
    if grain not in BILLING_SERIES_GRANULARITIES:
        raise ValueError("granularity deve ser day, week, month ou year")
    if grain == "day":
        return _ISSUE_YYYYMMDD
    if grain == "week":
        # Segunda-feira ISO como YYYYMMDD. 1900-01-01 foi segunda.
        return (
            "CONVERT(VARCHAR(8), DATEADD(DAY, "
            f"-(DATEDIFF(DAY, '19000101', {_ISSUE_DATE}) % 7), {_ISSUE_DATE}), 112)"
        )
    if grain == "year":
        return f"LEFT({_ISSUE_YYYYMMDD}, 4)"
    return f"LEFT({_ISSUE_YYYYMMDD}, 6)"


def build_customer_billing_series_sql(*, where_pairs: str, granularity: str) -> str:
    period_expr = billing_series_period_expr(granularity)
    return f"""
            WITH note_base AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    D2.D2_FILIAL AS branch,
                    D2.D2_DOC AS invoice_number,
                    D2.D2_SERIE AS invoice_series,
                    MAX(D2.D2_EMISSAO) AS issue_date,
                    MAX(CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))) AS note_value,
                    MAX(ISNULL(F2.F2_TIPO, D2.D2_TIPO)) AS doc_type
                  FROM SD2010 D2 WITH (NOLOCK)
                  INNER JOIN SF2010 F2 WITH (NOLOCK)
                    ON F2.F2_FILIAL = D2.D2_FILIAL
                   AND F2.F2_DOC = D2.D2_DOC
                   AND F2.F2_SERIE = D2.D2_SERIE
                   AND F2.D_E_L_E_T_ = ''
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({where_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                 GROUP BY
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    D2.D2_FILIAL,
                    D2.D2_DOC,
                    D2.D2_SERIE
            )
            SELECT
                {period_expr} AS year_month,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        ELSE note_value
                    END
                ) AS billed_value
              FROM note_base
             GROUP BY {period_expr}
             ORDER BY year_month ASC
        """
