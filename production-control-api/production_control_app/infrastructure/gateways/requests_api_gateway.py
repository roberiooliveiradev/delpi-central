"""Gateway S2S → Requests API (P2 — Problemas de Processo).

Contrato: POST {REQUESTS_API_URL}/integrations/requests com
X-Delpi-Service-Token (API_DELPI_INTERNAL_SERVICE_TOKEN compartilhado),
X-Delpi-Caller-App: production-control-api e a MESMA Idempotency-Key
recebida do cockpit — a chave atravessa ponta a ponta.

Mapeamento: 401/403 → RequestsGatewayUnauthorized (config quebrada, log de
erro); rede/timeout/5xx → RequestsGatewayUnavailable; demais 4xx →
RequestsGatewayRejected propagando a mensagem PT do upstream (segura para o
operador). Token nunca vai para log.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from delpi_auth.service_token import apply_internal_service_headers
from production_control_app.config import settings
from production_control_app.domain.errors import (
    RequestsGatewayRejected,
    RequestsGatewayUnauthorized,
    RequestsGatewayUnavailable,
)

logger = logging.getLogger(__name__)

_ENDPOINT = "/integrations/requests"
_CALLER_APP = "production-control-api"


def _upstream_message(response: httpx.Response) -> str | None:
    """Extrai a mensagem PT do envelope ``fail`` do Requests API."""
    try:
        body: Any = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        message = str(body.get("message") or "").strip()
        return message or None
    return None


class RequestsApiGateway:
    """Implementa RequestsGatewayPort sobre HTTP S2S com httpx."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.REQUESTS_API_URL or "").rstrip("/")
        self._timeout = (
            timeout if timeout is not None else float(settings.REQUESTS_API_TIMEOUT)
        )
        self._client = client or httpx.Client(timeout=self._timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create_request(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        if not self._base_url:
            raise RequestsGatewayUnavailable(
                "Integração com Minhas Solicitações não configurada."
            )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Delpi-Caller-App": _CALLER_APP,
            "Idempotency-Key": str(idempotency_key).strip(),
        }
        apply_internal_service_headers(headers)
        try:
            response = self._client.post(
                self._base_url + _ENDPOINT,
                json=body,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "requests_gateway_failed type_code=%s error=%s",
                body.get("typeCode"),
                type(exc).__name__,
            )
            raise RequestsGatewayUnavailable(
                "Serviço de solicitações indisponível."
            ) from exc

        status = response.status_code
        if status in (401, 403):
            logger.error(
                "requests_gateway_unauthorized type_code=%s status=%s",
                body.get("typeCode"),
                status,
            )
            raise RequestsGatewayUnauthorized(
                "Credencial S2S de solicitações recusada.",
                status_code=status,
            )
        if status >= 500:
            logger.warning(
                "requests_gateway_failed type_code=%s status=%s",
                body.get("typeCode"),
                status,
            )
            raise RequestsGatewayUnavailable(
                "Serviço de solicitações indisponível.",
                status_code=status,
            )
        if status >= 400:
            message = _upstream_message(response)
            logger.warning(
                "requests_gateway_rejected type_code=%s status=%s",
                body.get("typeCode"),
                status,
            )
            raise RequestsGatewayRejected(
                message or "Solicitação recusada pelo Minhas Solicitações.",
                status_code=status,
            )
        try:
            data: Any = response.json()
        except ValueError as exc:
            raise RequestsGatewayUnavailable(
                "Resposta do serviço de solicitações não é JSON válido."
            ) from exc
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            return data["data"]
        if isinstance(data, dict):
            return data
        raise RequestsGatewayUnavailable(
            "Resposta do serviço de solicitações fora do contrato."
        )
