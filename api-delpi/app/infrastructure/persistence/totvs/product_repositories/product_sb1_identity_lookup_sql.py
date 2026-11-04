"""Consulta somente leitura SB1 — identidade exata em lote (B1_COD / B1_REFEREN).

Sem LIKE. Sem TOP 1 que esconda ambiguidade. Chunk padrão alinhado a SA5.
"""

from __future__ import annotations

CHUNK_SIZE = 400


def chunk_values(values: list[str], chunk_size: int = CHUNK_SIZE) -> list[list[str]]:
    size = max(1, int(chunk_size))
    return [values[start : start + size] for start in range(0, len(values), size)]


def lookup_by_codes_sql(code_count: int) -> str:
    if code_count < 1:
        raise ValueError("lookup_by_codes exige ao menos um código.")
    placeholders = ", ".join("?" for _ in range(code_count))
    return f"""
        SELECT
            RTRIM(SB1.B1_COD) AS product_code,
            RTRIM(ISNULL(SB1.B1_DESC, '')) AS description,
            RTRIM(ISNULL(SB1.B1_TIPO, '')) AS product_type,
            RTRIM(ISNULL(SB1.B1_UM, '')) AS unit,
            RTRIM(ISNULL(SB1.B1_GRUPO, '')) AS group_code,
            RTRIM(ISNULL(SB1.B1_REFEREN, '')) AS customer_reference,
            RTRIM(ISNULL(SB1.B1_MSBLQL, '')) AS blocked_flag
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.D_E_L_E_T_ = ''
          AND RTRIM(SB1.B1_COD) IN ({placeholders})
    """


def lookup_by_customer_references_sql(ref_count: int) -> str:
    if ref_count < 1:
        raise ValueError("lookup_by_customer_references exige ao menos uma referência.")
    placeholders = ", ".join("?" for _ in range(ref_count))
    return f"""
        SELECT
            RTRIM(SB1.B1_COD) AS product_code,
            RTRIM(ISNULL(SB1.B1_DESC, '')) AS description,
            RTRIM(ISNULL(SB1.B1_TIPO, '')) AS product_type,
            RTRIM(ISNULL(SB1.B1_UM, '')) AS unit,
            RTRIM(ISNULL(SB1.B1_GRUPO, '')) AS group_code,
            RTRIM(ISNULL(SB1.B1_REFEREN, '')) AS customer_reference,
            RTRIM(ISNULL(SB1.B1_MSBLQL, '')) AS blocked_flag
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.D_E_L_E_T_ = ''
          AND RTRIM(SB1.B1_REFEREN) COLLATE Latin1_General_CI_AI IN ({placeholders})
    """
