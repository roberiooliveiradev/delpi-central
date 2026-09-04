"""SQL da série / enrichment de faturamento da carteira (gross NF ou net ROL)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)

BILLING_SERIES_GRANULARITIES = ("day", "week", "month", "year")
BILLING_NATURES = ("gross", "net")
DEFAULT_BILLING_NATURE = "gross"
SUPPORTED_BILLING_NATURES = list(BILLING_NATURES)
BILLING_METRICS = ("value", "quantity")
DEFAULT_BILLING_METRIC = "value"
SUPPORTED_BILLING_METRICS = list(BILLING_METRICS)

_QTY_SALE_SUM = "SUM(CONVERT(FLOAT, ISNULL(D2.D2_QUANT, 0)))"
_QTY_RETURN_SUM = "SUM(CONVERT(FLOAT, ISNULL(D1.D1_QUANT, 0)))"
_UNIT_AGG_SALE = """
                CASE
                    WHEN COUNT(DISTINCT NULLIF(RTRIM(D2.D2_UM), '')) = 1
                    THEN MAX(NULLIF(RTRIM(D2.D2_UM), ''))
                    ELSE NULL
                END AS unit,
                CASE
                    WHEN COUNT(DISTINCT NULLIF(RTRIM(D2.D2_UM), '')) > 1 THEN 1
                    ELSE 0
                END AS mixed_units
"""
_UNIT_AGG_RETURN = """
                CASE
                    WHEN COUNT(DISTINCT NULLIF(RTRIM(D1.D1_UM), '')) = 1
                    THEN MAX(NULLIF(RTRIM(D1.D1_UM), ''))
                    ELSE NULL
                END AS unit,
                CASE
                    WHEN COUNT(DISTINCT NULLIF(RTRIM(D1.D1_UM), '')) > 1 THEN 1
                    ELSE 0
                END AS mixed_units
"""

_ISSUE_YYYYMMDD = "LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 8)"
_ISSUE_DATE = f"CONVERT(DATE, {_ISSUE_YYYYMMDD}, 112)"

_SB1_SALE_JOIN = """
                LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                    ON  SB1.D_E_L_E_T_ = ''
                    AND SB1.B1_COD = D2.D2_COD
"""
_SB1_RETURN_JOIN = """
                LEFT JOIN SB1010 SB1D WITH (NOLOCK)
                    ON  SB1D.D_E_L_E_T_ = ''
                    AND SB1D.B1_COD = D1.D1_COD
