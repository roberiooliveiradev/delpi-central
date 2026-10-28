"""Cliente HTTP oficial para chamadas downstream em nome do usuário.

Convenções canônicas (mesmas de `delpi_api_client`/supplies):
- `Authorization: Bearer <JWT do usuário>` — delegação oficial; o owner
  downstream revalida identidade e autorização do recurso.
- `X-Delpi-Caller-App: engineering-api`.
- `apply_internal_service_headers` — token interno de serviço quando
  configurado (complementa, nunca substitui, a autorização do usuário).
- `X-Request-Id` propagado para correlação ponta a ponta.

Sem retries e com timeout explícito — falhas de fonte viram estados
honestos de seção, nunca dados silenciosos.
"""

from __future__ import annotations

from typing import Any, Mapping

import httpx

from delpi_api_client.envelope import format_error_message, parse_envelope
from delpi_auth.service_token import apply_internal_service_headers

_CALLER_APP = "engineering-api"


class DownstreamError(Exception):
    """Falha classificada de uma chamada a API oficial."""

    def __init__(
        self,
        kind: str,
        detail: str,
        *,
        status_code: int | None = None,
    ) -> None:
        self.kind = kind  # timeout | transport_error | http | contract_error
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"[{kind}] {detail}")


class DownstreamClient:
    """GET tipado a uma API oficial, com delegação do usuário."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport

    def _headers(self, access_token: str, request_id: str | None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": _CALLER_APP,
        }
        if request_id:
            headers["X-Request-Id"] = request_id
        apply_internal_service_headers(headers)
        return headers

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        access_token: str,
        request_id: str | None = None,
    ) -> Any:
        """GET e parse do envelope `{"success", "data"}` — retorna `data`.

        Raises DownstreamError com kind classificado.
        """
        clean_params = {
            key: value for key, value in (params or {}).items() if value is not None
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                resp = await client.get(
                    path,
                    params=clean_params,
                    headers=self._headers(access_token, request_id),
                )
        except httpx.TimeoutException as exc:
            raise DownstreamError("timeout", str(exc)) from exc
        except httpx.RequestError as exc:
            raise DownstreamError("transport_error", str(exc)) from exc

        try:
            body = resp.json()
        except Exception:
            body = None

        if resp.status_code >= 400:
            raise DownstreamError(
                "http",
                format_error_message(body, fallback=resp.text[:200]),
                status_code=resp.status_code,
            )

        data, _meta, _error = parse_envelope(body)
        if data is None and isinstance(body, dict) and body.get("success") is False:
            raise DownstreamError("contract_error", "Envelope sem payload de dados.")
        return data if data is not None else body
