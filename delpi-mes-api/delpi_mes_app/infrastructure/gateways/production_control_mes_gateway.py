from __future__ import annotations

import logging
from datetime import datetime
from time import monotonic
from typing import Any
from urllib.parse import quote

import httpx
from delpi_auth.service_token import apply_internal_service_headers

from delpi_mes_app.domain.errors import (
    MesSourceConflict,
    MesSourceInvalidResponse,
    MesSourceNotFound,
    MesSourceUnauthorized,
    MesSourceUnavailable,
    MesSourceValidationError,
)

logger = logging.getLogger(__name__)


class ProductionControlMesGateway:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(timeout, connect=min(timeout, 2.0))
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get_monitoring(self, *, branch: str) -> dict[str, Any]:
        return self._get("/integrations/mes/work-centers/live", params={"branch": branch})

    def get_timeline(self, run_id: str) -> dict[str, Any]:
        encoded = quote(str(run_id), safe="")
        return self._get(f"/integrations/mes/runs/{encoded}/timeline")

    def get_run_performance(self, run_id: str) -> dict[str, Any]:
        encoded = quote(str(run_id), safe="")
        return self._get(f"/integrations/mes/runs/{encoded}/performance")

    def get_work_center_timeline(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime | None,
    ) -> dict[str, Any]:
        encoded = quote(str(work_center), safe="")
        params: dict[str, Any] = {"branch": branch, "from": period_from.isoformat()}
        if period_to:
            params["to"] = period_to.isoformat()
        return self._get(
            f"/integrations/mes/work-centers/{encoded}/timeline", params=params
        )

    def get_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"branch": branch, "page": page, "pageSize": page_size}
        if work_center:
            params["workCenter"] = work_center
        if period_from:
            params["from"] = period_from.isoformat()
        if period_to:
            params["to"] = period_to.isoformat()
        return self._get("/integrations/mes/downtimes", params=params)

    def list_downtime_reasons(self) -> dict[str, Any]:
        return self._request("GET", "/integrations/mes/downtime-reasons")

    def create_downtime_reason(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST", "/integrations/mes/downtime-reasons", json=payload
        )

    def update_downtime_reason(
        self, code: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/integrations/mes/downtime-reasons/{quote(str(code), safe='')}",
            json=payload,
        )

    def set_downtime_reason_active(self, code: str, *, active: bool) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/integrations/mes/downtime-reasons/{quote(str(code), safe='')}/active",
            json={"active": bool(active)},
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "X-Delpi-Caller-App": "delpi-mes-api"}
        apply_internal_service_headers(headers)
        return headers

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = monotonic()
        try:
            response = self._client.request(
                method,
                f"{self._base_url}{path}",
                headers=self._headers(),
                params=params,
                json=json,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            self._log_error(type(exc).__name__, None, started)
            raise MesSourceUnavailable("Fonte de dados MES temporariamente indisponível.") from exc

        if response.status_code in {401, 403}:
            self._log_error("upstream_authorization", response.status_code, started)
            raise MesSourceUnauthorized("Integração MES não autorizada no serviço de origem.")
        if response.status_code == 404:
            raise MesSourceNotFound(
                self._safe_message(response, "Recurso MES não encontrado.")
            )
        if response.status_code == 409:
            raise MesSourceConflict(
                self._safe_message(response, "Operação em conflito no catálogo MES.")
            )
        if response.status_code == 422:
            raise MesSourceValidationError(self._safe_message(response, "Consulta MES inválida."))
        if response.status_code >= 500:
            self._log_error("upstream_unavailable", response.status_code, started)
            raise MesSourceUnavailable("Fonte de dados MES temporariamente indisponível.")
        if response.status_code >= 400:
            raise MesSourceInvalidResponse("Resposta inesperada da fonte de dados MES.")

        try:
            body = response.json()
        except ValueError as exc:
            raise MesSourceInvalidResponse("Resposta inválida da fonte de dados MES.") from exc
        if not isinstance(body, dict) or body.get("success") is not True or not isinstance(
            body.get("data"), dict
        ):
            raise MesSourceInvalidResponse("Contrato inválido da fonte de dados MES.")
        return body["data"]

    @staticmethod
    def _safe_message(response: httpx.Response, fallback: str) -> str:
        try:
            body = response.json()
        except ValueError:
            return fallback
        message = body.get("message") if isinstance(body, dict) else None
        return str(message)[:240] if message else fallback

    @staticmethod
    def _log_error(error_class: str, status: int | None, started: float) -> None:
        logger.warning(
            "delpi_mes_upstream_error error_class=%s upstream_status=%s elapsed_ms=%s",
            error_class,
            status,
            int((monotonic() - started) * 1000),
        )
