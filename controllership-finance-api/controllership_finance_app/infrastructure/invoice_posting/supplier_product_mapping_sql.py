"""Consulta somente leitura de SA5010 + SB1010.

A5_FILIAL não participa. A SA5 da Delpi é compartilhada entre as filiais.
A correspondência é exata depois do RTRIM do campo CHAR. Sem LIKE e sem TOP.
"""

from __future__ import annotations

CHUNK_SIZE = 400


def supplier_product_mapping_sql(code_count: int) -> str:
    if code_count < 1:
        raise ValueError("A consulta de Produto x Fornecedor exige ao menos um código.")
    placeholders = ", ".join("?" for _ in range(code_count))
    return f"""
        SELECT
            RTRIM(SA5.A5_CODPRF) AS supplier_product_code,
            RTRIM(SA5.A5_PRODUTO) AS internal_product_code,
            RTRIM(ISNULL(SB1.B1_DESC, '')) AS internal_product_description
        FROM SA5010 SA5 WITH (NOLOCK)
        LEFT JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.D_E_L_E_T_ = ''
           AND RTRIM(SB1.B1_COD) = RTRIM(SA5.A5_PRODUTO)
        WHERE SA5.D_E_L_E_T_ = ''
          AND RTRIM(SA5.A5_FORNECE) = ?
          AND RTRIM(SA5.A5_LOJA) = ?
          AND RTRIM(SA5.A5_CODPRF) IN ({placeholders})
    """


def chunk_supplier_product_codes(codes: list[str], chunk_size: int = CHUNK_SIZE) -> list[list[str]]:
    size = max(1, int(chunk_size))
    return [codes[start : start + size] for start in range(0, len(codes), size)]
