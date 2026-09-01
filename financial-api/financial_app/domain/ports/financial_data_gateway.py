from __future__ import annotations

from typing import Any, Protocol


class FinancialDataGateway(Protocol):
    """Contrato de leitura dos dados financeiros TOTVS expostos pela api-delpi.

    O BFF nunca fala SQL: a api-delpi permanece dona do contrato TOTVS puro e
    este port isola o Portal Financeiro do formato de transporte.
    """

    def fetch_delinquency_summary(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_delinquency_monthly(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        new_business_only: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_delinquency_aging(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_delinquency_customers(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str,
        search: str | None,
        only_with_delays: bool,
    ) -> dict[str, Any]: ...

    def fetch_delinquency_titles(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None,
        store_code: str | None,
        status: str,
        delay_range: str | None,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_filters(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_summary(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_series(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_ranking_centers(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        limit: int,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_ranking_suppliers(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        limit: int,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_cost_center_entries(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        supplier_code: str | None,
        supplier_store: str | None,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]: ...

    def fetch_rol(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_rol_invoices(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> dict[str, Any]: ...

    def fetch_rol_series(
        self,
        *,
        granularity: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]: ...

    def fetch_rol_by_customer(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
        include_others: bool = True,
    ) -> dict[str, Any]: ...

    def fetch_rol_by_branch(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_ebitda_pct(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_fixed_cost_pct(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...

    def fetch_pmr(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]: ...
