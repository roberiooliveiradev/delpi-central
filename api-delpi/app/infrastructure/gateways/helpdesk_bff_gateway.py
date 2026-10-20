"""Cliente HTTP da api-delpi para a helpdesk-api (BFF do GLPI).

A helpdesk-api é a dona da integração com o GLPI (sessão OAuth do usuário,
paginação, projeção e validação). Este gateway apenas encaminha o Bearer
do usuário autenticado — sem conta de serviço, sem impersonação.
"""
from __future__ import annotations

import time
from typing import Any, Callable

import httpx

from app.config import settings

_MAX_ATTEMPTS = 3
_TRANSIENT_STATUS = {408, 429, 502, 503, 504}


class HelpdeskBffGatewayError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class HelpdeskBffGateway:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._base_url = (base_url or settings.HELPDESK_API_BASE_URL).rstrip("/")
        self._timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else settings.HELPDESK_API_TIMEOUT_SECONDS
        )
        self._sleep = sleep

    def list_tickets(
        self,
        *,
        authorization: str,
        page: int,
        page_size: int,
        assignee_id: int | None = None,
        category_id: int | None = None,
        urgency_id: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {
            "page": str(page),
            "page_size": str(page_size),
        }
        if assignee_id is not None:
            params["assignee_id"] = str(assignee_id)
        if category_id is not None:
            params["category_id"] = str(category_id)
        if urgency_id is not None:
            params["urgency_id"] = str(urgency_id)
        response = self._get("/tickets", authorization=authorization, params=params)
        payload = _json_payload(response)
        if response.status_code >= 400 or payload.get("success") is False:
            raise HelpdeskBffGatewayError(
                _safe_message(payload, "Não foi possível consultar os chamados do Helpdesk."),
                _mapped_status(response.status_code),
            )
        # Contrato do BFF (helpdesk-api): página crua {items, page, page_size,
        # has_more} — sem o envelope {success,data,meta} da api-delpi.
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise HelpdeskBffGatewayError(
                "A consulta de chamados retornou um formato inválido.",
                502,
            )
        return data

    def _get(
        self,
        path: str,
        *,
        authorization: str,
        params: dict[str, str],
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": authorization, "Accept": "application/json"}
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                if self._client is not None:
                    response = self._client.get(url, headers=headers, params=params)
                else:
                    with httpx.Client(timeout=self._timeout_seconds) as client:
                        response = client.get(url, headers=headers, params=params)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS:
                    self._sleep(0.2 * attempt)
                    continue
                raise HelpdeskBffGatewayError(
                    "Tempo limite excedido ao consultar o Helpdesk.", 504
                ) from exc
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS:
                    self._sleep(0.2 * attempt)
                    continue
                raise HelpdeskBffGatewayError(
                    "Helpdesk indisponível no momento.", 503
                ) from exc
            if response.status_code in _TRANSIENT_STATUS and attempt < _MAX_ATTEMPTS:
                self._sleep(0.2 * attempt)
                continue
            return response
        raise HelpdeskBffGatewayError("Helpdesk indisponível no momento.", 503) from last_exc


def _json_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_message(payload: dict[str, Any], fallback: str) -> str:
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    error = payload.get("error")
    # helpdesk-api retorna {"error": "<code>"} — código como string.
    if isinstance(error, str) and error.strip():
        return f"{fallback} ({error.strip()})"
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, str) and code.strip():
            return f"{fallback} ({code.strip()})"
    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return fallback


def _mapped_status(status_code: int) -> int:
    if status_code in (400, 401, 403, 404, 422):
        return status_code
    if status_code in _TRANSIENT_STATUS:
        return status_code
    return 502


def build_helpdesk_bff_gateway() -> HelpdeskBffGateway:
    return HelpdeskBffGateway()
