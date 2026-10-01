"""Bounded MCP streamable-HTTP transport — C3-MCP-INTEROP-01.

DELPI profile: all three approved specialist servers run streamable HTTP
with ``json_response=True`` and ``stateless_http=True`` (shared
``delpi_mcp`` transport), so the wire surface required here is a bounded
JSON-RPC request/response per call over the existing ``requests``
dependency. SSE response frames are still parsed defensively.

Responsibilities: initialize handshake, tools/list, tools/call, timeout,
response-size bound, JSON-RPC/protocol error normalization, session-id
echo. No business rules, no specialist names, no authorization semantics.

The bearer token is only used for the Authorization header — never
logged, embedded in errors, or returned.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Callable, Mapping
from typing import Any

import requests

from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    MCP_INVALID_RESPONSE,
    MCP_PROTOCOL_ERROR,
    MCP_RESULT_TOO_LARGE,
    MCP_TIMEOUT,
    MCP_UNAVAILABLE,
    SpecialistInteropError,
)


# DELPI shared MCP minimum protocol version (shared/delpi_mcp/protocol.py).
MCP_PROTOCOL_VERSION = "2026-07-28"
MAX_MCP_RESPONSE_BYTES = 1024 * 1024

_ACCEPT = "application/json, text/event-stream"
_JSON_TYPES = ("application/json",)
_SSE_TYPE = "text/event-stream"


class DelpiMcpTransport:
    """One bounded MCP endpoint conversation for the DELPI server profile."""

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float,
        bearer_token: str | None = None,
        http_post: Callable[..., Any] = requests.post,
        max_response_bytes: int = MAX_MCP_RESPONSE_BYTES,
        client_name: str = "delia-api",
        client_version: str = "0.0.1",
    ) -> None:
        if not str(endpoint or "").strip():
            raise ValueError("mcp endpoint is required")
        if timeout_seconds <= 0:
            raise ValueError("mcp timeout_seconds must be > 0")
        self._endpoint = endpoint
        self._timeout_seconds = float(timeout_seconds)
        self._bearer_token = bearer_token
        self._http_post = http_post
        self._max_response_bytes = max_response_bytes
        self._client_name = client_name
        self._client_version = client_version
        self._session_id: str | None = None
        self._ids = itertools.count(1)

    def initialize(self) -> None:
        """MCP initialize handshake; captures the session id if issued."""
        result = self._rpc(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": self._client_name,
                    "version": self._client_version,
                },
            },
        )
        if not isinstance(result.get("serverInfo"), Mapping):
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "initialize result missing serverInfo"
            )
        self._notify("notifications/initialized", {})

    def list_tools(self) -> tuple[Mapping[str, Any], ...]:
        result = self._rpc("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "tools/list result missing tools"
            )
        return tuple(
            tool for tool in tools if isinstance(tool, Mapping)
        )

    def call_tool(
        self, name: str, arguments: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        result = self._rpc(
            "tools/call", {"name": name, "arguments": dict(arguments)}
        )
        if not isinstance(result, Mapping):
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "tools/call result is not an object"
            )
        return result

    def _notify(self, method: str, params: Mapping[str, Any]) -> None:
        response = self._send(
            {"jsonrpc": "2.0", "method": method, "params": dict(params)}
        )
        if response is not None and response.status_code >= 400:
            self._raise_for_status(response.status_code)

    def _rpc(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        request_id = next(self._ids)
        response = self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": dict(params),
            }
        )
        assert response is not None  # requests always return for RPC calls
        self._raise_for_status(response.status_code)
        self._capture_session(response)
        body = self._parse_body(response)
        if not isinstance(body, Mapping) or "result" not in body:
            if isinstance(body, Mapping) and isinstance(
                body.get("error"), Mapping
            ):
                raise SpecialistInteropError(
                    MCP_PROTOCOL_ERROR,
                    f"mcp protocol error (code {body['error'].get('code')})",
                )
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "mcp response is not a JSON-RPC result"
            )
        if body["id"] != request_id:
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "mcp response id mismatch"
            )
        result = body["result"]
        if not isinstance(result, Mapping):
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "mcp result is not an object"
            )
        return result

    def _send(self, payload: Mapping[str, Any]):
        headers = {
            "Accept": _ACCEPT,
            "Content-Type": "application/json",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        }
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        try:
            return self._http_post(
                self._endpoint,
                headers=headers,
                data=json.dumps(payload),
                timeout=self._timeout_seconds,
            )
        except requests.exceptions.Timeout as exc:
            raise SpecialistInteropError(
                MCP_TIMEOUT, "mcp request timed out"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise SpecialistInteropError(
                MCP_UNAVAILABLE, "mcp endpoint unreachable"
            ) from exc

    def _capture_session(self, response: Any) -> None:
        session_id = response.headers.get("mcp-session-id")
        if isinstance(session_id, str) and session_id.strip():
            self._session_id = session_id.strip()

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 401:
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED,
                "mcp endpoint rejected authentication",
            )
        if status_code == 403:
            raise SpecialistInteropError(
                MCP_AUTHORIZATION_DENIED,
                "mcp endpoint denied authorization",
            )
        if status_code == 429 or status_code >= 500:
            raise SpecialistInteropError(
                MCP_UNAVAILABLE, f"mcp endpoint unavailable (HTTP {status_code})"
            )
        raise SpecialistInteropError(
            MCP_PROTOCOL_ERROR,
            f"mcp endpoint rejected request (HTTP {status_code})",
        )

    def _parse_body(self, response: Any) -> Any:
        content = response.content or b""
        if len(content) > self._max_response_bytes:
            raise SpecialistInteropError(
                MCP_RESULT_TOO_LARGE, "mcp response exceeds size bound"
            )
        content_type = (response.headers.get("Content-Type") or "").split(";")[
            0
        ].strip().lower()
        if content_type in _JSON_TYPES or not content_type:
            try:
                return json.loads(content)
            except ValueError as exc:
                raise SpecialistInteropError(
                    MCP_INVALID_RESPONSE, "mcp response is not valid JSON"
                ) from exc
        if content_type == _SSE_TYPE:
            return self._parse_sse(content)
        raise SpecialistInteropError(
            MCP_INVALID_RESPONSE,
            f"unsupported mcp content-type '{content_type}'",
        )

    @staticmethod
    def _parse_sse(content: bytes) -> Any:
        """Extract the first JSON-RPC object from SSE data frames."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SpecialistInteropError(
                MCP_INVALID_RESPONSE, "mcp SSE response is not UTF-8"
            ) from exc
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            try:
                parsed = json.loads(data)
            except ValueError:
                continue
            if isinstance(parsed, Mapping) and (
                "result" in parsed or "error" in parsed
            ):
                return parsed
        raise SpecialistInteropError(
            MCP_INVALID_RESPONSE, "mcp SSE response has no JSON-RPC payload"
        )
