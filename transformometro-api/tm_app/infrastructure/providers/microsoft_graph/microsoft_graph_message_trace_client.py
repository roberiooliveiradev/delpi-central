"""Cliente Microsoft Graph — Message Trace (Exchange admin)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

import httpx

from tm_app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    sanitize_graph_error,
)

logger = logging.getLogger(__name__)

GRAPH_MESSAGE_TRACES_URL = (
    "https://graph.microsoft.com/v1.0/admin/exchange/tracing/messageTraces"
)
GRAPH_TRACE_DETAILS_URL = (
    "https://graph.microsoft.com/v1.0/admin/exchange/tracing/messageTraces"
    "/{trace_id}/getDetailsByRecipient"
)


class HttpGetClientProtocol(Protocol):
    def get(self, url: str, **kwargs: Any) -> httpx.Response: ...


def _format_graph_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _escape_odata_string(value: str) -> str:
    return str(value or "").replace("'", "''")


class MicrosoftGraphMessageTraceClient:
    """Consulta messageTraces e detalhes por destinatário (ExchangeMessageTrace.Read.All)."""

    def __init__(
        self,
        *,
        get_access_token: Callable[[], str],
        timeout_seconds: float = 30.0,
        http_client: HttpGetClientProtocol | None = None,
    ) -> None:
        self._get_access_token = get_access_token
        self._timeout = timeout_seconds
        self._http_client = http_client

    def list_message_traces(
        self,
        *,
        start: datetime,
        end: datetime,
        recipient: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "startDate": _format_graph_datetime(start),
            "endDate": _format_graph_datetime(end),
        }
        if recipient:
            safe = _escape_odata_string(recipient.strip())
            params["$filter"] = f"recipientAddress eq '{safe}'"

        payload = self._get_json(GRAPH_MESSAGE_TRACES_URL, params=params)
        rows = payload.get("value")
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]

    def get_details_by_recipient(self, trace_id: str) -> list[dict[str, Any]]:
        trace_key = str(trace_id or "").strip()
        if not trace_key:
            return []
        url = GRAPH_TRACE_DETAILS_URL.format(trace_id=trace_key)
        payload = self._get_json(url)
        rows = payload.get("value")
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        token = self._get_access_token()
        try:
            response = self._get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
        except httpx.TimeoutException as exc:
            raise GraphMailError("Timeout ao consultar Message Trace Microsoft Graph.") from exc
        except httpx.HTTPError as exc:
            raise GraphMailError(
                "Falha de conexão ao consultar Message Trace Microsoft Graph."
            ) from exc

        if response.status_code != 200:
            raise GraphMailError(
                sanitize_graph_error(
                    f"Message Trace Microsoft Graph rejeitado (HTTP {response.status_code})."
                )
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise GraphMailError(
                "Resposta inválida ao consultar Message Trace Microsoft Graph."
            ) from exc
        if not isinstance(payload, dict):
            raise GraphMailError(
                "Resposta inválida ao consultar Message Trace Microsoft Graph."
            )
        return payload

    def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        if self._http_client is not None:
            return self._http_client.get(url, **kwargs)
        with httpx.Client(timeout=self._timeout) as client:
            return client.get(url, **kwargs)
