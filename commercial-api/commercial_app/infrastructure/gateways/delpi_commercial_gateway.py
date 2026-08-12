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
        # Barra final: FastAPI redirect; service-to-service evita Mixed Content no browser.
        return self._request("GET", "/pedidos-venda-abertos/", params=params)

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
        code = quote(str(customer_code or "").strip(), safe="")
        store = quote(str(customer_store or "").strip(), safe="")
        return self._request(
            "GET",
            f"/pedidos-venda-abertos/clientes/{code}/{store}/notas-fiscais",
            params=params,
        )

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
