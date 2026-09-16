"""Governed HTTP execution against catalog-fixed API DELPI paths (no arbitrary URL)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)


class GovernedExecutionError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _fill_path(path_template: str, arguments: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    remaining = dict(arguments)
    parts: list[str] = []
    for segment in path_template.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            if name not in remaining:
                raise GovernedExecutionError(f"Missing path parameter: {name}", status_code=422)
            value = remaining.pop(name)
            parts.append(quote(str(value), safe=""))
        else:
            parts.append(segment)
    return "/".join(parts), remaining


def build_internal_request(
    action: TechnicalAction,
    arguments: dict[str, Any] | None,
) -> tuple[str, str, dict[str, Any]]:
    """Return method, path, query — never accepts host/url overrides."""
    if action.method != "GET":
        raise GovernedExecutionError("Only GET actions are executable in V1", status_code=405)
    args = dict(arguments or {})
    # Reject smuggling of transport controls
    for forbidden in ("url", "host", "path", "method", "operationId", "sql"):
        if forbidden in args:
            raise GovernedExecutionError(
                f"Argument '{forbidden}' is not allowed",
                status_code=400,
            )
    path, query = _fill_path(action.path, args)
    # Only primitive query values
    clean_query: dict[str, Any] = {}
    for key, value in query.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            raise GovernedExecutionError(
                f"Argument '{key}' must be a scalar",
                status_code=422,
            )
        clean_query[key] = value
    return action.method, path, clean_query


def execute_catalog_get(
    *,
    action: TechnicalAction,
    arguments: dict[str, Any] | None,
    authorization: str | None,
    client: Any,
) -> tuple[int, Any]:
    """Execute GET against catalog-fixed path via an injected HTTP/ASGI client.

    Application never constructs FastAPI/TestClient. Composition/Interface injects
    ``client`` with ``get(path, params=, headers=)``.
    """
    method, path, query = build_internal_request(action, arguments)
    if method != "GET":
        raise GovernedExecutionError("Only GET supported", status_code=405)
    if client is None:
        raise GovernedExecutionError("HTTP client is required", status_code=500)

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    response = client.get(path, params=query, headers=headers)
    status = getattr(response, "status_code", 500)
    try:
        body = response.json()
    except Exception:
        body = getattr(response, "text", None)
    return int(status), body
