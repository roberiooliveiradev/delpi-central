from __future__ import annotations

from typing import Any

import httpx

from production_control_app.config import settings
from production_control_app.domain.errors import DelpiGatewayError

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


class DelpiProductionGateway:
    """Proxy HTTP para rotas TOTVS de produção na api-delpi."""

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

    def fetch_pcp_orders_summary(self, *, branch: str) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/pcp-orders/summary",
            params={"branch": branch, "open_only": True},
        )

    def fetch_pcp_orders_items(
        self,
        *,
        branch: str,
        delayed_only: bool,
        page_size: int,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/pcp-orders/items",
            params={
                "branch": branch,
                "delayed_only": delayed_only,
                "open_only": True,
                "page": 1,
                "page_size": page_size,
                "sort": "delay_desc",
            },
        )

    def fetch_production_otd(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        page_size: int,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/otd",
            params={
                "branch": branch,
                "start_date": start_date,
                "end_date": end_date,
                "page": 1,
                "page_size": page_size,
            },
        )

    def fetch_production_otd_series(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        granularity: str,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/otd/series",
            params={
                "branch": branch,
                "start_date": start_date,
                "end_date": end_date,
                "granularity": granularity,
            },
        )

    def fetch_machine_load_work_centers(
        self,
        *,
        branch: str,
        scheduled_start: str,
        scheduled_end: str,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/machine-load/work-centers",
            params={
                "branch": branch,
                "scheduled_start": scheduled_start,
                "scheduled_end": scheduled_end,
                "open_only": True,
            },
        )

    def fetch_machine_load_operations(
        self,
        *,
        branch: str,
        scheduled_start: str,
        scheduled_end: str,
        work_center: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/production/machine-load/operations",
            params={
                "branch": branch,
                "scheduled_start": scheduled_start,
                "scheduled_end": scheduled_end,
                "work_center": work_center,
                "open_only": True,
                "page": page,
                "page_size": page_size,
                "sort": "schedule_asc",
            },
        )

    def fetch_machine_load_appointment_status(
        self,
        *,
        branch: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/production/machine-load/appointment-status",
            json_body={"branch": branch, "items": items},
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
            raise DelpiGatewayError(str(message))
        try:
            payload = response.json()
        except Exception as exc:
            raise DelpiGatewayError("Resposta inválida da api-delpi.") from exc
        if not isinstance(payload, dict):
            raise DelpiGatewayError("Resposta inválida da api-delpi.")
        return payload
