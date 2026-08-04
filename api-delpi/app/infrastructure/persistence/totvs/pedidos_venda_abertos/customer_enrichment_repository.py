from __future__ import annotations

from typing import Any, Sequence

from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerBilling12mRow,
    CustomerBillingMonthRow,
    CustomerEnrichmentRepositoryPort,
    CustomerGeoRow,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


def _trim(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value: Any) -> str | None:
    text = _trim(value)
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def _to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class CustomerEnrichmentRepository(BaseRepository, CustomerEnrichmentRepositoryPort):
    def fetch_customer_geo(
        self,
        *,
        customers: Sequence[tuple[str, str]],
    ) -> list[CustomerGeoRow]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []

        # SQL Server: OR de pares (limitado) — evita TVP.
        clauses: list[str] = []
        params: list[str] = []
        for code, store in pairs:
            clauses.append("(SA1.A1_COD = ? AND SA1.A1_LOJA = ?)")
            params.extend([code, store])
        where_pairs = " OR ".join(clauses)
        sql = f"""
            SELECT
                SA1.A1_COD AS customer_code,
                SA1.A1_LOJA AS customer_store,
                SA1.A1_MUN AS city,
                SA1.A1_EST AS state
              FROM SA1010 SA1 WITH (NOLOCK)
             WHERE SA1.D_E_L_E_T_ = ''
               AND ({where_pairs})
        """
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        return [
            CustomerGeoRow(
                customer_code=_trim(row.get("customer_code")),
                customer_store=_trim(row.get("customer_store")),
                city=_trim(row.get("city")) or None,
                state=_trim(row.get("state")) or None,
            )
            for row in rows
        ]

    def fetch_billing_12m(
        self,
        *,
        customers: Sequence[tuple[str, str]],
        start_date: str,
        mid_date: str,
        end_date: str,
    ) -> list[CustomerBilling12mRow]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []

        clauses: list[str] = []
        pair_params: list[str] = []
        for code, store in pairs:
            clauses.append("(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)")
            pair_params.extend([code, store])
        where_pairs = " OR ".join(clauses)

        sql = f"""
            WITH note_base AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    D2.D2_FILIAL AS branch,
                    D2.D2_DOC AS invoice_number,
                    D2.D2_SERIE AS invoice_series,
                    MAX(D2.D2_EMISSAO) AS issue_date,
                    MAX(CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))) AS note_value,
                    MAX(ISNULL(F2.F2_TIPO, D2.D2_TIPO)) AS doc_type
                  FROM SD2010 D2 WITH (NOLOCK)
                  INNER JOIN SF2010 F2 WITH (NOLOCK)
                    ON F2.F2_FILIAL = D2.D2_FILIAL
                   AND F2.F2_DOC = D2.D2_DOC
                   AND F2.F2_SERIE = D2.D2_SERIE
                   AND F2.D_E_L_E_T_ = ''
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({where_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                 GROUP BY
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    D2.D2_FILIAL,
                    D2.D2_DOC,
                    D2.D2_SERIE
            )
            SELECT
                customer_code,
                customer_store,
                MAX(issue_date) AS last_purchase_date,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        ELSE note_value
                    END
                ) AS billed_12m,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        WHEN issue_date >= ? THEN note_value
                        ELSE 0
                    END
                ) AS billed_recent_6m,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        WHEN issue_date < ? THEN note_value
                        ELSE 0
                    END
                ) AS billed_prior_6m
              FROM note_base
             GROUP BY customer_code, customer_store
        """
        # mid_date: recente = [mid, end]; anterior = [start, mid)
        params = tuple(pair_params + [start_date, end_date, mid_date, mid_date])
        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            CustomerBilling12mRow(
                customer_code=_trim(row.get("customer_code")),
                customer_store=_trim(row.get("customer_store")),
                last_purchase_date=_iso_date(row.get("last_purchase_date")),
                billed_12m=_to_float(row.get("billed_12m")),
                billed_recent_6m=_to_float(row.get("billed_recent_6m")),
                billed_prior_6m=_to_float(row.get("billed_prior_6m")),
            )
            for row in rows
        ]

    def fetch_billing_monthly_series(
        self,
        *,
        customers: Sequence[tuple[str, str]],
        start_date: str,
        end_date: str,
    ) -> list[CustomerBillingMonthRow]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []

        clauses: list[str] = []
        pair_params: list[str] = []
        for code, store in pairs:
            clauses.append("(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)")
            pair_params.extend([code, store])
        where_pairs = " OR ".join(clauses)

        sql = f"""
            WITH note_base AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    D2.D2_FILIAL AS branch,
                    D2.D2_DOC AS invoice_number,
                    D2.D2_SERIE AS invoice_series,
                    MAX(D2.D2_EMISSAO) AS issue_date,
                    MAX(CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))) AS note_value,
                    MAX(ISNULL(F2.F2_TIPO, D2.D2_TIPO)) AS doc_type
                  FROM SD2010 D2 WITH (NOLOCK)
                  INNER JOIN SF2010 F2 WITH (NOLOCK)
                    ON F2.F2_FILIAL = D2.D2_FILIAL
                   AND F2.F2_DOC = D2.D2_DOC
                   AND F2.F2_SERIE = D2.D2_SERIE
                   AND F2.D_E_L_E_T_ = ''
                 WHERE D2.D_E_L_E_T_ = ''
                   AND ({where_pairs})
                   AND D2.D2_EMISSAO >= ?
                   AND D2.D2_EMISSAO <= ?
                 GROUP BY
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    D2.D2_FILIAL,
                    D2.D2_DOC,
                    D2.D2_SERIE
            )
            SELECT
                LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 6) AS year_month,
                SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        ELSE note_value
                    END
                ) AS billed_value
              FROM note_base
             GROUP BY LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 6)
             ORDER BY year_month ASC
        """
        params = tuple(pair_params + [start_date, end_date])
        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            CustomerBillingMonthRow(
                year_month=_trim(row.get("year_month")),
                billed_value=_to_float(row.get("billed_value")),
            )
            for row in rows
            if _trim(row.get("year_month"))
        ]
