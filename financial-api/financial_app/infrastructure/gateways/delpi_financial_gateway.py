from __future__ import annotations

from typing import Any

import httpx

from financial_app.config import settings
from financial_app.domain.errors import DelpiGatewayError, InvalidPeriod

from delpi_auth.request_context import get_current_user, get_request_authorization
from delpi_auth.service_token import apply_internal_service_headers, internal_service_authorization


def _normalize_bearer(raw: str) -> str:
    value = raw.strip()
    return value if value.startswith("Bearer ") else f"Bearer {value}"


def bearer_authorization_from_context() -> str | None:
    header_auth = get_request_authorization()
    if header_auth:
        return header_auth

    user = get_current_user()
    if user is not None:
        token = getattr(user, "access_token", None)
        if token:
            return _normalize_bearer(token)

    internal = internal_service_authorization()
    if internal:
        return internal

    return None


class DelpiFinancialGateway:
    """Proxy HTTP para as rotas financeiras TOTVS da api-delpi."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.DELPI_API_URL).rstrip("/")
        self._timeout = float(timeout or settings.DELPI_API_TIMEOUT)
        self._caller_app = caller_app or settings.DELPI_API_CALLER_APP

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-Delpi-Caller-App": self._caller_app,
        }
        authorization = bearer_authorization_from_context()
        if authorization:
            headers["Authorization"] = authorization
        apply_internal_service_headers(headers)
        return headers

    # ------------------------------------------------------------------
    # Inadimplência — /financeiro/inadimplencia/*
    # ------------------------------------------------------------------

    def fetch_delinquency_summary(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/inadimplencia/resumo",
            params={"start_date": start_date, "end_date": end_date},
        )

    def fetch_delinquency_monthly(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        customer_code: str | None = None,
        store_code: str | None = None,
        new_business_only: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/inadimplencia/mensal",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "customer_code": customer_code,
                "store_code": store_code,
                "novos_negocios": new_business_only or None,
            },
        )

    def fetch_delinquency_aging(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/inadimplencia/faixas-atraso",
            params={"start_date": start_date, "end_date": end_date},
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/inadimplencia/clientes",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "q": search,
                "only_with_delays": "true" if only_with_delays else "false",
            },
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/inadimplencia/titulos",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "customer_code": customer_code,
                "store_code": store_code,
                "status": status,
                "delay_range": delay_range,
                "q": search,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
            },
        )

    # ------------------------------------------------------------------
    # Despesas por centro de custo — /financeiro/despesas-centro-custo/*
    # ------------------------------------------------------------------

    def fetch_cost_center_filters(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/filtros",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "cost_center": cost_center,
                "exclude_mp_products": exclude_mp_products,
            },
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/resumo",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "cost_center": cost_center,
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "exclude_mp_products": exclude_mp_products,
            },
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/serie",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "cost_center": cost_center,
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "exclude_mp_products": exclude_mp_products,
            },
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/ranking-centros",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "limit": limit,
                "exclude_mp_products": exclude_mp_products,
            },
        )

    def fetch_cost_center_ranking_suppliers(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        cost_center: str | None,
        limit: int,
        exclude_mp_products: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/ranking-fornecedores",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "cost_center": cost_center,
                "limit": limit,
                "exclude_mp_products": exclude_mp_products,
            },
        )

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
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financeiro/despesas-centro-custo/lancamentos",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "branch": branch,
                "cost_center": cost_center,
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "search": search,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "exclude_mp_products": exclude_mp_products,
            },
        )

    # ------------------------------------------------------------------
    # KPIs financeiros — /financial/*
    # ------------------------------------------------------------------

    def fetch_rol(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request("GET", "/financial/rol", params=self._kpi_params(branch, start_date, end_date))

    def fetch_rol_invoices(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financial/rol/invoices",
            params={**self._kpi_params(branch, start_date, end_date), "limit": limit},
        )

    def fetch_rol_series(
        self,
        *,
        granularity: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/commercial/rol/series",
            params={
                "granularity": granularity,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def fetch_rol_by_customer(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
        include_others: bool = True,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/commercial/rol/by-customer",
            params={
                "branch": branch,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "include_others": include_others,
            },
        )

    def fetch_rol_by_branch(
        self, *, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/commercial/rol/by-branch",
            params={"start_date": start_date, "end_date": end_date},
        )

    def fetch_ebitda_pct(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request(
            "GET", "/financial/ebitda_pct", params=self._kpi_params(branch, start_date, end_date)
        )

    def fetch_fixed_cost_pct(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/financial/fixed_cost_pct",
            params=self._kpi_params(branch, start_date, end_date),
        )

    def fetch_pmr(
        self, *, branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return self._request("GET", "/financial/pmr", params=self._kpi_params(branch, start_date, end_date))

    @staticmethod
    def _kpi_params(
        branch: str | None, start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        return {"branch": branch, "start_date": start_date, "end_date": end_date}

    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        clean_params = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(
                    method,
                    url,
                    params=clean_params or None,
                    json=json_body,
                    headers=self._headers(),
                )
        except httpx.RequestError as exc:
            raise DelpiGatewayError("Erro ao consultar api-delpi.") from exc
        if response.status_code >= 400:
            message = "Erro ao consultar api-delpi."
            try:
                body = response.json()
                message = body.get("message") or body.get("detail") or message
            except Exception:
                pass
            if response.status_code == 400 and "período" in str(message).lower():
                raise InvalidPeriod(str(message)) from None
            raise DelpiGatewayError(str(message))
        try:
            payload = response.json()
        except Exception as exc:
            raise DelpiGatewayError("Resposta inválida da api-delpi.") from exc
        if not isinstance(payload, dict):
            raise DelpiGatewayError("Resposta inválida da api-delpi.")
        return payload
