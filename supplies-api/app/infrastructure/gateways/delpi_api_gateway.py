from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.delpi_api")


class DelpiApiGatewayError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class DelpiApiGateway:
    """HTTP client for api-delpi reads — timeout required, no blind write retries."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self.base_url = (base_url or Settings.DELPI_API_URL).rstrip("/") + "/"
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.DELPI_API_TIMEOUT_SECONDS
        )
        self.caller_app = caller_app or Settings.DELPI_API_CALLER_APP

    def get(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request("GET", path, access_token=access_token, params=params)

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        method_upper = method.upper()
        if method_upper in {"POST", "PUT", "PATCH", "DELETE"} and json_body is not None:
            # Explicit writes allowed only as single attempt — never retry here.
            pass

        url = urljoin(self.base_url, path.lstrip("/"))
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": self.caller_app,
        }

        try:
            response = requests.request(
                method_upper,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            logger.warning("delpi_api_timeout path=%s", path)
            raise DelpiApiGatewayError("api-delpi timeout") from exc
        except requests.RequestException as exc:
            logger.exception("delpi_api_request_failed path=%s", path)
            raise DelpiApiGatewayError("api-delpi request failed") from exc

        if response.status_code >= 500:
            raise DelpiApiGatewayError(
                "api-delpi server error",
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            raise DelpiApiGatewayError(
                "api-delpi client error",
                status_code=response.status_code,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise DelpiApiGatewayError("api-delpi invalid JSON") from exc
