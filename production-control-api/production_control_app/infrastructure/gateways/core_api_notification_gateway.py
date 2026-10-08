"""Gateway S2S → notificações da Core API (C6).

Contrato: POST {CORE_API_BASE_URL}/integrations/notifications com
X-Delpi-Service-Token: <CORE_API_INTEGRATIONS_SERVICE_TOKEN> — a mesma
credencial configurada no container da Core API.

Mapeamento: 401/403 → NotificationGatewayUnauthorized (config quebrada,
log de erro); rede/timeout/5xx → NotificationGatewayUnavailable (warning);
demais 4xx → NotificationGatewayContractError. Token nunca vai para log.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from production_control_app.config import settings
from production_control_app.domain.errors import (
    NotificationGatewayContractError,
    NotificationGatewayUnauthorized,
    NotificationGatewayUnavailable,
)

logger = logging.getLogger(__name__)

_ENDPOINT = "/integrations/notifications"


class CoreApiNotificationGateway:
    """Implementa NotificationGatewayPort sobre HTTP S2S."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        service_token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.CORE_API_BASE_URL or "").rstrip("/")
        self._timeout = (
            timeout if timeout is not None else float(settings.CORE_API_TIMEOUT)
        )
        self._service_token = (
            service_token
            if service_token is not None
            else (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "")
        ).strip()
        self._client = client or httpx.Client(timeout=self._timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._base_url or not self._service_token:
            raise NotificationGatewayUnavailable(
                "Integração de notificações não configurada."
            )
        try:
            response = self._client.post(
                self._base_url + _ENDPOINT,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Delpi-Service-Token": self._service_token,
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "notification_dispatch_failed category=%s error=%s",
                payload.get("category"),
                type(exc).__name__,
            )
            raise NotificationGatewayUnavailable(
                "Serviço de notificações indisponível."
            ) from exc

        status = response.status_code
        if status in (401, 403):
            logger.error(
                "notification_dispatch_unauthorized category=%s status=%s",
                payload.get("category"),
                status,
            )
            raise NotificationGatewayUnauthorized(
                "Credencial S2S de notificações recusada.",
                status_code=status,
            )
        if status >= 500:
            logger.warning(
                "notification_dispatch_failed category=%s status=%s",
                payload.get("category"),
                status,
            )
            raise NotificationGatewayUnavailable(
                "Serviço de notificações indisponível.",
                status_code=status,
            )
        if status >= 400:
            logger.warning(
                "notification_dispatch_rejected category=%s status=%s",
                payload.get("category"),
                status,
            )
            raise NotificationGatewayContractError(
                "Dispatch de notificação rejeitado pela Core API.",
                status_code=status,
            )
        try:
            body: Any = response.json()
        except ValueError as exc:
            raise NotificationGatewayContractError(
                "Resposta de notificações não é JSON válido."
            ) from exc
        if not isinstance(body, dict):
            raise NotificationGatewayContractError(
                "Resposta de notificações fora do contrato."
            )
        return body
