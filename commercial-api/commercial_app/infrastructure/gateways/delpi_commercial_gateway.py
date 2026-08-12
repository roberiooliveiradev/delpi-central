from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from commercial_app.config import settings
from commercial_app.infrastructure.http.auth_header import bearer_authorization_from_context


class DelpiCommercialGateway:
    """Proxy HTTP para rotas TOTVS/enrichment na api-delpi."""

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
        return headers

    def search_active_customers(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request(
            "GET",
            "/pedidos-venda-abertos/customers/search",
            params=params,
        )

    def enrich_portfolio_customers(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/pedidos-venda-abertos/customers/enrichment",
            json_body=payload,
        )

    def list_customer_open_order_metrics(
        self,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/pedidos-venda-abertos/customers/open-order-metrics",
            json_body=payload or {},
        )

    def list_open_orders(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        # TOTVS puro (sem membership PVA) — escopo fica no BFF commercial.
        return self._request(
            "GET",
            "/pedidos-venda-abertos/totvs-open-orders",
            params=params,
        )

    def list_ops_abertas(self) -> dict[str, Any]:
        return self._request("GET", "/pedidos-venda-abertos/ops-abertas")

    def list_customer_billing_series(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/pedidos-venda-abertos/customers/billing-series",
            json_body=payload,
        )

    def list_customer_outbound_invoices(
        self,
        *,
        customer_code: str,
        customer_store: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # TOTVS puro (sem membership PVA) — escopo fica no BFF commercial.
        code = quote(str(customer_code or "").strip(), safe="")
        store = quote(str(customer_store or "").strip(), safe="")
        return self._request(
            "GET",
            f"/pedidos-venda-abertos/totvs-outbound-invoices/{code}/{store}",
            params=params,
        )

    def get_commercial_analytics(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Proxy GET `/commercial/...` na api-delpi (KPIs / OTD / OV)."""
        normalized = path if path.startswith("/") else f"/{path}"
        return self._request("GET", f"/commercial{normalized}", params=params)

    def get_dashboard_department_idd(
        self,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Proxy GET `/dashboard/department-idd` (SI via api-delpi)."""
        return self._request("GET", "/dashboard/department-idd", params=params)

    def get_commercial_proposal_document(
        self,
        path: str = "",
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Proxy GET `/commercial-proposals` (+ path) na api-delpi."""
        suffix = path if not path or path.startswith("/") else f"/{path}"
        return self._request("GET", f"/commercial-proposals{suffix}", params=params)

    def get_commercial_proposal_document_pdf(
        self,
        proposta_interna: str,
    ) -> tuple[bytes, str | None]:
        code = quote(str(proposta_interna or "").strip(), safe="")
        return self._request_bytes("GET", f"/commercial-proposals/{code}/pdf")

    def post_commercial_proposal_document_pdf(
        self,
        proposta_interna: str,
        *,
        payload: dict[str, Any],
    ) -> tuple[bytes, str | None]:
        code = quote(str(proposta_interna or "").strip(), safe="")
        return self._request_bytes(
            "POST",
            f"/commercial-proposals/{code}/pdf",
            json_body=payload,
        )

    def get_production(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = path if path.startswith("/") else f"/{path}"
        return self._request("GET", f"/production{normalized}", params=params)

    def get_product(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = path if path.startswith("/") else f"/{path}"
        return self._request("GET", f"/products{normalized}", params=params)

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[bytes, str | None]:
        url = f"{self._base_url}{path}"
        clean_params = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        headers = self._headers()
        if json_body is not None:
            headers = {**headers, "Content-Type": "application/json"}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(
                method,
                url,
                params=clean_params or None,
                json=json_body,
                headers=headers,
            )
        if response.status_code >= 400:
            message = "Erro ao consultar api-delpi."
            try:
                body = response.json()
                message = body.get("message") or body.get("detail") or message
            except Exception:
                pass
            raise RuntimeError(message)
        filename = None
        disposition = response.headers.get("content-disposition") or ""
        if "filename=" in disposition:
            filename = disposition.split("filename=", 1)[1].strip().strip('"')
        return response.content, filename

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
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(
                method,
                url,
                params=clean_params or None,
                json=json_body,
                headers=self._headers(),
            )
        if response.status_code >= 400:
            message = "Erro ao consultar api-delpi."
            try:
                body = response.json()
                message = body.get("message") or body.get("detail") or message
            except Exception:
                pass
            raise RuntimeError(message)
        try:
            return response.json()
        except Exception as exc:
            raise RuntimeError("Resposta inválida da api-delpi.") from exc
