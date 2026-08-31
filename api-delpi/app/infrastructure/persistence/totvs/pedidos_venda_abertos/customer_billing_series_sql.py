"""SQL da série / enrichment de faturamento da carteira (gross NF ou net ROL)."""

from __future__ import annotations

from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)

BILLING_SERIES_GRANULARITIES = ("day", "week", "month", "year")
BILLING_NATURES = ("gross", "net")
DEFAULT_BILLING_NATURE = "gross"
SUPPORTED_BILLING_NATURES = list(BILLING_NATURES)

_ISSUE_YYYYMMDD = "LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 8)"
_ISSUE_DATE = f"CONVERT(DATE, {_ISSUE_YYYYMMDD}, 112)"


def normalize_billing_nature(value: str | None) -> str:
    nature = (value or DEFAULT_BILLING_NATURE).strip().lower() or DEFAULT_BILLING_NATURE
    if nature not in BILLING_NATURES:
        raise ValueError("nature inválida. Use gross ou net.")
    return nature


def billing_series_period_expr(granularity: str) -> str:
    """Expressão SQL Server do bucket (YYYYMMDD / YYYYMM / YYYY)."""
    grain = (granularity or "month").strip().lower()
    if grain not in BILLING_SERIES_GRANULARITIES:
        raise ValueError("granularity deve ser day, week, month ou year")
    if grain == "day":
        return _ISSUE_YYYYMMDD
    if grain == "week":
        return (
            "CONVERT(VARCHAR(8), DATEADD(DAY, "
            f"-(DATEDIFF(DAY, '19000101', {_ISSUE_DATE}) % 7), {_ISSUE_DATE}), 112)"
        )
    if grain == "year":
        return f"LEFT({_ISSUE_YYYYMMDD}, 4)"
    return f"LEFT({_ISSUE_YYYYMMDD}, 6)"


def _period_expr_from_protheus_col(col: str, granularity: str) -> str:
    """Bucket a partir de coluna data Protheus YYYYMMDD (D2_EMISSAO / D1_DTDIGIT)."""
    ymd = f"LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), {col}))), 8)"
    grain = (granularity or "month").strip().lower()
    if grain == "day":
        return ymd
    if grain == "week":
        as_date = f"CONVERT(DATE, {ymd}, 112)"
        return (
            "CONVERT(VARCHAR(8), DATEADD(DAY, "
            f"-(DATEDIFF(DAY, '19000101', {as_date}) % 7), {as_date}), 112)"
        )
    if grain == "year":
        return f"LEFT({ymd}, 4)"
    return f"LEFT({ymd}, 6)"


def build_customer_billing_series_sql(
    *,
    where_pairs: str,
    granularity: str,
    nature: str = DEFAULT_BILLING_NATURE,
) -> str:
    nature = normalize_billing_nature(nature)
    if nature == "gross":
        return _build_gross_series_sql(where_pairs=where_pairs, granularity=granularity)
    return _build_net_series_sql(where_pairs=where_pairs, granularity=granularity)


def _build_gross_series_sql(*, where_pairs: str, granularity: str) -> str:
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


def _build_net_series_sql(*, where_pairs: str, granularity: str) -> str:
    """ROL líquido por bucket: vendas (D2_EMISSAO) − devoluções (D1_DTDIGIT)."""
    sale_period = _period_expr_from_protheus_col("D2.D2_EMISSAO", granularity)
    ret_period = _period_expr_from_protheus_col("D1.D1_DTDIGIT", granularity)
    exists_where = "D1X.D1_DTDIGIT >= ? AND D1X.D1_DTDIGIT <= ?"
    d2_pairs = where_pairs
    d1_pairs = where_pairs.replace("D2.D2_CLIENTE", "D1.D1_FORNECE").replace(
        "D2.D2_LOJA", "D1.D1_LOJA"
    )
    net_sale = CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")
    net_ret = CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")
    eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
        exists_where=exists_where,
    )
    return f"""
            WITH vendas AS (
                SELECT
                    {sale_period} AS year_month,
                    {net_sale} AS billed_value
                  FROM SD2010 D2 WITH (NOLOCK)
                  {CommercialRolReturnSql.sale_customer_join(with_nolock=True)}
                  {CommercialRolReturnSql.sale_tes_join(with_nolock=True)}
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({d2_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                   AND {eligibility}
                 GROUP BY {sale_period}
            ),
            devolucoes AS (
                SELECT
                    {ret_period} AS year_month,
                    {net_ret} AS billed_value
                  FROM SD1010 D1 WITH (NOLOCK)
                  {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                 WHERE D1.D_E_L_E_T_ = ''
                   AND ({d1_pairs})
                   AND D1.D1_DTDIGIT >= ?
                   AND D1.D1_DTDIGIT <= ?
                   AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                 GROUP BY {ret_period}
            )
            SELECT
                ISNULL(V.year_month, D.year_month) AS year_month,
                ISNULL(V.billed_value, 0) - ISNULL(D.billed_value, 0) AS billed_value
              FROM vendas V
              FULL OUTER JOIN devolucoes D
                ON D.year_month = V.year_month
             ORDER BY year_month ASC
        """


