"""Cliente HTTP oficial para chamadas downstream em nome do usuário.

Delegação humana (F2a.R1 — contrato aprovado):
- `Authorization: Bearer <JWT do usuário>` — o owner downstream resolve o
  principal delegado para auditoria/ator delegado.
- `X-Delpi-Caller-App: engineering-api` — identificação de consumidor,
  nunca autorização.
- `X-Request-Id` propagado para correlação ponta a ponta.

Credencial de serviço (G4.A.R1 — contrato S2S individual):
- `service_token` (opt-in por chamada, apenas para superfícies protegidas
  por S2S na api-delpi) viaja em `X-Delpi-Service-Authorization` — o
  header canônico do contrato interserviços. A credencial técnica
  (client-credentials Keycloak) autoriza a OPERAÇÃO técnica; o Bearer
  humano permanece separado, como ator delegado para auditoria — nunca é
  substituído, nunca se mistura com a identidade de serviço.

NUNCA injetar `X-Delpi-Service-Token`/`apply_internal_service_headers`
(token legado compartilhado) em chamadas downstream: o middleware
compartilhado o aceitaria como principal de serviço privilegiado
(`principal_type="service"`, `is_superadmin=True`) — bypass de
autorização por recurso (F2a.R1, gate de segurança). Sem fallback
privilegiado: se a credencial falhar, a seção fica indisponível/forbidden.

Sem retries e com timeout explícito — falhas de fonte viram estados
honestos de seção, nunca dados silenciosos.
"""

from __future__ import annotations

from typing import Any, Mapping

import httpx

from delpi_api_client.envelope import format_error_message, parse_envelope
from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
)

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

    def _headers(
        self,
        access_token: str,
        request_id: str | None,
        service_token: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Delpi-Caller-App": _CALLER_APP,
        }
        if service_token:
            headers[SERVICE_AUTHORIZATION_HEADER] = build_service_authorization(
                service_token
            )
        if request_id:
            headers["X-Request-Id"] = request_id
        return headers

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        access_token: str,
        request_id: str | None = None,
        service_token: str | None = None,
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
                    headers=self._headers(access_token, request_id, service_token),
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

    async def get_raw(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        access_token: str,
        request_id: str | None = None,
        service_token: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        """GET binário (ex.: PDF de desenho) — sem parse de envelope JSON.

        Retorna (status_code, headers, content). Erros HTTP seguem a
        mesma classificação de ``get``: 401/403/404/etc → DownstreamError
        ``http`` com status_code, transporte → transport_error/timeout.
        """
        headers = self._headers(access_token, request_id, service_token)
        headers["Accept"] = "*/*"
        clean_params = {
            key: value for key, value in (params or {}).items() if value is not None
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                resp = await client.get(path, params=clean_params, headers=headers)
        except httpx.TimeoutException as exc:
            raise DownstreamError("timeout", str(exc)) from exc
        except httpx.RequestError as exc:
            raise DownstreamError("transport_error", str(exc)) from exc

        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = None
            raise DownstreamError(
                "http",
                format_error_message(body, fallback=resp.text[:200]),
                status_code=resp.status_code,
            )
        return resp.status_code, dict(resp.headers), resp.content

    async def post(
        self,
        path: str,
        *,
        json_body: Mapping[str, Any],
        access_token: str,
        request_id: str | None = None,
        service_token: str | None = None,
    ) -> Any:
        """POST e parse do envelope `{"success", "data"}` — retorna `data`.

        Mesma delegação do GET: Bearer humano preservado + caller_app de
        telemetria; `service_token` opt-in vai no header S2S canônico,
        nunca no legado compartilhado (F2a.R1/G4.A.R1).
        """
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                resp = await client.post(
                    path,
                    json=dict(json_body),
                    headers=self._headers(access_token, request_id, service_token),
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
