"""Gateway autenticado para o requests-api — Bearer do usuário humano.

A criação e a leitura de solicitações acontecem **como o usuário** (nunca
como serviço): identidade, filial e permissões de criação seguem sendo
autoridade do requests-api. Tokens nunca são logados.
"""

from __future__ import annotations

import logging
from time import monotonic
from typing import Any
from urllib.parse import quote

import httpx

from delpi_mes_app.domain.errors import (
    MesSourceConflict,
    MesSourceInvalidResponse,
    MesSourceNotFound,
    MesSourceUnavailable,
    MesSourceValidationError,
)

logger = logging.getLogger(__name__)


class RequestsApiGateway:
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

    def create_request_as_user(
        self,
        *,
        access_token: str,
        type_code: str,
        payload: dict[str, Any],
        branch: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        headers = self._headers(access_token)
        headers["Idempotency-Key"] = idempotency_key
        body: dict[str, Any] = {"type_code": type_code, "payload": payload}
        if branch:
            body["branch"] = branch
        return self._call(
            "POST", "/v1/requests", headers=headers, json=body
        )

    def get_request_as_user(
        self, *, access_token: str, request_id: str
    ) -> dict[str, Any]:
        encoded = quote(str(request_id), safe="")
        return self._call(
            "GET", f"/v1/requests/{encoded}", headers=self._headers(access_token)
        )

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": "delpi-mes-api",
        }

    def _call(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = monotonic()
        try:
            response = self._client.request(
                method, f"{self._base_url}{path}", headers=headers, json=json
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning(
                "requests_api_error kind=%s elapsed_ms=%s",
                type(exc).__name__,
                int((monotonic() - started) * 1000),
            )
            raise MesSourceUnavailable(
                "Serviço de solicitações temporariamente indisponível."
            ) from exc

        if response.status_code == 404:
            raise MesSourceNotFound("Solicitação não encontrada.")
        if response.status_code == 409:
            raise MesSourceConflict(
                self._safe_message(response, "Operação em conflito na solicitação.")
            )
        if response.status_code == 422:
            raise MesSourceValidationError(
                self._safe_message(response, "Dados da solicitação inválidos.")
            )
        if response.status_code in {401, 403}:
            raise PermissionError(
                self._safe_message(
                    response, "Sem permissão para operar a solicitação."
                )
            )
        if response.status_code >= 500:
            logger.warning(
                "requests_api_error status=%s elapsed_ms=%s",
                response.status_code,
                int((monotonic() - started) * 1000),
            )
            raise MesSourceUnavailable(
                "Serviço de solicitações temporariamente indisponível."
            )
        if response.status_code >= 400:
            raise MesSourceInvalidResponse(
                "Resposta inesperada do serviço de solicitações."
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise MesSourceInvalidResponse(
                "Resposta inválida do serviço de solicitações."
            ) from exc
        if not isinstance(body, dict) or body.get("success") is not True:
            raise MesSourceInvalidResponse(
                "Contrato inválido do serviço de solicitações."
            )
        return body.get("data") if isinstance(body.get("data"), dict) else {}

    @staticmethod
    def _safe_message(response: httpx.Response, fallback: str) -> str:
        try:
            body = response.json()
        except ValueError:
            return fallback
        message = body.get("message") if isinstance(body, dict) else None
        return str(message).strip() if message else fallback
