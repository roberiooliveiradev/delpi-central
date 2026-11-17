"""Leitura fiscal do impacto do frete sobre compras nacionais.

A base (denominador) inclui TODAS as NFs nacionais válidas, inclusive sem CT-e.
Os custos seguem DLP02R01: D1_CUSTO das mercadorias e das linhas de CT-e.
Os vínculos SF8 são deduplicados antes do join com os itens, evitando que
repetições de vínculo multipliquem os valores de frete.
"""
from __future__ import annotations

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

MAX_INVOICES = 50000
BRAZILIAN_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT",
    "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS",
    "RO", "RR", "SC", "SP", "SE", "TO",
)


def build_freight_impact_sql(
    branches: list[str], date_from: str, date_to: str
) -> tuple[str, tuple[str, ...]]:
    """Parâmetros seguros: filiais concretas e datas no formato YYYYMMDD."""
    if not branches or any(code not in ("01", "02") for code in branches):
        raise ValueError("Filiais inválidas")
    branch_marks = ", ".join("?" for _ in branches)
    uf_marks = ", ".join("?" for _ in BRAZILIAN_STATES)
    sql = f"""
    WITH PURCHASES AS (
        SELECT
            F1.F1_FILIAL AS branch,
            F1.F1_DOC AS invoice_document,
            F1.F1_SERIE AS invoice_series,
            F1.F1_FORNECE AS supplier_code,
            F1.F1_LOJA AS supplier_store,
            MAX(SA2.A2_NREDUZ) AS supplier_name,
            MAX(F1.F1_EMISSAO) AS issue_date,
            CAST(SUM(COALESCE(D1.D1_CUSTO, 0)) AS DECIMAL(19, 4)) AS purchase_cost
        FROM SF1010 F1 WITH (NOLOCK)
        INNER JOIN SA2010 SA2 WITH (NOLOCK)
            ON SA2.A2_COD = F1.F1_FORNECE
           AND SA2.A2_LOJA = F1.F1_LOJA
           AND SA2.A2_FILIAL = ''
           AND SA2.D_E_L_E_T_ = ''
           AND SA2.A2_EST IN ({uf_marks})
        INNER JOIN SD1010 D1 WITH (NOLOCK)
            ON D1.D1_FILIAL = F1.F1_FILIAL
           AND D1.D1_DOC = F1.F1_DOC
           AND D1.D1_SERIE = F1.F1_SERIE
           AND D1.D1_FORNECE = F1.F1_FORNECE
           AND D1.D1_LOJA = F1.F1_LOJA
           AND D1.D1_TIPO = 'N'
           AND D1.D_E_L_E_T_ = ''
        WHERE F1.D_E_L_E_T_ = ''
          AND F1.F1_TIPO = 'N'
          AND F1.F1_ESPECIE = 'SPED'
          AND F1.F1_FILIAL IN ({branch_marks})
          AND F1.F1_EMISSAO BETWEEN ? AND ?
        GROUP BY
            F1.F1_FILIAL, F1.F1_DOC, F1.F1_SERIE,
            F1.F1_FORNECE, F1.F1_LOJA
    ),
    FREIGHT_LINKS AS (
        SELECT DISTINCT
            F8.F8_FILIAL AS branch,
            F8.F8_NFORIG AS invoice_document,
            COALESCE(NULLIF(RTRIM(F8.F8_SERORIG), ''),
                     RTRIM(F8.F8_SDOCORI)) AS invoice_series,
            F8.F8_FORNECE AS supplier_code,
            F8.F8_LOJA AS supplier_store,
            F8.F8_NFDIFRE AS freight_document,
            COALESCE(NULLIF(RTRIM(F8.F8_SEDIFRE), ''),
                     RTRIM(F8.F8_SDOCFRE)) AS freight_series,
            F8.F8_TRANSP AS carrier_code,
            F8.F8_LOJTRAN AS carrier_store
        FROM SF8010 F8 WITH (NOLOCK)
        WHERE F8.D_E_L_E_T_ = ''
          AND F8.F8_TIPO = 'F'
          AND F8.F8_FILIAL IN ({branch_marks})
    ),
    FREIGHT_AGG AS (
        SELECT
            P.branch, P.invoice_document, P.invoice_series,
            P.supplier_code, P.supplier_store,
            CAST(SUM(COALESCE(CTI.D1_CUSTO, 0)) AS DECIMAL(19, 4)) AS freight_cost,
            COUNT(DISTINCT
                CONCAT(RTRIM(L.freight_document), '|', RTRIM(L.freight_series),
                       '|', RTRIM(L.carrier_code), '|', RTRIM(L.carrier_store))
            ) AS cte_count
        FROM PURCHASES P
        INNER JOIN FREIGHT_LINKS L
            ON L.branch = P.branch
           AND L.invoice_document = P.invoice_document
           AND L.invoice_series = P.invoice_series
           AND L.supplier_code = P.supplier_code
           AND L.supplier_store = P.supplier_store
        INNER JOIN SF1010 CTE WITH (NOLOCK)
            ON CTE.F1_FILIAL = L.branch
           AND CTE.F1_DOC = L.freight_document
           AND CTE.F1_SERIE = L.freight_series
           AND CTE.F1_FORNECE = L.carrier_code
           AND CTE.F1_LOJA = L.carrier_store
           AND CTE.F1_ESPECIE = 'CTE'
           AND CTE.D_E_L_E_T_ = ''
        INNER JOIN SD1010 CTI WITH (NOLOCK)
            ON CTI.D1_FILIAL = L.branch
           AND CTI.D1_DOC = L.freight_document
           AND CTI.D1_SERIE = L.freight_series
           AND CTI.D1_FORNECE = L.carrier_code
           AND CTI.D1_LOJA = L.carrier_store
           AND CTI.D1_NFORI = L.invoice_document
           AND CTI.D1_SERIORI = L.invoice_series
           AND CTI.D_E_L_E_T_ = ''
        INNER JOIN SD1010 ORI WITH (NOLOCK)
            ON ORI.D1_FILIAL = P.branch
           AND ORI.D1_DOC = P.invoice_document
           AND ORI.D1_SERIE = P.invoice_series
           AND ORI.D1_FORNECE = P.supplier_code
           AND ORI.D1_LOJA = P.supplier_store
           AND ORI.D1_ITEM = CTI.D1_ITEMORI
           AND ORI.D1_TIPO = 'N'
           AND ORI.D_E_L_E_T_ = ''
        GROUP BY
            P.branch, P.invoice_document, P.invoice_series,
            P.supplier_code, P.supplier_store
    )
    SELECT TOP ({MAX_INVOICES + 1})
        RTRIM(P.branch) AS branch,
        RTRIM(P.invoice_document) AS invoice_document,
        RTRIM(P.invoice_series) AS invoice_series,
        RTRIM(P.supplier_code) AS supplier_code,
        RTRIM(P.supplier_store) AS supplier_store,
        RTRIM(P.supplier_name) AS supplier_name,
        RTRIM(P.issue_date) AS issue_date,
        P.purchase_cost,
        COALESCE(F.freight_cost, 0) AS freight_cost,
        COALESCE(F.cte_count, 0) AS cte_count
    FROM PURCHASES P
    LEFT JOIN FREIGHT_AGG F
        ON F.branch = P.branch
       AND F.invoice_document = P.invoice_document
       AND F.invoice_series = P.invoice_series
       AND F.supplier_code = P.supplier_code
       AND F.supplier_store = P.supplier_store
    ORDER BY P.branch, P.issue_date, P.invoice_document, P.invoice_series
    """
    params = (
        *BRAZILIAN_STATES, *branches, date_from.replace("-", ""),
        date_to.replace("-", ""), *branches,
    )
    return sql, params


class FreightImpactRepository(BaseRepository):
    def list_invoices(
        self, *, branches: list[str], date_from: str, date_to: str
    ) -> list[dict]:
        sql, params = build_freight_impact_sql(branches, date_from, date_to)
        with self:
            rows = self.execute_query(sql, params)
        if len(rows) > MAX_INVOICES:
            raise ValueError(
                "Período com mais de 50.000 NFs. Reduza as datas ou selecione uma filial."
            )
        return rows
