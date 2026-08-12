"""SQL parametrizado — VW_PD3_BENEF_RETORNOS (materiais de terceiros).

Colunas da view live em homolog não podem ser inventadas (ex.:
COD_PARCEIRO_RETORNO → 42S22 / 503). Enriquecimento via JOIN (SB1.B1_REFEREN)
é permitido.
"""

from __future__ import annotations

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.domain.totvs.protheus_third_party_materials import VIEW_NAME

VIEW = VIEW_NAME

# SB1.B1_REFEREN (Ref. Cliente) não está na view live — JOIN na consulta.
VIEW_FROM = f"""
        {VIEW} V WITH (NOLOCK)
        LEFT JOIN SB1010 SB1 WITH (NOLOCK)
            ON LTRIM(RTRIM(SB1.B1_COD)) = V.PRODUTO
           AND LTRIM(RTRIM(SB1.B1_FILIAL)) = ''
           AND SB1.D_E_L_E_T_ = ' '
"""

DETAIL_COLUMNS = """
    V.RECNO_REMESSA,
    V.FILIAL,
    V.ID_REMESSA,
    V.NF_RECEBIMENTO,
    V.SERIE_RECEBIMENTO,
    V.EMISSAO_RECEBIMENTO,
    V.DIGITACAO_RECEBIMENTO,
    V.TES_RECEBIMENTO,
    V.PRODUTO,
    LTRIM(RTRIM(SB1.B1_REFEREN)) AS REFERENCIA_CLIENTE,
    V.DESCRICAO_PRODUTO,
    V.UNIDADE_MEDIDA,
    V.TIPO_PRODUTO,
    V.GRUPO_PRODUTO,
    V.PRODUTO_BLOQUEADO,
    V.TIPO_PARCEIRO,
    V.COD_PARCEIRO,
    V.LOJA_PARCEIRO,
    V.NOME_PARCEIRO,
    V.NOME_REDUZIDO_PARCEIRO,
    V.PARCEIRO_BLOQUEADO,
    V.QTD_RECEBIDA,
    V.QTD_DEVOLVIDA_TOTAL,
    V.SALDO_A_ENTREGAR,
    V.STATUS_REMESSA,
    V.POSSUI_SALDO,
    V.IND_ATENDIDO,
    V.QTD_RETORNOS_SOMADA,
    V.DIFERENCA_CONTROLE,
    V.RECNO_RETORNO,
    V.NF_RETORNO,
    V.SERIE_RETORNO,
    V.EMISSAO_RETORNO,
    V.DIGITACAO_RETORNO,
    V.TES_RETORNO,
    V.QTD_RETORNO,
    V.QTD_DEVOLVIDA_ACUMULADA,
    V.SALDO_APOS_RETORNO,
    V.TIPO_PARCEIRO_RETORNO
""".strip()


def build_filter_clause(
    request: ThirdPartyMaterialsQueryRequest,
) -> tuple[str, list]:
    clauses = ["LTRIM(RTRIM(V.FILIAL)) = ?"]
    params: list = [request.branch]

    if request.product:
        clauses.append("LTRIM(RTRIM(V.PRODUTO)) = ?")
        params.append(request.product)
    if request.customer_reference:
        clauses.append(
            "LTRIM(RTRIM(ISNULL(SB1.B1_REFEREN, ''))) COLLATE Latin1_General_CI_AI LIKE ?"
        )
        params.append(f"{request.customer_reference}%")
    if request.partner_code:
        clauses.append("LTRIM(RTRIM(V.COD_PARCEIRO)) = ?")
        params.append(request.partner_code)
    if request.partner_store:
        clauses.append("LTRIM(RTRIM(V.LOJA_PARCEIRO)) = ?")
        params.append(request.partner_store)
    if request.receipt_number:
        clauses.append("LTRIM(RTRIM(V.NF_RECEBIMENTO)) = ?")
        params.append(request.receipt_number)
    if request.return_number:
        clauses.append("LTRIM(RTRIM(V.NF_RETORNO)) = ?")
        params.append(request.return_number)
    if request.issued_from:
        clauses.append("V.EMISSAO_RECEBIMENTO >= ?")
        params.append(request.issued_from)
    if request.issued_to:
        clauses.append("V.EMISSAO_RECEBIMENTO <= ?")
        params.append(request.issued_to)
    if request.view_status():
        clauses.append("V.STATUS_REMESSA = ?")
        params.append(request.view_status())
    if request.only_with_balance:
        clauses.append("V.POSSUI_SALDO = 'S'")

    ignored = request.ignored_products()
    if ignored:
        placeholders = ", ".join("?" for _ in ignored)
        clauses.append(f"LTRIM(RTRIM(V.PRODUTO)) NOT IN ({placeholders})")
        params.extend(ignored)

    return " AND ".join(clauses), params


