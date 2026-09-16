"""Infrastructure: resolve catalog action + execute catalog-fixed ASGI GET."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)


def _fill_path(path_template: str, arguments: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    remaining = dict(arguments)
    parts: list[str] = []
    for segment in path_template.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            if name not in remaining:
                raise ValueError(f"Missing path parameter: {name}")
            value = remaining.pop(name)
            parts.append(quote(str(value), safe=""))
        else:
            parts.append(segment)
    return "/".join(parts), remaining


class AsgiCatalogActionExecutor:
    """Catalog-fixed GET executor. Owns HTTP + Authorization for one request binding.

    Does not accept host/URL/method overrides from callers. Composition injects
    the ASGI client and the end-user Authorization for the current request only.
    """

    def __init__(self, client: Any, *, authorization: str):
        self._client = client
        self._authorization = authorization

    def execute(
        self,
        *,
        action_id: str,
        validated_arguments: dict[str, Any],
    ) -> CatalogActionExecutionResult:
        action = get_action_by_id(action_id)
        if action is None:
            return CatalogActionExecutionResult(
                outcome="error",
                error_message="Unknown action_id",
            )
        if not action.executable:
            return CatalogActionExecutionResult(
                outcome="forbidden",
                error_message="Action is not DAVI-eligible",
            )
        if action.method != "GET":
            return CatalogActionExecutionResult(
                outcome="error",
                error_message="Only GET actions are executable in V1",
            )

        try:
            path, query = _fill_path(action.path, dict(validated_arguments or {}))
        except ValueError as exc:
            return CatalogActionExecutionResult(
                outcome="error",
                error_message=str(exc),
            )

        headers = {"Authorization": self._authorization}
        response = self._client.get(path, params=query, headers=headers)
        status = int(getattr(response, "status_code", 500))
        try:
            body = response.json()
        except Exception:
            body = getattr(response, "text", None)

        if status == 401:
            return CatalogActionExecutionResult(outcome="unauthorized", payload=body)
        if status == 403:
            return CatalogActionExecutionResult(outcome="forbidden", payload=body)
        if status >= 400:
            return CatalogActionExecutionResult(
                outcome="error",
                payload=body,
                error_message=f"Upstream error status={status}",
            )
        return CatalogActionExecutionResult(outcome="ok", payload=body)
