"""Read-only SQL for the entry-audit Protheus extracts.

The BFF owns the fiscal rules. These statements only filter and project
the physical columns inventoried in the entry-audit contract. Bind
parameters only — caller values never reach the SQL text.
"""

from __future__ import annotations

from typing import Any


def _species_clause(column: str, species: list[str]) -> tuple[str, list[Any]]:
    placeholders = ", ".join("?" for _ in species)
    return f"RTRIM({column}) IN ({placeholders})", list(species)


def _page_clause() -> str:
    return "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"


def documents_sql(species: list[str]) -> tuple[str, list[str]]:
    species_sql, _ = _species_clause("SF1.F1_ESPECIE", species)
    sql = f"""
SELECT RTRIM(SF1.F1_FILIAL) AS branch,
       RTRIM(SF1.F1_DOC) AS document_number,
       RTRIM(SF1.F1_SERIE) AS series,
       RTRIM(SF1.F1_FORNECE) AS supplier_code,
       RTRIM(SF1.F1_LOJA) AS supplier_store,
       RTRIM(SA2.A2_NOME) AS supplier_name,
       RTRIM(SA2.A2_CGC) AS supplier_tax_id,
       RTRIM(SA2.A2_EST) AS supplier_state,
       RTRIM(SF1.F1_ESPECIE) AS species,
       RTRIM(SF1.F1_TIPO) AS invoice_type,
       RTRIM(SF1.F1_FORMUL) AS own_form,
       RTRIM(SF1.F1_CHVNFE) AS access_key,
       RTRIM(SF1.F1_EMISSAO) AS issue_date,
       RTRIM(SF1.F1_RECBMTO) AS received_date,
       SF1.F1_FRETE AS freight_amount,
       SF1.F1_DESPESA AS expense_amount,
       SF1.F1_BASEICM AS icms_base,
       SF1.F1_VALICM AS icms_amount,
       SF1.F1_BASEIPI AS ipi_base,
       SF1.F1_VALIPI AS ipi_amount,
       SF1.F1_VALMERC AS goods_amount,
       SF1.F1_VALBRUT AS gross_amount,
       SF1.F1_DESCONT AS discount_amount,
       SF1.F1_BRICMS AS st_base,
       SF1.F1_ICMSRET AS st_amount,
       SF1.F1_SEGURO AS insurance_amount,
       COUNT(*) OVER() AS total_count
  FROM SF1010 SF1 WITH (NOLOCK)
  LEFT JOIN SA2010 SA2 WITH (NOLOCK)
    ON SA2.D_E_L_E_T_ = ' '
   AND SA2.A2_FILIAL = ''
   AND SA2.A2_COD = SF1.F1_FORNECE
   AND SA2.A2_LOJA = SF1.F1_LOJA
 WHERE SF1.D_E_L_E_T_ = ' '
   AND SF1.F1_FILIAL = ?
   AND SF1.F1_RECBMTO >= ?
   AND SF1.F1_RECBMTO <= ?
   AND {species_sql}
 ORDER BY SF1.F1_RECBMTO, SF1.F1_DOC, SF1.F1_SERIE, SF1.F1_FORNECE, SF1.F1_LOJA
 {_page_clause()}
"""
    return sql, ["branch", "received_from", "received_to", *species, "offset", "page_size"]


def items_sql(species: list[str]) -> tuple[str, list[str]]:
    species_sql, _ = _species_clause("SF1.F1_ESPECIE", species)
    sql = f"""
SELECT RTRIM(SD1.D1_FILIAL) AS branch,
       RTRIM(SD1.D1_DOC) AS document_number,
       RTRIM(SD1.D1_SERIE) AS series,
       RTRIM(SD1.D1_FORNECE) AS supplier_code,
       RTRIM(SD1.D1_LOJA) AS supplier_store,
       RTRIM(SD1.D1_ITEM) AS item,
       RTRIM(SD1.D1_COD) AS product_code,
       RTRIM(SD1.D1_CF) AS cfop,
       RTRIM(SD1.D1_CLASFIS) AS tax_situation,
       RTRIM(SD1.D1_TES) AS tes,
       SD1.D1_QUANT AS quantity,
       SD1.D1_VUNIT AS unit_price,
       SD1.D1_TOTAL AS total_amount,
       SD1.D1_BASEICM AS icms_base,
       SD1.D1_PICM AS icms_rate,
       SD1.D1_VALICM AS icms_amount,
       SD1.D1_BASEIPI AS ipi_base,
       SD1.D1_IPI AS ipi_rate,
       SD1.D1_VALIPI AS ipi_amount,
       SD1.D1_ICMSRET AS st_amount,
       SD1.D1_VALDESC AS discount_amount,
       COUNT(*) OVER() AS total_count
  FROM SD1010 SD1 WITH (NOLOCK)
 INNER JOIN SF1010 SF1 WITH (NOLOCK)
    ON SF1.D_E_L_E_T_ = ' '
   AND SF1.F1_FILIAL = SD1.D1_FILIAL
   AND SF1.F1_DOC = SD1.D1_DOC
   AND SF1.F1_SERIE = SD1.D1_SERIE
   AND SF1.F1_FORNECE = SD1.D1_FORNECE
   AND SF1.F1_LOJA = SD1.D1_LOJA
 WHERE SD1.D_E_L_E_T_ = ' '
   AND SF1.F1_FILIAL = ?
   AND SF1.F1_RECBMTO >= ?
   AND SF1.F1_RECBMTO <= ?
   AND {species_sql}
 ORDER BY SF1.F1_RECBMTO, SD1.D1_DOC, SD1.D1_SERIE, SD1.D1_FORNECE, SD1.D1_LOJA, SD1.D1_ITEM
 {_page_clause()}
"""
    return sql, ["branch", "received_from", "received_to", *species, "offset", "page_size"]


