"""Reuses the authoritative inspection and OTD views; never joins their facts."""

from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_RAW_MATERIAL,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN,
)

MAX_SOURCE_ROWS = 5000


def build_supplier_performance_sql(branches: list[str], date_from: str, date_to: str):
    placeholders = ", ".join("?" for _ in branches)
    sql = f"""
WITH inspection_facts AS (
    SELECT I.Filial AS branch, I.Id_Inspecao,
        RTRIM(I.Codigo_Fornecedor) AS supplier_code,
        RTRIM(I.Loja_Fornecedor) AS supplier_store,
        MAX(I.Nome_Fornecedor) AS supplier_name,
        MAX(I.Eh_Aprovada) AS approved, MAX(I.Eh_Rejeitada) AS rejected,
        MAX(CASE WHEN I.Codigo_Situacao = '5' THEN 1 ELSE 0 END) AS conditional_count,
        MAX(CASE WHEN I.Codigo_Situacao = '4' THEN 1 ELSE 0 END) AS urgent_count
    FROM dbo.vw_minha_delpi_inspecoes_entrada_historico_tela I
    WHERE I.Filial IN ({placeholders}) AND I.Data_Laudo >= ? AND I.Data_Laudo < DATEADD(day, 1, CAST(? AS date))
      AND (LEFT(I.Codigo_Produto, {SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN}) = ? OR EXISTS (
          SELECT 1 FROM dbo.SB1010 P
          WHERE P.D_E_L_E_T_ = '' AND P.B1_COD = I.Codigo_Produto AND P.B1_TIPO = ?
      ))
    GROUP BY I.Filial, I.Id_Inspecao, RTRIM(I.Codigo_Fornecedor), RTRIM(I.Loja_Fornecedor)
), source_counts AS (
    SELECT 'quality' AS source, branch, supplier_code, supplier_store,
        MAX(supplier_name) AS supplier_name,
        SUM(CASE WHEN approved + rejected = 1 THEN 1 ELSE 0 END) AS assessed_count,
        SUM(CASE WHEN approved = 1 AND rejected = 0 THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN approved + rejected = 1 THEN 0 ELSE 1 END) AS unknown_count,
        SUM(conditional_count) AS conditional_count, SUM(urgent_count) AS urgent_count
    FROM inspection_facts
    GROUP BY branch, supplier_code, supplier_store
    UNION ALL
    SELECT 'delivery', V.FILIAL, RTRIM(V.FORNECEDOR), RTRIM(V.LOJA), MAX(V.NOME_FORNECEDOR),
        COUNT(*), SUM(CASE WHEN V.DIAS >= 0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN V.DIAS IS NULL THEN 1 ELSE 0 END), 0, 0
    FROM dbo.VW_PONTUALIDADE_FORNECEDORES V
    WHERE V.FILIAL IN ({placeholders}) AND V.DT_DIGITACAO >= ? AND V.DT_DIGITACAO < DATEADD(day, 1, CAST(? AS date))
    GROUP BY V.FILIAL, RTRIM(V.FORNECEDOR), RTRIM(V.LOJA)
)
SELECT TOP {MAX_SOURCE_ROWS + 1} * FROM source_counts
ORDER BY supplier_code, supplier_store, branch, source
"""
    params = [
        *branches,
        date_from,
        date_to,
        SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
        PRODUCT_TYPE_RAW_MATERIAL,
        *branches,
        date_from,
        date_to,
    ]
    return sql, tuple(params)