def build_count_shipments_sql(
    request: ThirdPartyMaterialsQueryRequest,
) -> tuple[str, tuple]:
    where_sql, params = build_filter_clause(request)
    sql = f"""
        SELECT COUNT(*) AS total_items
        FROM (
            SELECT DISTINCT V.RECNO_REMESSA
            FROM {VIEW_FROM}
            WHERE {where_sql}
        ) T
    """
    return sql, tuple(params)


def build_shipment_page_sql(
    request: ThirdPartyMaterialsQueryRequest,
) -> tuple[str, tuple]:
    where_sql, params = build_filter_clause(request)
    sql = f"""
        SELECT RECNO_REMESSA
        FROM (
            SELECT
                V.RECNO_REMESSA,
                MAX(V.EMISSAO_RECEBIMENTO) AS emissao,
                MAX(V.NF_RECEBIMENTO) AS nf
            FROM {VIEW_FROM}
            WHERE {where_sql}
            GROUP BY V.RECNO_REMESSA
        ) T
        ORDER BY emissao DESC, nf DESC, RECNO_REMESSA DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    offset = (request.page - 1) * request.page_size
    return sql, tuple([*params, offset, request.page_size])


def build_details_by_recnos_sql(recnos: list[int]) -> tuple[str, tuple]:
    if not recnos:
        return (
            f"SELECT {DETAIL_COLUMNS} FROM {VIEW_FROM} WHERE 1 = 0",
            (),
        )
    placeholders = ", ".join("?" for _ in recnos)
    sql = f"""
        SELECT {DETAIL_COLUMNS}
        FROM {VIEW_FROM}
        WHERE V.RECNO_REMESSA IN ({placeholders})
        ORDER BY V.EMISSAO_RECEBIMENTO DESC, V.RECNO_REMESSA DESC,
                 V.EMISSAO_RETORNO, V.DIGITACAO_RETORNO, V.RECNO_RETORNO
    """
    return sql, tuple(recnos)


def build_details_by_recno_sql(
    *,
    shipment_recno: int,
    branch: str,
    ignored_products: tuple[str, ...],
) -> tuple[str, tuple]:
    clauses = ["V.RECNO_REMESSA = ?", "LTRIM(RTRIM(V.FILIAL)) = ?"]
    params: list = [shipment_recno, branch]
    if ignored_products:
        placeholders = ", ".join("?" for _ in ignored_products)
        clauses.append(f"LTRIM(RTRIM(V.PRODUTO)) NOT IN ({placeholders})")
        params.extend(ignored_products)
    sql = f"""
        SELECT {DETAIL_COLUMNS}
        FROM {VIEW_FROM}
        WHERE {" AND ".join(clauses)}
        ORDER BY V.EMISSAO_RETORNO, V.DIGITACAO_RETORNO, V.RECNO_RETORNO
    """
    return sql, tuple(params)


def build_summary_sql(
    request: ThirdPartyMaterialsQueryRequest,
) -> tuple[str, tuple]:
    where_sql, params = build_filter_clause(request)
    sql = f"""
        SELECT
            COUNT(*) AS total_shipments,
            SUM(CASE WHEN POSSUI_SALDO = 'S' THEN 1 ELSE 0 END) AS open_shipments,
            SUM(CASE WHEN STATUS_REMESSA = 'PARCIAL' THEN 1 ELSE 0 END) AS partial_shipments,
            SUM(CASE WHEN STATUS_REMESSA = 'SEM RETORNO' THEN 1 ELSE 0 END) AS no_return_shipments,
            CAST(ISNULL(SUM(CASE WHEN POSSUI_SALDO = 'S' THEN SALDO_A_ENTREGAR ELSE 0 END), 0)
                AS decimal(28, 8)) AS pending_balance
        FROM (
            SELECT DISTINCT
                V.RECNO_REMESSA,
                V.POSSUI_SALDO,
                V.STATUS_REMESSA,
                V.SALDO_A_ENTREGAR
            FROM {VIEW_FROM}
            WHERE {where_sql}
        ) T
    """
    return sql, tuple(params)


def build_export_sql(
    request: ThirdPartyMaterialsQueryRequest,
    *,
    limit: int,
) -> tuple[str, tuple]:
    where_sql, params = build_filter_clause(request)
    sql = f"""
        SELECT TOP (?) {DETAIL_COLUMNS}
        FROM {VIEW_FROM}
        WHERE {where_sql}
        ORDER BY V.EMISSAO_RECEBIMENTO DESC, V.RECNO_REMESSA DESC,
                 V.EMISSAO_RETORNO, V.DIGITACAO_RETORNO, V.RECNO_RETORNO
    """
    return sql, tuple([limit, *params])
