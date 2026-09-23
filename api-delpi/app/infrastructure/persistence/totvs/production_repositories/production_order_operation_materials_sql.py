"""SQL canônico dos empenhos SD4 por OP e operação — consulta única e em lote.

Uma só definição de "empenho da operação" serve as duas rotas: a consulta de uma
OP+operação e a consulta em lote por lista de OPs. A diferença é apenas o
predicado da OP e a presença do filtro de operação.
"""

from __future__ import annotations

from app.domain.production.operation_materials_scope import (
    OPERATION_MATERIALS_COMMITMENT_TABLE,
    OPERATION_MATERIALS_PRODUCT_TABLE,
)
from app.domain.services.production.consumption_real_quantity_service import (
    ConsumptionRealQuantityService,
)


def operation_materials_sql(*, order_count: int = 1, filter_operation: bool = True) -> str:
    """Monta o SQL de empenhos agregados por OP, operação e componente.

    ``order_count`` é a quantidade de OPs no predicado (1 = consulta única).
    ``filter_operation`` adiciona o filtro ``D4_OPERAC``, usado só na consulta
    de uma operação específica.
    """
    if order_count < 1:
        raise ValueError("order_count deve ser pelo menos 1.")

    consumption_expr = ConsumptionRealQuantityService.SQL_EXPRESSION.replace("D4.", "RE.")

    if order_count == 1:
        order_clause = "AND RTRIM(LTRIM(RE.D4_OP)) = ?"
    else:
        placeholders = ", ".join(["?"] * order_count)
        order_clause = f"AND RTRIM(LTRIM(RE.D4_OP)) IN ({placeholders})"

    operation_clause = "AND RTRIM(LTRIM(RE.D4_OPERAC)) = ?" if filter_operation else ""

    return f"""
        SELECT
            RTRIM(LTRIM(RE.D4_FILIAL)) AS branch,
            RTRIM(LTRIM(RE.D4_OP)) AS production_order,
            RTRIM(LTRIM(RE.D4_OPERAC)) AS operation,
            RTRIM(LTRIM(RE.D4_COD)) AS product_code,
            RTRIM(LTRIM(P.B1_DESC)) AS description,
            RTRIM(LTRIM(P.B1_UM)) AS unit,
            RTRIM(LTRIM(P.B1_TIPO)) AS product_type,
            CAST(SUM(RE.D4_QTDEORI) AS FLOAT) AS original_qty,
            CAST(SUM(RE.D4_QUANT) AS FLOAT) AS open_qty,
            CAST(SUM({consumption_expr}) AS FLOAT) AS consumed_qty,
            COUNT(*) AS commitment_count
        FROM {OPERATION_MATERIALS_COMMITMENT_TABLE} RE WITH (NOLOCK)
        INNER JOIN {OPERATION_MATERIALS_PRODUCT_TABLE} P WITH (NOLOCK)
            ON P.B1_COD = RE.D4_COD
           AND P.D_E_L_E_T_ = ''
        WHERE RE.D_E_L_E_T_ = ''
          {order_clause}
          {operation_clause}
          AND RE.D4_FILIAL = ?
        GROUP BY
            RE.D4_FILIAL,
            RE.D4_OP,
            RE.D4_OPERAC,
            RE.D4_COD,
            P.B1_DESC,
            P.B1_UM,
            P.B1_TIPO
        ORDER BY RE.D4_OP ASC, RE.D4_OPERAC ASC, RE.D4_COD ASC
    """
