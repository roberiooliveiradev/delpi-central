"""Itens de NF de saída por cliente/loja/filial — quantidade física, lote de produtos.

Somente leitura. Soft-delete SF2/SD2 exclui canceladas. Tipo D = devolução.
Quantidades retornadas como texto decimal (sem float na autoridade de cálculo).

Unidade efetiva: D2_UM (item faturado). B1_UM é catálogo auxiliar, filtrado por
B1_FILIAL = D2_FILIAL para não duplicar linhas SB1.
"""

from __future__ import annotations

CHUNK_SIZE = 400


def chunk_codes(codes: list[str], chunk_size: int = CHUNK_SIZE) -> list[list[str]]:
    size = max(1, int(chunk_size))
    return [codes[i : i + size] for i in range(0, len(codes), size)]


def line_items_sql(*, product_count: int, exclude_returns: bool) -> str:
    if product_count < 1:
        raise ValueError("product_count deve ser >= 1")
    placeholders = ", ".join("?" for _ in range(product_count))
    return_clause = "AND ISNULL(F2.F2_TIPO, ISNULL(D2.D2_TIPO, '')) <> 'D'" if exclude_returns else ""
    return f"""
        SELECT
            RTRIM(D2.D2_FILIAL) AS branch,
            RTRIM(D2.D2_DOC) AS invoice_number,
            RTRIM(D2.D2_SERIE) AS invoice_series,
            RTRIM(D2.D2_ITEM) AS item,
            RTRIM(D2.D2_COD) AS product_code,
            RTRIM(ISNULL(SB1.B1_DESC, '')) AS product_description,
            RTRIM(ISNULL(NULLIF(RTRIM(D2.D2_UM), ''), ISNULL(SB1.B1_UM, ''))) AS unit,
            RTRIM(ISNULL(D2.D2_UM, '')) AS invoice_unit,
            RTRIM(ISNULL(SB1.B1_UM, '')) AS catalog_unit,
            CONVERT(VARCHAR(40), D2.D2_QUANT) AS quantity,
            RTRIM(D2.D2_EMISSAO) AS issue_date_raw,
            RTRIM(D2.D2_CLIENTE) AS customer_code,
            RTRIM(D2.D2_LOJA) AS customer_store,
            RTRIM(ISNULL(F2.F2_TIPO, ISNULL(D2.D2_TIPO, ''))) AS doc_type
        FROM SD2010 D2 WITH (NOLOCK)
        INNER JOIN SF2010 F2 WITH (NOLOCK)
            ON F2.F2_FILIAL = D2.D2_FILIAL
            AND F2.F2_DOC = D2.D2_DOC
            AND F2.F2_SERIE = D2.D2_SERIE
            AND F2.D_E_L_E_T_ = ''
        LEFT JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = D2.D2_COD
            AND SB1.B1_FILIAL = D2.D2_FILIAL
            AND SB1.D_E_L_E_T_ = ''
        WHERE D2.D_E_L_E_T_ = ''
          AND RTRIM(D2.D2_FILIAL) = ?
          AND RTRIM(D2.D2_CLIENTE) = ?
          AND RTRIM(D2.D2_LOJA) = ?
          AND D2.D2_EMISSAO >= ?
          AND D2.D2_EMISSAO <= ?
          AND RTRIM(D2.D2_COD) IN ({placeholders})
          {return_clause}
        ORDER BY D2.D2_EMISSAO ASC, D2.D2_DOC ASC, D2.D2_ITEM ASC
    """
