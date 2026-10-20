"""api-delpi gateway authenticated with an individual S2S credential.

Same transport contract as ``DelpiApiGateway`` (timeout, request-id
propagation, error mapping, no write retries) but the service credential is
a Keycloak client-credentials JWT sent in
``X-Delpi-Service-Authorization``. The shared internal token is never added:
when the S2S provider is unavailable or unconfigured the call fails closed
instead of degrading to the legacy credential.
"""

from __future__ import annotations

import logging
import threading

from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
)
from delpi_auth.service_errors import ServiceAuthError
from delpi_auth.service_token_provider import ClientCredentialsTokenProvider

from app.infrastructure.gateways.delpi_api_gateway import (
    DelpiApiGateway,
    DelpiApiGatewayError,
)

logger = logging.getLogger("supplies-api.delpi_s2s")

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


class DelpiS2SApiGateway(DelpiApiGateway):
    def __init__(
        self,
        *,
        token_provider=None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            caller_app=caller_app,
        )
        self._token_provider = token_provider

    def _service_token(self) -> str:
        provider = self._token_provider or get_s2s_token_provider()
        try:
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
