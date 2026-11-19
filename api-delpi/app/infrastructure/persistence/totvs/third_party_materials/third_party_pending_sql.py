"""Report de pendências de materiais recebidos de fornecedores, a partir da SB6.

A view tem uma linha por retorno: reduzir a uma linha por RECNO_REMESSA
antes de somar. Não confundir B6_TIPO='D' com o fluxo inverso ('E').
"""
from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.infrastructure.persistence.totvs.third_party_materials.third_party_materials_sql import (
    VIEW_FROM,
    build_filter_clause,
)


def _pending_cte(request: ThirdPartyMaterialsQueryRequest) -> tuple[str, list]:
    filters, params = build_filter_clause(request)
    cte = f"""
    WITH PendingShipments AS (
        SELECT
            V.RECNO_REMESSA,
            MAX(V.COD_PARCEIRO) AS supplier_code,
            MAX(V.LOJA_PARCEIRO) AS supplier_store,
            MAX(V.PRODUTO) AS product_code,
            MAX(V.DESCRICAO_PRODUTO) AS product_description,
            MAX(V.UNIDADE_MEDIDA) AS unit,
            MAX(V.QTD_RECEBIDA) AS received_quantity,
            MAX(V.QTD_DEVOLVIDA_TOTAL) AS returned_quantity,
            MAX(V.SALDO_A_ENTREGAR) AS pending_quantity
        FROM {VIEW_FROM}
        WHERE {filters}
          AND V.TIPO_PARCEIRO = 'F'
          AND V.POSSUI_SALDO = 'S'
        GROUP BY V.RECNO_REMESSA
    ),
    Consolidated AS (
        SELECT
            supplier_code,
            supplier_store,
            product_code,
            MAX(product_description) AS product_description,
            MAX(unit) AS unit,
            COUNT_BIG(*) AS shipment_count,
            CAST(SUM(received_quantity) AS decimal(28, 8)) AS received_quantity,
            CAST(SUM(returned_quantity) AS decimal(28, 8)) AS returned_quantity,
            CAST(SUM(pending_quantity) AS decimal(28, 8)) AS pending_quantity
        FROM PendingShipments
        GROUP BY supplier_code, supplier_store, product_code
    )
    """
    return cte, params


SUPPLIER_FROM = """
    FROM Consolidated C
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
      ON LTRIM(RTRIM(SA2.A2_COD)) = C.supplier_code
     AND LTRIM(RTRIM(SA2.A2_LOJA)) = C.supplier_store
     AND LTRIM(RTRIM(SA2.A2_FILIAL)) = ''
     AND SA2.D_E_L_E_T_ = ' '
"""

SUPPLIER_COLUMNS = """
    C.supplier_code,
    C.supplier_store,
    COALESCE(NULLIF(LTRIM(RTRIM(SA2.A2_NOME)), ''), C.supplier_code) AS supplier_name,
    C.product_code,
    C.product_description,
    C.unit,
    C.shipment_count,
    C.received_quantity,
    C.returned_quantity,
    C.pending_quantity
"""


def build_pending_summary_sql(request: ThirdPartyMaterialsQueryRequest) -> tuple[str, tuple]:
    cte, params = _pending_cte(request)
    sql = f"""
    {cte}
    SELECT
        COUNT_BIG(*) AS product_count,
        (SELECT COUNT_BIG(*) FROM (
            SELECT supplier_code, supplier_store
            FROM Consolidated GROUP BY supplier_code, supplier_store
        ) Suppliers) AS supplier_count,
        COALESCE(SUM(shipment_count), 0) AS shipment_count,
        CAST(COALESCE(SUM(pending_quantity), 0) AS decimal(28, 8)) AS pending_quantity,
        COUNT(DISTINCT COALESCE(NULLIF(unit, ''), '[SEM UM]')) AS unit_count,
        MAX(unit) AS unit
    FROM Consolidated
    """
    return sql, tuple(params)


def build_pending_page_sql(request: ThirdPartyMaterialsQueryRequest) -> tuple[str, tuple]:
    cte, params = _pending_cte(request)
    sql = f"""
    {cte}
    SELECT {SUPPLIER_COLUMNS}
    {SUPPLIER_FROM}
    ORDER BY C.pending_quantity DESC, C.supplier_code, C.supplier_store, C.product_code
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    offset = (request.page - 1) * request.page_size
    return sql, tuple([*params, offset, request.page_size])


def build_pending_export_sql(
    request: ThirdPartyMaterialsQueryRequest, *, limit: int
) -> tuple[str, tuple]:
    cte, params = _pending_cte(request)
    sql = f"""
    {cte}
    SELECT TOP (?) {SUPPLIER_COLUMNS}
    {SUPPLIER_FROM}
    ORDER BY C.supplier_code, C.supplier_store, C.product_code
    """
    return sql, tuple([limit, *params])