def build_customer_billing_12m_sql(
    *,
    where_pairs: str,
    nature: str = DEFAULT_BILLING_NATURE,
) -> str:
    nature = normalize_billing_nature(nature)
    if nature == "gross":
        return _build_gross_12m_sql(where_pairs=where_pairs)
    return _build_net_12m_sql(where_pairs=where_pairs)


def _build_gross_12m_sql(*, where_pairs: str) -> str:
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
                customer_code,
                customer_store,
                MAX(issue_date) AS last_purchase_date,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        ELSE note_value
                    END
                ) AS billed_12m,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        WHEN issue_date >= ? THEN note_value
                        ELSE 0
                    END
                ) AS billed_recent_6m,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        WHEN issue_date < ? THEN note_value
                        ELSE 0
                    END
                ) AS billed_prior_6m
              FROM note_base
             GROUP BY customer_code, customer_store
        """


def _build_net_12m_sql(*, where_pairs: str) -> str:
    exists_where = "D1X.D1_DTDIGIT >= ? AND D1X.D1_DTDIGIT <= ?"
    d2_pairs = where_pairs
    d1_pairs = where_pairs.replace("D2.D2_CLIENTE", "D1.D1_FORNECE").replace(
        "D2.D2_LOJA", "D1.D1_LOJA"
    )
    net_line = CommercialRolReturnSql.sale_net_line_expr(d2_alias="D2")
    ret_line = CommercialRolReturnSql.return_net_line_expr(d1_alias="D1")
    eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
        exists_where=exists_where,
    )
    return f"""
            WITH vendas AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    MAX(D2.D2_EMISSAO) AS last_purchase_date,
                    SUM(CONVERT(FLOAT, {net_line})) AS billed_12m,
                    SUM(CONVERT(FLOAT, CASE
                        WHEN D2.D2_EMISSAO >= ? THEN {net_line} ELSE 0 END)) AS billed_recent_6m,
                    SUM(CONVERT(FLOAT, CASE
                        WHEN D2.D2_EMISSAO < ? THEN {net_line} ELSE 0 END)) AS billed_prior_6m
                  FROM SD2010 D2 WITH (NOLOCK)
                  {CommercialRolReturnSql.sale_customer_join(with_nolock=True)}
                  {CommercialRolReturnSql.sale_tes_join(with_nolock=True)}
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({d2_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                   AND {eligibility}
                 GROUP BY D2.D2_CLIENTE, D2.D2_LOJA
            ),
            devolucoes AS (
                SELECT
                    D1.D1_FORNECE AS customer_code,
                    D1.D1_LOJA AS customer_store,
                    SUM(CONVERT(FLOAT, {ret_line})) AS billed_12m,
                    SUM(CONVERT(FLOAT, CASE
                        WHEN D1.D1_DTDIGIT >= ? THEN {ret_line} ELSE 0 END)) AS billed_recent_6m,
                    SUM(CONVERT(FLOAT, CASE
                        WHEN D1.D1_DTDIGIT < ? THEN {ret_line} ELSE 0 END)) AS billed_prior_6m
                  FROM SD1010 D1 WITH (NOLOCK)
                  {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                 WHERE D1.D_E_L_E_T_ = ''
                   AND ({d1_pairs})
                   AND D1.D1_DTDIGIT >= ?
                   AND D1.D1_DTDIGIT <= ?
                   AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                 GROUP BY D1.D1_FORNECE, D1.D1_LOJA
            )
            SELECT
                ISNULL(V.customer_code, D.customer_code) AS customer_code,
                ISNULL(V.customer_store, D.customer_store) AS customer_store,
                V.last_purchase_date AS last_purchase_date,
                ISNULL(V.billed_12m, 0) - ISNULL(D.billed_12m, 0) AS billed_12m,
                ISNULL(V.billed_recent_6m, 0) - ISNULL(D.billed_recent_6m, 0) AS billed_recent_6m,
                ISNULL(V.billed_prior_6m, 0) - ISNULL(D.billed_prior_6m, 0) AS billed_prior_6m
              FROM vendas V
              FULL OUTER JOIN devolucoes D
                ON D.customer_code = V.customer_code
               AND D.customer_store = V.customer_store
        """


def billing_12m_params(
    *,
    pair_params: list[str],
    start_date: str,
    mid_date: str,
    end_date: str,
    nature: str,
) -> tuple:
    """Parâmetros bind alinhados a ``build_customer_billing_12m_sql`` (ordem dos ``?``)."""
    nature = normalize_billing_nature(nature)
    if nature == "gross":
        return tuple(pair_params + [start_date, end_date, mid_date, mid_date])
    # net vendas: mid/mid (CASE) + pairs + start/end + exists start/end
    # net devoluções: mid/mid (CASE) + pairs + start/end
    return tuple(
        [mid_date, mid_date]
        + pair_params
        + [start_date, end_date, start_date, end_date]
        + [mid_date, mid_date]
        + pair_params
        + [start_date, end_date]
    )


def billing_series_params(
    *,
    pair_params: list[str],
    start_date: str,
    end_date: str,
    nature: str,
) -> tuple:
    nature = normalize_billing_nature(nature)
    if nature == "gross":
        return tuple(pair_params + [start_date, end_date])
    # net: vendas pairs+start/end+exists start/end; devolucoes pairs+start/end
    return tuple(
        pair_params
        + [start_date, end_date, start_date, end_date]
        + pair_params
        + [start_date, end_date]
    )
