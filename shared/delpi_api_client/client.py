"""HTTP client for api-delpi, consumed by strategic-indicators-api."""

from __future__ import annotations

import os
from typing import Any, Mapping

import httpx
from shared_http import apply_internal_service_headers

_DEFAULT_TIMEOUT = 30.0


class DelpiApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class DelpiApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (
            base_url or os.getenv("DELPI_API_URL", "http://delpi-api-delpi:8000")
        ).rstrip("/")
        self._timeout = timeout or float(os.getenv("DELPI_API_TIMEOUT", str(_DEFAULT_TIMEOUT)))

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, str | None] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        headers: dict[str, str] = {}
        apply_internal_service_headers(headers)
        if authorization:
            headers["Authorization"] = authorization

        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            resp = client.get(path, params=clean_params, headers=headers)

        if resp.status_code >= 400:
            raise DelpiApiError(resp.status_code, resp.text[:500])

        body = resp.json()
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body

    # -- Financial --
    def get_rol(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/financial/rol", params=params, authorization=authorization)

    def get_rol_target_pct(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/financial/rol-target-pct", params=params, authorization=authorization)

    # -- Commercial --
    def get_new_business_rol_pct(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/commercial/new-business-rol-pct", params=params, authorization=authorization)

    def get_new_clients_average(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/commercial/new-clients-average", params=params, authorization=authorization)

    def get_new_clients_rol_pct(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/commercial/new-clients-rol-pct", params=params, authorization=authorization)

    def get_sales_conversion_rate(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/commercial/sales-conversion-rate", params=params, authorization=authorization)

    def get_sales_order_otd(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/commercial/sales-order-otd", params=params, authorization=authorization)

    # -- Production --
    def get_overall_equipment_effectiveness(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/production/overall-equipment-effectiveness-pct", params=params, authorization=authorization)

    def get_on_time_delivery(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/production/on-time-delivery-pct", params=params, authorization=authorization)

    # -- Supplies --
    def get_cpv(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/supplies/cpv", params=params, authorization=authorization)

    def get_supplies_otd(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/supplies/otd", params=params, authorization=authorization)

    def get_stock_value(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/supplies/stock-value", params=params, authorization=authorization)

    def get_inventory_turnover(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/supplies/inventory-turnover", params=params, authorization=authorization)

    # -- Quality --
    def get_ppm_summary(self, ppm_type: str, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get(f"/quality/ppm/{ppm_type}/summary", params=params, authorization=authorization)

    def list_ppm(self, ppm_type: str, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get(f"/quality/ppm/{ppm_type}", params=params, authorization=authorization)

    def list_quality_branches(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/quality/branches", params=params, authorization=authorization)

    def list_nonconformities(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/quality/nonconformities", params=params, authorization=authorization)

    # -- Engineering --
    def list_lmps(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/engineering/lmps", params=params, authorization=authorization)

    def get_lmp(self, sale_number: str, *, authorization: str | None = None) -> dict[str, Any]:
        return self._get(f"/engineering/lmps/{sale_number}", authorization=authorization)

    def get_lmp_dashboard(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/engineering/lmps/dashboard", params=params, authorization=authorization)

    def get_lmp_dashboard_summary(self, *, params: Mapping[str, str | None] | None = None, authorization: str | None = None) -> dict[str, Any]:
        return self._get("/engineering/lmps/dashboard/summary", params=params, authorization=authorization)