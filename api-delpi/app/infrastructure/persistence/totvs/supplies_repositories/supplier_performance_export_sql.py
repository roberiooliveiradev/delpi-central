"""IDF evidence export: same event/date grain as the existing score (read-only).

The delivery source intentionally mirrors the deployed IDF query. A separate
documented discrepancy with the general OTD product-scope filter must be
resolved as a business-rule change, never silently during an export feature.
"""
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_RAW_MATERIAL,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN,
)

MAX_EXPORT_ROWS_PER_SOURCE = 12000


def _filters(branches, date_from, date_to, supplier_code, supplier_store, *, quality):
    placeholders = ", ".join("?" for _ in branches)
    alias = "I" if quality else "V"
    date_column = "Data_Laudo" if quality else "DT_DIGITACAO"
    code_column = "Codigo_Fornecedor" if quality else "FORNECEDOR"
    store_column = "Loja_Fornecedor" if quality else "LOJA"
    clause = (
        f"{alias}.{'Filial' if quality else 'FILIAL'} IN ({placeholders}) "
        f"AND {alias}.{date_column} >= ? "
        f"AND {alias}.{date_column} < DATEADD(day, 1, CAST(? AS date))"
    )
    params = [*branches, date_from, date_to]
    if quality:
        clause += (
            f" AND (LEFT({alias}.Codigo_Produto, {SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN}) = ? "
            "OR EXISTS (SELECT 1 FROM dbo.SB1010 P "
            "WHERE P.D_E_L_E_T_ = '' AND P.B1_COD = I.Codigo_Produto "
            "AND P.B1_TIPO = ?))"
        )
        params.extend((SUPPLIES_OTD_PRODUCT_CODE_PREFIX, PRODUCT_TYPE_RAW_MATERIAL))
    if supplier_code is not None:
        clause += f" AND RTRIM(LTRIM({alias}.{code_column})) = ?"
        clause += f" AND RTRIM(LTRIM({alias}.{store_column})) = ?"
        params.extend((supplier_code, supplier_store))
    return clause, tuple(params)


def build_inspection_evidence_sql(branches, date_from, date_to, supplier_code=None, supplier_store=None):
    where, params = _filters(
        branches, date_from, date_to, supplier_code, supplier_store, quality=True
    )
    # Id_Inspecao is the same de-duplication grain used by the IDF denominator.
    sql = f"""
SELECT TOP {MAX_EXPORT_ROWS_PER_SOURCE + 1}
    I.Filial AS branch,
    CAST(I.Id_Inspecao AS VARCHAR(40)) AS inspection_id,
    RTRIM(LTRIM(I.Codigo_Fornecedor)) AS supplier_code,
    RTRIM(LTRIM(I.Loja_Fornecedor)) AS supplier_store,
    MAX(I.Nome_Fornecedor) AS supplier_name,
    CONVERT(VARCHAR(10), MAX(I.Data_Recebimento), 23) AS receipt_date,
    CONVERT(VARCHAR(10), MAX(I.Data_Laudo), 23) AS report_date,
    CONVERT(VARCHAR(8), MAX(I.Hora_Laudo), 108) AS report_time,
    MAX(I.Nota_Fiscal) AS invoice_number,
    MAX(I.Serie_Nota_Fiscal) AS invoice_series,
    MAX(I.Item_Nota_Fiscal) AS invoice_item,
    MAX(I.Codigo_Produto) AS product_code,
    MAX(I.Lote) AS lot,
    MAX(I.Lote_Fornecedor) AS supplier_lot,
    MAX(I.Quantidade) AS quantity,
    MAX(I.Unidade_Medida) AS unit,
    MAX(I.Codigo_Situacao) AS situation_code,
    MAX(I.Status_Inspecao) AS inspection_status,
    MAX(I.Resultado_Resumo) AS result_summary,
    MAX(I.Codigo_Laudo) AS report_code,
    MAX(I.Justificativa_Laudo) AS report_justification,
    MAX(I.Nome_Ensaiador) AS inspector,
    MAX(I.Qtde_Ensaios) AS test_count,
    MAX(I.Qtde_Ensaios_Reprovados) AS rejected_test_count,
    MAX(I.Eh_Aprovada) AS approved,
    MAX(I.Eh_Rejeitada) AS rejected,
    MAX(CASE WHEN I.Codigo_Situacao = '5' THEN 1 ELSE 0 END) AS conditional,
    MAX(CASE WHEN I.Codigo_Situacao = '4' THEN 1 ELSE 0 END) AS urgent
FROM dbo.vw_minha_delpi_inspecoes_entrada_historico_tela I
WHERE {where}
GROUP BY I.Filial, I.Id_Inspecao, RTRIM(LTRIM(I.Codigo_Fornecedor)), RTRIM(LTRIM(I.Loja_Fornecedor))
ORDER BY branch, supplier_code, supplier_store, inspection_id
"""
    return sql, params


def build_delivery_evidence_sql(branches, date_from, date_to, supplier_code=None, supplier_store=None):
    where, params = _filters(
        branches, date_from, date_to, supplier_code, supplier_store, quality=False
    )
    sql = f"""
SELECT TOP {MAX_EXPORT_ROWS_PER_SOURCE + 1}
    V.FILIAL AS branch,
    RTRIM(LTRIM(V.FORNECEDOR)) AS supplier_code,
    RTRIM(LTRIM(V.LOJA)) AS supplier_store,
    V.NOME_FORNECEDOR AS supplier_name,
    V.DOCUMENTO AS document,
    V.NUMERO_PEDIDO AS order_number,
    V.ITEM_PEDIDO AS order_item,
    V.PRODUTO AS product_code,
    V.DESCRICAO_PRODUTO AS product_description,
    V.TIPO_PRODUTO AS product_type,
    V.QUANTIDADE AS quantity,
    CONVERT(VARCHAR(10), V.DT_EMISSAO_PC, 23) AS order_issue_date,
    CONVERT(VARCHAR(10), V.DT_ENTREGA, 23) AS expected_delivery_date,
    CONVERT(VARCHAR(10), V.DT_DIGITACAO, 23) AS receipt_entry_date,
    CONVERT(VARCHAR(10), V.DT_EMISSAO_NF, 23) AS invoice_issue_date,
    V.DIAS AS days_diff
FROM dbo.VW_PONTUALIDADE_FORNECEDORES V
WHERE {where}
ORDER BY branch, supplier_code, supplier_store, V.DT_DIGITACAO, V.NUMERO_PEDIDO, V.ITEM_PEDIDO
"""
    return sql, params
