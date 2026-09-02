"""SQL — vínculos NF de compra x CT-e (SF8010 + SF1010) para análise de frete.

Contrato puro: devolve as linhas de vínculo com os valores de cada documento.
Rateio, percentual, limite por filial e classificação de inconsistência são
regra do consumidor e ficam fora desta camada.

Duas particularidades justificam o formato da query:

1. **Fecho da base.** A base de rateio de um CT-e soma o ``F1_VALMERC`` de todas
   as NFs vinculadas a ele, inclusive as que estão fora do filtro do usuário.
   Por isso o filtro de data não pode ser empurrado para o ``WHERE`` — ele vira
   a coluna ``in_filter`` e a seleção final traz o CT-e inteiro.
2. **Inconsistência visível.** Os joins com a SF1010 são ``LEFT`` para expor
   documento referenciado e não localizado. Vínculo órfão (sem NF) é escopado
   pelo ``F8_DTDIGIT`` do próprio vínculo, já que não existe data de NF.
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.domain.totvs.protheus_freight_links import (
    FREIGHT_LINK_TYPE,
    FREIGHT_SERIES_COLUMNS,
    ORIGIN_SERIES_COLUMNS,
    series_coalesce_expr,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

# Datas da NF de compra com fallback para a digitação do próprio vínculo.
# COALESCE só cai no fallback quando o LEFT JOIN não encontrou a NF.
ISSUE_DATE_EXPR = "COALESCE(NF.F1_EMISSAO, L.link_entry_date)"
ENTRY_DATE_EXPR = "COALESCE(NF.F1_DTDIGIT, L.link_entry_date)"


def build_purchase_freight_branch_filter(branch: Optional[str]) -> Tuple[str, tuple]:
    """Filtro empurrado para a SF8010.

    Só a filial pode descer até aqui: todas as linhas de um CT-e compartilham a
    mesma ``F8_FILIAL``, então filtrar por filial não quebra o fecho da base.
    """
    qb = QueryBuilder()
    qb.eq("F8.F8_FILIAL", branch)
    return qb.build()


def build_purchase_freight_scope_filter(
    *,
    issue_start: Optional[str],
    issue_end: Optional[str],
    entry_start: Optional[str],
    entry_end: Optional[str],
    supplier: Optional[str],
    invoice_document: Optional[str],
    freight_document: Optional[str],
) -> Tuple[str, tuple]:
    """Predicado da coluna ``in_filter`` — nunca vira ``WHERE`` da SF8010."""
    qb = QueryBuilder()
    qb.date_range(ISSUE_DATE_EXPR, issue_start, issue_end)
    qb.date_range(ENTRY_DATE_EXPR, entry_start, entry_end)
    qb.eq("RTRIM(L.supplier_code)", supplier)
    qb.eq("RTRIM(L.invoice_document)", invoice_document)
    qb.eq("RTRIM(L.freight_document)", freight_document)
    return qb.build()


def build_purchase_freight_links_sql(
    *,
    branch_clause: str,
    scope_clause: str,
) -> str:
    """Monta a query completa.

    Ordem dos parâmetros: tipo do vínculo, filial, escopo (``in_filter``),
    limite do ``TOP``.
    """
    freight_series = series_coalesce_expr(FREIGHT_SERIES_COLUMNS, table_alias="F8")
    origin_series = series_coalesce_expr(ORIGIN_SERIES_COLUMNS, table_alias="F8")

    return f"""
        WITH LINK AS (
            SELECT DISTINCT
                F8.F8_FILIAL AS branch,
                F8.F8_NFDIFRE AS freight_document,
                {freight_series} AS freight_series,
                F8.F8_TRANSP AS carrier_code,
                F8.F8_LOJTRAN AS carrier_store,
                F8.F8_NFORIG AS invoice_document,
                {origin_series} AS invoice_series,
                F8.F8_FORNECE AS supplier_code,
                F8.F8_LOJA AS supplier_store,
                F8.F8_DTDIGIT AS link_entry_date
            FROM SF8010 F8 WITH (NOLOCK)
            WHERE F8.F8_TIPO = ?
              AND F8.D_E_L_E_T_ = ''
              AND {branch_clause}
        ),
        PAIR AS (
            SELECT
                RTRIM(L.branch) AS branch,
                RTRIM(L.freight_document) AS freight_document,
                RTRIM(L.freight_series) AS freight_series,
                RTRIM(L.carrier_code) AS carrier_code,
                RTRIM(L.carrier_store) AS carrier_store,
                RTRIM(L.invoice_document) AS invoice_document,
                RTRIM(L.invoice_series) AS invoice_series,
                RTRIM(L.supplier_code) AS supplier_code,
                RTRIM(L.supplier_store) AS supplier_store,
                RTRIM(L.link_entry_date) AS link_entry_date,
                CASE WHEN NF.F1_FILIAL IS NULL THEN 0 ELSE 1 END AS invoice_found,
                CAST(NF.F1_VALMERC AS DECIMAL(18, 2)) AS invoice_goods_value,
                RTRIM(NF.F1_EMISSAO) AS invoice_issue_date,
                RTRIM(NF.F1_DTDIGIT) AS invoice_entry_date,
                RTRIM(SA2F.A2_NREDUZ) AS supplier_name,
                CASE WHEN CTE.F1_FILIAL IS NULL THEN 0 ELSE 1 END AS freight_found,
                CAST(CTE.F1_VALBRUT AS DECIMAL(18, 2)) AS freight_gross_value,
                RTRIM(CTE.F1_EMISSAO) AS freight_issue_date,
                RTRIM(CTE.F1_CHVNFE) AS freight_access_key,
                RTRIM(CTE.F1_TPCTE) AS freight_document_type,
                RTRIM(CTE.F1_ESPECIE) AS freight_document_kind,
                RTRIM(SA2T.A2_NREDUZ) AS carrier_name,
                CASE WHEN {scope_clause} THEN 1 ELSE 0 END AS in_filter
            FROM LINK L
            LEFT JOIN SF1010 NF WITH (NOLOCK)
                ON NF.F1_FILIAL = L.branch
               AND NF.F1_DOC = L.invoice_document
               AND NF.F1_SERIE = L.invoice_series
               AND NF.F1_FORNECE = L.supplier_code
               AND NF.F1_LOJA = L.supplier_store
               AND NF.D_E_L_E_T_ = ''
            LEFT JOIN SF1010 CTE WITH (NOLOCK)
                ON CTE.F1_FILIAL = L.branch
               AND CTE.F1_DOC = L.freight_document
               AND CTE.F1_SERIE = L.freight_series
               AND CTE.F1_FORNECE = L.carrier_code
               AND CTE.F1_LOJA = L.carrier_store
               AND CTE.D_E_L_E_T_ = ''
            LEFT JOIN SA2010 SA2F WITH (NOLOCK)
                ON SA2F.A2_COD = L.supplier_code
               AND SA2F.A2_LOJA = L.supplier_store
               AND SA2F.D_E_L_E_T_ = ''
            LEFT JOIN SA2010 SA2T WITH (NOLOCK)
                ON SA2T.A2_COD = L.carrier_code
               AND SA2T.A2_LOJA = L.carrier_store
               AND SA2T.D_E_L_E_T_ = ''
        ),
        MATCHED AS (
            SELECT DISTINCT
                branch,
                freight_document,
                freight_series,
                carrier_code,
                carrier_store
            FROM PAIR
            WHERE in_filter = 1
              AND invoice_found = 1
        )
        SELECT TOP (?)
            P.*
        FROM PAIR P
        LEFT JOIN MATCHED M
            ON M.branch = P.branch
           AND M.freight_document = P.freight_document
           AND M.freight_series = P.freight_series
           AND M.carrier_code = P.carrier_code
           AND M.carrier_store = P.carrier_store
        WHERE M.branch IS NOT NULL
           OR P.in_filter = 1
        ORDER BY
            P.branch ASC,
            P.invoice_document ASC,
            P.invoice_series ASC,
            P.freight_document ASC,
            P.freight_series ASC
    """


def build_purchase_freight_links_params(
    *,
    branch_params: tuple,
    scope_params: tuple,
    fetch_limit: int,
) -> tuple:
    """Concatena os parâmetros na ordem em que aparecem no texto da query."""
    return (FREIGHT_LINK_TYPE, *branch_params, *scope_params, fetch_limit)
