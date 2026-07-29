"""SQL canônico — conciliação LNF com SF1010.

Notas ``F1_TIPO = 'B'`` (beneficiamento) gravam o partido em ``SA1010`` (cliente),
não em ``SA2010``. A solicitação LNF guarda ``A2_COD``/``A2_LOJA``; o match de
beneficiamento usa CNPJ (dígitos) entre SA1 do ERP e SA2 da solicitação.
"""
from __future__ import annotations

from typing import Any, Sequence


def _cgc_digits_expr(column_sql: str) -> str:
    """Normaliza CGC/CNPJ para comparação só com dígitos."""
    return (
        "REPLACE(REPLACE(REPLACE(REPLACE("
        f"RTRIM(ISNULL({column_sql}, '')), '.', ''), '/', ''), '-', ''), ' ', '')"
    )


def build_find_active_by_fiscal_keys_sql(
    keys: Sequence[dict[str, Any]],
) -> tuple[str, list[Any]]:
    """Monta SQL + params para match direto (SA2) ou beneficiamento (SA1↔SA2 via CNPJ).

    O SELECT projeta os códigos da **solicitação** (não necessariamente ``F1_FORNECE``),
    para o matching Python por chave fiscal continuar estável.
    """
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for raw in keys:
        branch = str(raw.get("branch_code") or "").strip()
        supplier = str(raw.get("supplier_code") or "").strip()
        store = str(raw.get("supplier_store") or "").strip()
        doc_key = str(raw.get("document_match_key") or "").strip()
        series = str(raw.get("series") or "").strip().upper()
        if not (branch and supplier and store and doc_key):
            continue
        token = (branch, supplier, store, doc_key, series)
        if token in seen:
            continue
        seen.add(token)
        unique.append(
            {
                "branch_code": branch,
                "supplier_code": supplier,
                "supplier_store": store,
                "document_match_key": doc_key,
                "series": series,
            }
        )

    if not unique:
        return "", []

    values_sql = ", ".join(["(?, ?, ?, ?, ?)"] * len(unique))
    params: list[Any] = []
    for key in unique:
        params.extend(
            [
                key["branch_code"],
                key["supplier_code"],
                key["supplier_store"],
                key["document_match_key"],
                key["series"],
            ]
        )

    sa1_cgc = _cgc_digits_expr("SA1.A1_CGC")
    sa2_cgc = _cgc_digits_expr("SA2.A2_CGC")

    sql = f"""
        ;WITH keys AS (
            SELECT
                RTRIM(branch_code) AS branch_code,
                RTRIM(supplier_code) AS supplier_code,
                RTRIM(supplier_store) AS supplier_store,
                RTRIM(document_match_key) AS document_match_key,
                UPPER(RTRIM(series)) AS series
            FROM (VALUES {values_sql}) AS v(
                branch_code,
                supplier_code,
                supplier_store,
                document_match_key,
                series
            )
        )
        SELECT
            k.branch_code AS branch_code,
            k.supplier_code AS supplier_code,
            k.supplier_store AS supplier_store,
            k.document_match_key AS document_match_key,
            k.series AS series,
            SF1.R_E_C_N_O_ AS sf1_recno,
            RTRIM(SF1.F1_DTDIGIT) AS erp_entry_date_raw,
            UPPER(RTRIM(SF1.F1_TIPO)) AS invoice_type,
            RTRIM(SF1.F1_FORNECE) AS erp_party_code,
            RTRIM(SF1.F1_LOJA) AS erp_party_store
        FROM keys k
        INNER JOIN SF1010 SF1 WITH (NOLOCK)
            ON RTRIM(SF1.F1_FILIAL) = k.branch_code
           AND RIGHT(REPLICATE('0', 9) + RTRIM(SF1.F1_DOC), 9) = k.document_match_key
           AND UPPER(RTRIM(SF1.F1_SERIE)) = k.series
           AND SF1.D_E_L_E_T_ = ''
           AND RTRIM(SF1.F1_DOC) NOT LIKE '%[^0-9]%'
           AND RTRIM(SF1.F1_DOC) <> ''
           AND (
                (
                    RTRIM(SF1.F1_FORNECE) = k.supplier_code
                    AND RTRIM(SF1.F1_LOJA) = k.supplier_store
                )
                OR (
                    UPPER(RTRIM(SF1.F1_TIPO)) = 'B'
                    AND EXISTS (
                        SELECT 1
                        FROM SA1010 SA1 WITH (NOLOCK)
                        INNER JOIN SA2010 SA2 WITH (NOLOCK)
                            ON {sa1_cgc} <> ''
                           AND {sa1_cgc} = {sa2_cgc}
                        WHERE SA1.D_E_L_E_T_ = ''
                          AND SA2.D_E_L_E_T_ = ''
                          AND RTRIM(SA1.A1_COD) = RTRIM(SF1.F1_FORNECE)
                          AND RTRIM(SA1.A1_LOJA) = RTRIM(SF1.F1_LOJA)
                          AND RTRIM(SA2.A2_COD) = k.supplier_code
                          AND RTRIM(SA2.A2_LOJA) = k.supplier_store
                    )
                )
           )
    """
    return sql, params