"""


@dataclass(frozen=True, slots=True)
class BillingSeriesRecorte:
    """Filtros de produto/família/mercado alinhados ao ROL by-product."""

    product_codes: tuple[str, ...] = ()
    product_groups: tuple[str, ...] = ()
    market: str | None = None

    @property
    def has_line_filters(self) -> bool:
        return bool(self.product_codes or self.product_groups or self.market)


def normalize_billing_nature(value: str | None) -> str:
    nature = (value or DEFAULT_BILLING_NATURE).strip().lower() or DEFAULT_BILLING_NATURE
    if nature not in BILLING_NATURES:
        raise ValueError("nature inválida. Use gross ou net.")
    return nature


def normalize_billing_metric(value: str | None) -> str:
    metric = (value or DEFAULT_BILLING_METRIC).strip().lower() or DEFAULT_BILLING_METRIC
    if metric not in BILLING_METRICS:
        raise ValueError("metric inválida. Use value ou quantity.")
    return metric


def normalize_billing_series_recorte(
    *,
    product_codes: list[str] | tuple[str, ...] | None = None,
    product_groups: list[str] | tuple[str, ...] | None = None,
    market: str | None = None,
) -> BillingSeriesRecorte:
    codes = tuple(
        sorted({str(code).strip() for code in (product_codes or []) if str(code).strip()})
    )
    groups = tuple(
        sorted(
            {
                str(group).strip()
                for group in (product_groups or [])
                if str(group).strip()
            }
        )
    )
    market_pred = None
    if market is not None and str(market).strip():
        CommercialRolReturnSql.market_filter_predicate(str(market).strip())
        market_pred = str(market).strip().lower()
        if market_pred in {"external", "foreign"}:
            market_pred = "export"
    return BillingSeriesRecorte(
        product_codes=codes,
        product_groups=groups,
        market=market_pred,
    )


def _in_list_clause(column: str, values: tuple[str, ...]) -> tuple[str, list[str]]:
    placeholders = ", ".join("?" for _ in values)
    return f"{column} IN ({placeholders})", list(values)


def _recorte_sale_fragments(
    recorte: BillingSeriesRecorte,
) -> tuple[str, str, list[str]]:
    joins = _SB1_SALE_JOIN if recorte.product_groups else ""
    clauses: list[str] = []
    params: list[str] = []
    if recorte.product_codes:
        clause, values = _in_list_clause("D2.D2_COD", recorte.product_codes)
        clauses.append(clause)
        params.extend(values)
    if recorte.product_groups:
        clause, values = _in_list_clause(
            "RTRIM(LTRIM(SB1.B1_GRUPO))",
            recorte.product_groups,
        )
        clauses.append(clause)
        params.extend(values)
    market_pred = CommercialRolReturnSql.market_filter_predicate(
        recorte.market, d2_alias="D2"
    )
    if market_pred:
        clauses.append(market_pred)
    where = (" AND " + " AND ".join(clauses)) if clauses else ""
    return joins, where, params


def _recorte_return_fragments(
    recorte: BillingSeriesRecorte,
) -> tuple[str, str, list[str]]:
    joins = _SB1_RETURN_JOIN if recorte.product_groups else ""
    clauses: list[str] = []
    params: list[str] = []
    if recorte.product_codes:
        clause, values = _in_list_clause("D1.D1_COD", recorte.product_codes)
        clauses.append(clause)
        params.extend(values)
    if recorte.product_groups:
        clause, values = _in_list_clause(
            "RTRIM(LTRIM(SB1D.B1_GRUPO))",
            recorte.product_groups,
        )
        clauses.append(clause)
        params.extend(values)
    where = (" AND " + " AND ".join(clauses)) if clauses else ""
    return joins, where, params


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
    metric: str = DEFAULT_BILLING_METRIC,
    recorte: BillingSeriesRecorte | None = None,
) -> str:
    nature = normalize_billing_nature(nature)
    metric = normalize_billing_metric(metric)
    active = recorte if recorte and recorte.has_line_filters else BillingSeriesRecorte()
    if metric == "quantity":
        if nature == "gross":
            return _build_gross_line_series_sql(
                where_pairs=where_pairs,
                granularity=granularity,
                recorte=active,
                metric="quantity",
            )
        return _build_net_series_sql(
            where_pairs=where_pairs,
            granularity=granularity,
            recorte=active,
            metric="quantity",
        )
    if nature == "gross" and not active.has_line_filters:
        return _build_gross_series_sql(where_pairs=where_pairs, granularity=granularity)
    if nature == "gross":
        return _build_gross_line_series_sql(
            where_pairs=where_pairs,
            granularity=granularity,
            recorte=active,
            metric="value",
        )
    return _build_net_series_sql(
        where_pairs=where_pairs,
        granularity=granularity,
        recorte=active,
        metric="value",
    )


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


def _build_gross_line_series_sql(
    *,
    where_pairs: str,
    granularity: str,
    recorte: BillingSeriesRecorte,
    metric: str = DEFAULT_BILLING_METRIC,
) -> str:
    """Gross por linha: D2_TOTAL (value) ou D2_QUANT (quantity) — nunca F2_VALBRUT."""
    metric = normalize_billing_metric(metric)
    sale_period = _period_expr_from_protheus_col("D2.D2_EMISSAO", granularity)
    joins, where_extra, _ = _recorte_sale_fragments(recorte)
    if metric == "quantity":
        value_expr = _QTY_SALE_SUM
        unit_select = f",{_UNIT_AGG_SALE}"
    else:
        value_expr = CommercialRolReturnSql.sale_gross_sum_expr(d2_alias="D2")
        unit_select = ""
    return f"""
            SELECT
                {sale_period} AS year_month,
                {value_expr} AS billed_value
                {unit_select}
              FROM SD2010 D2 WITH (NOLOCK)
              {joins}
             WHERE D2.D_E_L_E_T_ = ''
               AND ISNULL(D2.D2_TIPO, '') <> 'D'
               AND ({where_pairs})
               AND D2.D2_EMISSAO >= ?
               AND D2.D2_EMISSAO <= ?
               {where_extra}
             GROUP BY {sale_period}
             ORDER BY year_month ASC
        """


def _build_net_series_sql(
    *,
    where_pairs: str,
    granularity: str,
    recorte: BillingSeriesRecorte | None = None,
    metric: str = DEFAULT_BILLING_METRIC,
) -> str:
    """ROL líquido por bucket: vendas (D2_EMISSAO) − devoluções (D1_DTDIGIT)."""
    metric = normalize_billing_metric(metric)
    active = recorte or BillingSeriesRecorte()
    sale_joins, sale_where, _ = _recorte_sale_fragments(active)
    ret_joins, ret_where, _ = _recorte_return_fragments(active)
    sale_period = _period_expr_from_protheus_col("D2.D2_EMISSAO", granularity)
    ret_period = _period_expr_from_protheus_col("D1.D1_DTDIGIT", granularity)
    exists_where = "D1X.D1_DTDIGIT >= ? AND D1X.D1_DTDIGIT <= ?"
    d2_pairs = where_pairs
    d1_pairs = where_pairs.replace("D2.D2_CLIENTE", "D1.D1_FORNECE").replace(
        "D2.D2_LOJA", "D1.D1_LOJA"
    )
    if metric == "quantity":
        sale_value = _QTY_SALE_SUM
        ret_value = _QTY_RETURN_SUM
        sale_unit = f",{_UNIT_AGG_SALE}"
        ret_unit = f",{_UNIT_AGG_RETURN}"
        outer_unit = """
                CASE
                    WHEN ISNULL(V.mixed_units, 0) = 1 OR ISNULL(D.mixed_units, 0) = 1 THEN NULL
                    WHEN V.unit IS NOT NULL AND D.unit IS NOT NULL AND V.unit <> D.unit THEN NULL
                    ELSE COALESCE(V.unit, D.unit)
                END AS unit,
                CASE
                    WHEN ISNULL(V.mixed_units, 0) = 1 OR ISNULL(D.mixed_units, 0) = 1 THEN 1
                    WHEN V.unit IS NOT NULL AND D.unit IS NOT NULL AND V.unit <> D.unit THEN 1
                    ELSE 0
                END AS mixed_units
        """
    else:
        sale_value = CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")
        ret_value = CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")
        sale_unit = ""
        ret_unit = ""
        outer_unit = ""
    eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
        exists_where=exists_where,
    )
    outer_unit_select = f",{outer_unit}" if outer_unit else ""
    return f"""
            WITH vendas AS (
                SELECT
                    {sale_period} AS year_month,
                    {sale_value} AS billed_value
                    {sale_unit}
                  FROM SD2010 D2 WITH (NOLOCK)
                  {CommercialRolReturnSql.sale_customer_join(with_nolock=True)}
                  {CommercialRolReturnSql.sale_tes_join(with_nolock=True)}
                  {sale_joins}
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({d2_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                   AND {eligibility}
                   {sale_where}
                 GROUP BY {sale_period}
            ),
            devolucoes AS (
                SELECT
                    {ret_period} AS year_month,
                    {ret_value} AS billed_value
                    {ret_unit}
                  FROM SD1010 D1 WITH (NOLOCK)
                  {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                  {ret_joins}
                 WHERE D1.D_E_L_E_T_ = ''
                   AND ({d1_pairs})
                   AND D1.D1_DTDIGIT >= ?
                   AND D1.D1_DTDIGIT <= ?
                   AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                   {ret_where}
                 GROUP BY {ret_period}
            )
            SELECT
                ISNULL(V.year_month, D.year_month) AS year_month,
                ISNULL(V.billed_value, 0) - ISNULL(D.billed_value, 0) AS billed_value
                {outer_unit_select}
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
    metric: str = DEFAULT_BILLING_METRIC,
    recorte: BillingSeriesRecorte | None = None,
) -> tuple:
    nature = normalize_billing_nature(nature)
    metric = normalize_billing_metric(metric)
    active = recorte if recorte and recorte.has_line_filters else BillingSeriesRecorte()
    _, _, sale_params = _recorte_sale_fragments(active)
    _, _, ret_params = _recorte_return_fragments(active)
    if nature == "gross":
        # value+sem recorte = path F2_VALBRUT; quantity ou recorte = path linha
        if metric == "value" and not active.has_line_filters:
            return tuple(pair_params + [start_date, end_date])
        return tuple(pair_params + [start_date, end_date] + sale_params)
    # net: vendas pairs+start/end+exists start/end+sale filters; devolucoes pairs+start/end+ret filters
    return tuple(
        pair_params
        + [start_date, end_date, start_date, end_date]
        + sale_params
        + pair_params
        + [start_date, end_date]
        + ret_params
    )
