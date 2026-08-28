"""SQL canônico — OPs abertas para previsão de atendimento (ops-abertas).

Universo Delpi: saldo ``C2_QUANT > C2_QUJE`` **e** ``C2_DATRF`` vazio, só
produto acabado (``B1_TIPO = PA`` — mesmo recorte da view legada).
Encerrada parcial com saldo residual **não** entra (ver ``ordem-producao-chave.md``).

Substitui a view opaca ``VW_OPS_ABERTAS_PRODUTO`` / ``_RESUMO`` como fonte do
predicado de aberta; o contrato de colunas permanece o mesmo dos consumers
(Portal Comercial e PVA).
"""

from __future__ import annotations

from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_FINISHED_GOOD
from app.infrastructure.persistence.totvs.production_repositories.production_otd_sql_filters import (
    sc2_finish_date_empty_sql,
)

PRODUCTION_ORDER_TABLE = "SC2010"
PRODUCT_TABLE = "SB1010"

_OPEN_BALANCE_SQL = "OP.C2_QUANT > OP.C2_QUJE"
_OPEN_FINISH_SQL = sc2_finish_date_empty_sql("OP")
# Mesmo recorte da view legada VW_OPS_ABERTAS_PRODUTO (só produto acabado).
_FINISHED_GOOD_SQL = f"RTRIM(COALESCE(P.B1_TIPO, '')) = '{PRODUCT_TYPE_FINISHED_GOOD}'"

_DATE_ISO = "CONVERT(VARCHAR(10), TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM({col})), ''), 112), 23)"


def build_ops_abertas_detalhe_sql() -> str:
    """Lista OPs abertas por produto (detalhe), ordenadas para FIFO de previsão."""
    return f"""
    SELECT
        RTRIM(OP.C2_FILIAL) AS filial,
        RTRIM(OP.C2_OP) AS numero_op,
        RTRIM(OP.C2_PRODUTO) AS produto,
        RTRIM(COALESCE(P.B1_DESC, '')) AS descricao_produto,
        RTRIM(COALESCE(P.B1_TIPO, '')) AS tipo_produto,
        CAST(ISNULL(OP.C2_QUANT, 0) AS FLOAT) AS quantidade_op,
        CAST(ISNULL(OP.C2_QUJE, 0) AS FLOAT) AS quantidade_produzida,
        CAST(OP.C2_QUANT - OP.C2_QUJE AS FLOAT) AS saldo_op,
        {_DATE_ISO.format(col="OP.C2_EMISSAO")} AS data_emissao_op,
        {_DATE_ISO.format(col="OP.C2_DATPRI")} AS data_inicio_prevista_op,
        {_DATE_ISO.format(col="OP.C2_DATPRF")} AS data_fim_prevista_op,
        RTRIM(COALESCE(OP.C2_LOCAL, '')) AS armazem,
        RTRIM(COALESCE(OP.C2_OBS, '')) AS observacao_op
    FROM {PRODUCTION_ORDER_TABLE} OP WITH (NOLOCK)
    INNER JOIN {PRODUCT_TABLE} P WITH (NOLOCK)
        ON P.B1_COD = OP.C2_PRODUTO
       AND P.D_E_L_E_T_ = ''
    WHERE OP.D_E_L_E_T_ = ''
      AND {_OPEN_BALANCE_SQL}
      AND {_OPEN_FINISH_SQL}
      AND {_FINISHED_GOOD_SQL}
    ORDER BY
        OP.C2_FILIAL,
        OP.C2_PRODUTO,
        CASE WHEN NULLIF(LTRIM(RTRIM(OP.C2_DATPRF)), '') IS NULL THEN 1 ELSE 0 END,
        OP.C2_DATPRF ASC,
        OP.C2_OP ASC
    """


def build_ops_abertas_resumo_sql() -> str:
    """Agregação por filial/produto no mesmo universo de OPs abertas."""
    return f"""
    SELECT
        RTRIM(OP.C2_FILIAL) AS filial,
        RTRIM(OP.C2_PRODUTO) AS produto,
        RTRIM(COALESCE(MAX(P.B1_DESC), '')) AS descricao_produto,
        RTRIM(COALESCE(MAX(P.B1_TIPO), '')) AS tipo_produto,
        COUNT(*) AS quantidade_ops_abertas,
        CAST(SUM(ISNULL(OP.C2_QUANT, 0)) AS FLOAT) AS quantidade_total_ops,
        CAST(SUM(ISNULL(OP.C2_QUJE, 0)) AS FLOAT) AS quantidade_total_produzida,
        CAST(SUM(OP.C2_QUANT - OP.C2_QUJE) AS FLOAT) AS saldo_total_ops,
        CONVERT(
            VARCHAR(10),
            MIN(TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(OP.C2_DATPRF)), ''), 112)),
            23
        ) AS primeira_data_prevista_op,
        CONVERT(
            VARCHAR(10),
            MAX(TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(OP.C2_DATPRF)), ''), 112)),
            23
        ) AS ultima_data_prevista_op
    FROM {PRODUCTION_ORDER_TABLE} OP WITH (NOLOCK)
    INNER JOIN {PRODUCT_TABLE} P WITH (NOLOCK)
        ON P.B1_COD = OP.C2_PRODUTO
       AND P.D_E_L_E_T_ = ''
    WHERE OP.D_E_L_E_T_ = ''
      AND {_OPEN_BALANCE_SQL}
      AND {_OPEN_FINISH_SQL}
      AND {_FINISHED_GOOD_SQL}
    GROUP BY
        OP.C2_FILIAL,
        OP.C2_PRODUTO
    ORDER BY
        OP.C2_FILIAL,
        OP.C2_PRODUTO
    """
