"""api-delpi gateway authenticated with the individual S2S credential.

Pattern mirrors supplies-api ``DelpiS2SApiGateway`` (commit 633390da):

- ``Authorization`` carries the delegated end-user Bearer;
- ``X-Delpi-Service-Authorization`` carries this BFF's own Keycloak
  client-credentials JWT (never the supplies credential, never the shared
  internal token);
- ``X-Delpi-Caller-App`` is observability metadata only;
- token/config failure fails closed — no fallback credential exists.
"""

from __future__ import annotations

import logging
import threading
from typing import Any
from urllib.parse import urljoin

import requests

from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
)
from delpi_auth.service_errors import ServiceAuthError
from delpi_auth.service_token_provider import ClientCredentialsTokenProvider

from controllership_finance_app.config import settings

logger = logging.getLogger("controllership-finance-api.delpi_s2s")


class DelpiApiGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


_provider_lock = threading.Lock()
_shared_provider: ClientCredentialsTokenProvider | None = None


def get_s2s_token_provider() -> ClientCredentialsTokenProvider:
    """Process-wide provider so the token cache survives per-request gateways."""
    global _shared_provider
    if _shared_provider is None:
        with _provider_lock:
            if _shared_provider is None:
                _shared_provider = ClientCredentialsTokenProvider.from_env()
    return _shared_provider


def reset_s2s_token_provider() -> None:
    """Test hook — drop the cached provider so env changes take effect."""
    global _shared_provider
    with _provider_lock:
        _shared_provider = None


class ApiDelpiSettlementsGateway:
    """Read-only client for the api-delpi financial settlements routes."""

    def __init__(
        self,
        *,
        token_provider=None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or settings.DELPI_API_URL
        ).rstrip("/") + "/"
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.DELPI_API_TIMEOUT_SECONDS
        )
        self.caller_app = caller_app or settings.DELPI_API_CALLER_APP
        self._token_provider = token_provider

    def _service_token(self) -> str:
        try:
            provider = self._token_provider or get_s2s_token_provider()
            return provider.get_token()
        except ServiceAuthError as exc:
            logger.warning("delpi_s2s_token_unavailable code=%s", exc.code)
            raise DelpiApiGatewayError(
                "api-delpi s2s authentication unavailable"
            ) from exc

    def _build_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": self.caller_app,
            SERVICE_AUTHORIZATION_HEADER: build_service_authorization(
                self._service_token()
            ),
        }

    def get(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))
        try:
            response = requests.get(
                url,
                headers=self._build_headers(access_token),
                params=params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            logger.warning("delpi_api_timeout path=%s", path)
            raise DelpiApiGatewayError("api-delpi timeout") from exc
        except requests.RequestException as exc:
            logger.exception("delpi_api_request_failed path=%s", path)
            raise DelpiApiGatewayError("api-delpi request failed") from exc

        error_code = _extract_error_code(response)
        if response.status_code >= 500:
            raise DelpiApiGatewayError(
                "api-delpi server error",
                status_code=response.status_code,
                error_code=error_code,
            )
        if response.status_code >= 400:
            raise DelpiApiGatewayError(
                "api-delpi client error",
                status_code=response.status_code,
                error_code=error_code,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise DelpiApiGatewayError("api-delpi invalid JSON") from exc


def _extract_error_code(response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return error["code"]
    return None
