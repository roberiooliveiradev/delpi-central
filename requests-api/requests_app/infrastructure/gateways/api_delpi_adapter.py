from __future__ import annotations

from typing import Any

import httpx

from delpi_auth.service_token import apply_internal_service_headers
from requests_app.config import settings
from requests_app.domain.entities import Request
from requests_app.domain.ports.operational_lookup_port import OperationalLookupPort
from requests_app.domain.ports.request_destination_port import (
    DeliveryResult,
    RequestDestinationPort,
)


class ApiDelpiAdapter(RequestDestinationPort, OperationalLookupPort):
    """Destination + TOTVS lookups via api-delpi invoice-issuance routes."""

    adapter_name = "api_delpi"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.DELPI_API_URL).rstrip("/")
        self._timeout = timeout or float(settings.DELPI_API_TIMEOUT or 30)
        self._caller_app = (caller_app or settings.DELPI_API_CALLER_APP or "requests-api").strip()

    def _headers(self, authorization: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", "X-Delpi-Caller-App": self._caller_app}
        apply_internal_service_headers(headers)
        if authorization:
            headers["Authorization"] = authorization
        return headers

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.get(path, params=clean, headers=self._headers(authorization))
        response.raise_for_status()
        body = response.json()
        if isinstance(body, dict) and "data" in body:
            data = body.get("data")
            return data if isinstance(data, dict) else {"value": data}
        return body if isinstance(body, dict) else {"value": body}

    def health(self) -> DeliveryResult:
        try:
            with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
                response = client.get("/health", headers=self._headers())
            if response.status_code >= 400:
                return DeliveryResult(
                    ok=False,
                    detail=f"api-delpi health HTTP {response.status_code}",
                    meta={"status_code": response.status_code},
                )
            return DeliveryResult(
                ok=True,
                detail="api-delpi reachable",
                meta={"status_code": response.status_code},
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(ok=False, detail=str(exc))

    def deliver(
        self,
        *,
        request: Request,
        event_type: str,
        payload: dict[str, Any],
    ) -> DeliveryResult:
        return DeliveryResult(
            ok=True,
            detail="api_delpi deliver acknowledged (side-effects via outbox/notifications)",
            meta={
                "request_id": str(request.id),
                "event_type": event_type,
                "payload_keys": sorted(payload.keys()),
            },
        )

    def search_parties(
        self,
        *,
        party_type: str,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/invoice-issuance/parties",
            params={"party_type": party_type, "query": query, "limit": limit},
            authorization=authorization,
        )

    def search_products(
        self,
        *,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/invoice-issuance/products",
            params={"query": query, "limit": limit},
            authorization=authorization,
        )

    def search_carriers(
        self,
        *,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/invoice-issuance/carriers",
            params={"query": query, "limit": limit},
            authorization=authorization,
        )

    def list_open_sales_orders(
        self,
        *,
        branch: str,
        party_code: str,
        party_store: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/invoice-issuance/open-sales-orders",
            params={
                "branch": branch,
                "party_code": party_code,
                "party_store": party_store,
            },
            authorization=authorization,
        )

    def get_warehouse_01_balance(
        self,
        *,
        product_code: str,
        branch: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        code = str(product_code or "").strip()
        return self._get(
            f"/invoice-issuance/products/{code}/warehouse-01-balance",
            params={"branch": branch},
            authorization=authorization,
        )


class InMemoryOperationalLookupAdapter(OperationalLookupPort):
    """Test double with canned shapes matching api-delpi envelopes."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def search_parties(self, *, party_type: str, query: str, limit: int = 20, authorization: str | None = None) -> dict[str, Any]:
        self.calls.append(("parties", {"party_type": party_type, "query": query, "limit": limit}))
        return {
            "items": [
                {
                    "party_type": party_type,
                    "party_code": "C001",
                    "party_store": "01",
                    "party_name": f"Match {query}",
                    "tax_id": "12345678000199",
                    "blocked": False,
                }
            ]
        }

    def search_products(self, *, query: str, limit: int = 20, authorization: str | None = None) -> dict[str, Any]:
        self.calls.append(("products", {"query": query, "limit": limit}))
        return {
            "items": [
                {
                    "product_code": "P001",
                    "code": "P001",
                    "description": f"Produto {query}",
                    "unit": "UN",
                    "blocked": False,
                }
            ]
        }

    def search_carriers(self, *, query: str, limit: int = 20, authorization: str | None = None) -> dict[str, Any]:
        self.calls.append(("carriers", {"query": query, "limit": limit}))
        return {
            "items": [
                {
                    "carrier_code": "T01",
                    "carrier_name": f"Transportadora {query}",
                    "blocked": False,
                }
            ]
        }

    def list_open_sales_orders(
        self,
        *,
        branch: str,
        party_code: str,
        party_store: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            ("open_sales_orders", {"branch": branch, "party_code": party_code, "party_store": party_store})
        )
        return {
            "party_code": party_code,
            "party_store": party_store,
            "orders": [],
            "orders_count": 0,
            "lines_count": 0,
        }

    def get_warehouse_01_balance(
        self,
        *,
        product_code: str,
        branch: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(("warehouse_01_balance", {"product_code": product_code, "branch": branch}))
        return {
            "product_code": product_code,
            "branch_code": branch,
            "warehouse": "01",
            "balance": 10.0,
        }