def fiscal_book_sql(species: list[str]) -> tuple[str, list[str]]:
    species_sql, _ = _species_clause("SF1.F1_ESPECIE", species)
    sql = f"""
SELECT RTRIM(SFT.FT_FILIAL) AS branch,
       RTRIM(SFT.FT_NFISCAL) AS document_number,
       RTRIM(SFT.FT_SERIE) AS series,
       RTRIM(SFT.FT_CLIEFOR) AS supplier_code,
       RTRIM(SFT.FT_LOJA) AS supplier_store,
       RTRIM(SFT.FT_ITEM) AS item,
       RTRIM(SFT.FT_CHVNFE) AS access_key,
       RTRIM(SFT.FT_TIPOMOV) AS movement_type,
       SFT.FT_VALICM AS icms_amount,
       SFT.FT_ISENICM AS icms_exempt_amount,
       SFT.FT_OUTRICM AS icms_other_amount,
       SFT.FT_VALIPI AS ipi_amount,
       RTRIM(SFT.FT_DTCANC) AS cancelled_on,
       RTRIM(SFT.FT_ENTRADA) AS entered_on,
       COUNT(*) OVER() AS total_count
  FROM SFT010 SFT WITH (NOLOCK)
 INNER JOIN SF1010 SF1 WITH (NOLOCK)
    ON SF1.D_E_L_E_T_ = ' '
   AND SF1.F1_FILIAL = SFT.FT_FILIAL
   AND SF1.F1_DOC = SFT.FT_NFISCAL
   AND SF1.F1_SERIE = SFT.FT_SERIE
   AND SF1.F1_FORNECE = SFT.FT_CLIEFOR
   AND SF1.F1_LOJA = SFT.FT_LOJA
 WHERE SFT.D_E_L_E_T_ = ' '
   AND SFT.FT_TIPOMOV = 'E'
   AND (SFT.FT_DTCANC IS NULL OR RTRIM(SFT.FT_DTCANC) = '')
   AND SF1.F1_FILIAL = ?
   AND SF1.F1_RECBMTO >= ?
   AND SF1.F1_RECBMTO <= ?
   AND {species_sql}
 ORDER BY SF1.F1_RECBMTO, SFT.FT_NFISCAL, SFT.FT_SERIE, SFT.FT_CLIEFOR, SFT.FT_LOJA, SFT.FT_ITEM
 {_page_clause()}
"""
    return sql, ["branch", "received_from", "received_to", *species, "offset", "page_size"]


def tes_sql() -> str:
    return """
WITH ranked AS (
    SELECT RTRIM(SF4.F4_CODIGO) AS code,
           RTRIM(SF4.F4_TEXTO) AS description,
           RTRIM(SF4.F4_ICM) AS calculates_icms,
           RTRIM(SF4.F4_CREDICM) AS credits_icms,
           RTRIM(SF4.F4_LFICM) AS icms_book,
           RTRIM(SF4.F4_IPI) AS calculates_ipi,
           RTRIM(SF4.F4_CREDIPI) AS credits_ipi,
           RTRIM(SF4.F4_LFIPI) AS ipi_book,
           RTRIM(SF4.F4_CONSUMO) AS consumption_material,
           RTRIM(SF4.F4_TIPO) AS tes_type,
           RTRIM(SF4.F4_CF) AS fiscal_code,
           ROW_NUMBER() OVER (
               PARTITION BY RTRIM(SF4.F4_CODIGO)
               ORDER BY CASE WHEN RTRIM(SF4.F4_FILIAL) = '01' THEN 0 ELSE 1 END,
                        SF4.R_E_C_N_O_
           ) AS rn
      FROM SF4010 SF4 WITH (NOLOCK)
     WHERE SF4.D_E_L_E_T_ = ' '
       AND RTRIM(SF4.F4_FILIAL) IN ('', '01')
)
SELECT code, description, calculates_icms, credits_icms, icms_book,
       calculates_ipi, credits_ipi, ipi_book, consumption_material,
       tes_type, fiscal_code,
       COUNT(*) OVER() AS total_count
  FROM ranked
 WHERE rn = 1
 ORDER BY code
 OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


def branches_sql() -> str:
    return """
SELECT RTRIM(M0_CODFIL) AS code,
       RTRIM(M0_CODIGO) AS company_code,
       RTRIM(M0_NOMECOM) AS name,
       RTRIM(M0_ESTENT) AS state,
       RTRIM(M0_CGC) AS tax_id
  FROM SYS_COMPANY WITH (NOLOCK)
 WHERE D_E_L_E_T_ = ' '
   AND RTRIM(M0_CODIGO) = '01'
   AND RTRIM(M0_CODFIL) IN ('01', '02')
 ORDER BY RTRIM(M0_CODFIL)
"""
