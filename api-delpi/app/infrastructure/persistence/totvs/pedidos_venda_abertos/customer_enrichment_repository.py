from __future__ import annotations

from typing import Any, Sequence

from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerBilling12mRow,
    CustomerBillingMonthRow,
    CustomerEnrichmentRepositoryPort,
    CustomerGeoRow,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    DEFAULT_BILLING_METRIC,
    DEFAULT_BILLING_NATURE,
    billing_12m_params,
    billing_series_params,
    build_customer_billing_12m_sql,
    build_customer_billing_series_sql,
    normalize_billing_metric,
    normalize_billing_nature,
    normalize_billing_series_recorte,
)


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
                SA1.A1_EST AS state,
                SA1.A1_CONTATO AS contact_name,
                SA1.A1_TEL AS phone,
                SA1.A1_EMAIL AS email
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
                contact_name=_trim(row.get("contact_name")) or None,
                phone=_trim(row.get("phone")) or None,
                email=_trim(row.get("email")) or None,
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
        nature: str = DEFAULT_BILLING_NATURE,
    ) -> list[CustomerBilling12mRow]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []

        nature = normalize_billing_nature(nature)
        clauses: list[str] = []
        pair_params: list[str] = []
        for code, store in pairs:
            clauses.append("(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)")
            pair_params.extend([code, store])
        where_pairs = " OR ".join(clauses)

        sql = build_customer_billing_12m_sql(where_pairs=where_pairs, nature=nature)
        params = billing_12m_params(
            pair_params=pair_params,
            start_date=start_date,
            mid_date=mid_date,
            end_date=end_date,
            nature=nature,
        )
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
        granularity: str = "month",
        nature: str = DEFAULT_BILLING_NATURE,
        metric: str = DEFAULT_BILLING_METRIC,
        product_codes: Sequence[str] | None = None,
        product_groups: Sequence[str] | None = None,
        market: str | None = None,
    ) -> list[CustomerBillingMonthRow]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []

        nature = normalize_billing_nature(nature)
        metric = normalize_billing_metric(metric)
        recorte = normalize_billing_series_recorte(
            product_codes=list(product_codes or []),
            product_groups=list(product_groups or []),
            market=market,
        )
        clauses: list[str] = []
        pair_params: list[str] = []
        for code, store in pairs:
            clauses.append("(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)")
            pair_params.extend([code, store])
        where_pairs = " OR ".join(clauses)

        sql = build_customer_billing_series_sql(
            where_pairs=where_pairs,
            granularity=granularity,
            nature=nature,
            metric=metric,
            recorte=recorte,
        )
        params = billing_series_params(
            pair_params=pair_params,
            start_date=start_date,
            end_date=end_date,
            nature=nature,
            metric=metric,
            recorte=recorte,
        )
        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            CustomerBillingMonthRow(
                year_month=_trim(row.get("year_month")),
                billed_value=_to_float(row.get("billed_value")),
                unit=_trim(row.get("unit")) or None,
                mixed_units=bool(int(row.get("mixed_units") or 0)),
            )
            for row in rows
            if _trim(row.get("year_month"))
        ]
