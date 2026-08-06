"""SQL — cadastro de planos de inspeção de processo (QP6 × OPs abertas SC2)."""

from __future__ import annotations

from app.domain.totvs.protheus_branches import branch_filter_sql


def _open_ops_cte(*, branch_scope: str) -> tuple[str, list]:
    """OPs abertas (C2_DATRF vazio) com flag has_plan via existência em QP6010."""
    branch_clause, branch_params = branch_filter_sql("OP.C2_FILIAL", branch_scope)
    where_extra = f"AND {branch_clause}" if branch_clause else ""
    sql = f"""
    open_ops AS (
        SELECT
            RTRIM(OP.C2_FILIAL) AS branch,
            RTRIM(OP.C2_OP) AS production_order,
            RTRIM(OP.C2_PRODUTO) AS product_code,
            NULLIF(LTRIM(RTRIM(OP.C2_YOBSQUA)), '') AS observation,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM QP6010 Q WITH (NOLOCK)
                    WHERE Q.D_E_L_E_T_ = ''
                      AND RTRIM(Q.QP6_PRODUT) = RTRIM(OP.C2_PRODUTO)
                ) THEN 1
                ELSE 0
            END AS has_plan
        FROM SC2010 OP WITH (NOLOCK)
        WHERE OP.D_E_L_E_T_ = ''
          AND (OP.C2_DATRF IS NULL OR LTRIM(RTRIM(OP.C2_DATRF)) = '')
          {where_extra}
    )
    """
    return sql, list(branch_params)


def build_summary_sql(branch_scope: str) -> tuple[str, tuple]:
    cte, params = _open_ops_cte(branch_scope=branch_scope)
    sql = f"""
    ;WITH {cte}
    SELECT
        COUNT(*) AS total_open_orders,
        SUM(CASE WHEN has_plan = 0 THEN 1 ELSE 0 END) AS orders_without_plan,
        COUNT(DISTINCT CASE WHEN has_plan = 0 THEN product_code END) AS products_without_plan,
        SUM(CASE WHEN has_plan = 1 THEN 1 ELSE 0 END) AS orders_with_plan
    FROM open_ops
    """
    return sql, tuple(params)


def build_count_orders_without_plan_sql(branch_scope: str) -> tuple[str, tuple]:
    cte, params = _open_ops_cte(branch_scope=branch_scope)
    sql = f"""
    ;WITH {cte}
    SELECT COUNT(*) AS total
    FROM open_ops
    WHERE has_plan = 0
    """
    return sql, tuple(params)


def build_list_orders_without_plan_sql(
    branch_scope: str,
    *,
    offset: int,
    page_size: int,
) -> tuple[str, tuple]:
    cte, params = _open_ops_cte(branch_scope=branch_scope)
    sql = f"""
    ;WITH {cte}
    SELECT
        o.branch,
        o.product_code,
        NULLIF(LTRIM(RTRIM(P.B1_DESC)), '') AS product_description,
        o.production_order,
        o.observation
    FROM open_ops o
    LEFT JOIN SB1010 P WITH (NOLOCK)
        ON P.D_E_L_E_T_ = ''
       AND RTRIM(P.B1_COD) = o.product_code
    WHERE o.has_plan = 0
    ORDER BY o.product_code, o.production_order
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    return sql, tuple([*params, offset, page_size])


def build_count_products_without_plan_sql(branch_scope: str) -> tuple[str, tuple]:
    cte, params = _open_ops_cte(branch_scope=branch_scope)
    sql = f"""
    ;WITH {cte}
    SELECT COUNT(*) AS total
    FROM (
        SELECT product_code
        FROM open_ops
        WHERE has_plan = 0
        GROUP BY product_code
    ) x
    """
    return sql, tuple(params)


def build_list_products_without_plan_sql(
    branch_scope: str,
    *,
    offset: int,
    page_size: int,
) -> tuple[str, tuple]:
    cte, params = _open_ops_cte(branch_scope=branch_scope)
    sql = f"""
    ;WITH {cte}
    SELECT
        o.product_code,
        NULLIF(LTRIM(RTRIM(P.B1_DESC)), '') AS product_description,
        COUNT(*) AS open_orders_count
    FROM open_ops o
    LEFT JOIN SB1010 P WITH (NOLOCK)
        ON P.D_E_L_E_T_ = ''
       AND RTRIM(P.B1_COD) = o.product_code
    WHERE o.has_plan = 0
    GROUP BY o.product_code, P.B1_DESC
    ORDER BY o.product_code
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    return sql, tuple([*params, offset, page_size])


def build_count_products_with_plan_sql() -> tuple[str, tuple]:
    sql = """
    SELECT COUNT(*) AS total
    FROM (
        SELECT QP6_PRODUT
        FROM QP6010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
        GROUP BY QP6_PRODUT
    ) x
    """
    return sql, ()


def build_list_products_with_plan_sql(
    *,
    offset: int,
    page_size: int,
) -> tuple[str, tuple]:
    # Cadastro: revisão ativa = MAX(QP6_REVI) por produto (não usar em auditoria QIP).
    sql = """
    ;WITH active_qp6 AS (
        SELECT
            RTRIM(QP6_PRODUT) AS product_code,
            MAX(QP6_REVI) AS revision
        FROM QP6010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
        GROUP BY QP6_PRODUT
    )
    SELECT
        a.product_code,
        NULLIF(LTRIM(RTRIM(P.B1_DESC)), '') AS product_description,
        RTRIM(a.revision) AS revision,
        NULLIF(LTRIM(RTRIM(Q.QP6_DESCPO)), '') AS description,
        NULLIF(LTRIM(RTRIM(Q.QP6_TIPO)), '') AS inspection_type,
        NULLIF(LTRIM(RTRIM(Q.QP6_DTCAD)), '') AS created_at,
        NULLIF(LTRIM(RTRIM(Q.QP6_DTINI)), '') AS start_date
    FROM active_qp6 a
    INNER JOIN QP6010 Q WITH (NOLOCK)
        ON Q.D_E_L_E_T_ = ''
       AND RTRIM(Q.QP6_PRODUT) = a.product_code
       AND Q.QP6_REVI = a.revision
    LEFT JOIN SB1010 P WITH (NOLOCK)
        ON P.D_E_L_E_T_ = ''
       AND RTRIM(P.B1_COD) = a.product_code
    ORDER BY a.product_code
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    return sql, (offset, page_size)


def build_product_has_plan_sql(product_code: str) -> tuple[str, tuple]:
    sql = """
    SELECT TOP 1 1 AS ok
    FROM QP6010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
      AND RTRIM(QP6_PRODUT) = RTRIM(?)
    """
    return sql, (product_code,)


__all__ = [
    "build_summary_sql",
    "build_count_orders_without_plan_sql",
    "build_list_orders_without_plan_sql",
    "build_count_products_without_plan_sql",
    "build_list_products_without_plan_sql",
    "build_count_products_with_plan_sql",
    "build_list_products_with_plan_sql",
    "build_product_has_plan_sql",
]
