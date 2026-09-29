"""Shared MCP tool-error wire assembly (S5).

Owns ONLY the duplicated, SDK-facing mechanics of turning an application
error into a tool result:

- ``CallToolResult`` construction for the canonical mcp 2.x model
  (``structured_content``/``meta`` kwargs, ``isError``/``structuredContent``
  wire aliases);
- JSON-safe serialization of the public envelope;
- the shared HTTP-status → error-kind vocabulary;
- redaction of secret-shaped detail keys.

It does NOT own domain error semantics: exception → code/message/kind
mapping remains in each app's bridge, which knows its typed exceptions.
There is no shared domain error hierarchy.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

__all__ = [
    "INTERNAL_ERROR_MESSAGE",
    "json_payload_text",
    "kind_for_http_status",
    "mcp_tool_result",
    "redact_error_details",
]

INTERNAL_ERROR_MESSAGE = "Falha interna na tool."

_SECRET_KEY = re.compile(
    r"(token|secret|password|passwd|credential|authorization|bearer|api[-_]?key)",
    re.IGNORECASE,
)

def json_payload_text(payload: Any) -> str:
    """JSON-safe serialization for tool-result text content."""
    return json.dumps(payload, ensure_ascii=False, default=str)


def kind_for_http_status(status: int, *, server_error: str = "upstream") -> str:
    """Shared HTTP-status → error-kind vocabulary.

    ``server_error`` parameterizes the >= 500 bucket because apps carry
    different wire vocabulary there (``upstream`` vs ``validation``).
    """
    if status == 401:
        return "unauthenticated"
    if status == 403:
        return "forbidden"
    if status == 404:
        return "not_found"
    if status == 409:
        return "conflict"
    if status >= 500:
        return server_error
    return "validation"


def mcp_tool_result(
    payload: Mapping[str, Any] | None = None,
    *,
    is_error: bool,
    text: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> CallToolResult:
    """Build a CallToolResult on the canonical mcp 2.x model.

    ``payload`` becomes the structured content; the text content defaults to
    its JSON serialization (apps that need a fixed message pass ``text``).
    ``meta`` is attached as the wire ``_meta`` object.
    """
    from mcp.types import CallToolResult, TextContent

    body = text if text is not None else json_payload_text(payload or {})
    kwargs: dict[str, Any] = {
        "content": [TextContent(type="text", text=body)],
        "is_error": is_error,
    }
    if payload is not None:
        kwargs["structured_content"] = dict(payload)
    if meta is not None:
        kwargs["meta"] = dict(meta)
    return CallToolResult(**kwargs)


def redact_error_details(details: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Drop secret-shaped keys and non-JSON-safe values from error details.

    Returns ``None`` when nothing survives — never fabricates an empty
    details block (ERROR_IS_NOT_EMPTY_DATA).
    """
    if not details:
        return None
    safe: dict[str, Any] = {}
    for key, value in details.items():
        if _SECRET_KEY.search(str(key)):
            continue
        try:
            json.dumps(value, default=str)
        except (TypeError, ValueError):
            continue
        safe[str(key)] = value
    return safe or None
