"""Infrastructure: resolve catalog action + execute catalog-fixed ASGI READ calls."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
)
from app.application.external_capabilities.dynamic_information.constants import (
    SEMANTIC_TRANSPORT_READ_POST,
)
from app.domain.ports.davi_catalog_action_executor_port import (
    CatalogActionExecutionResult,
)

logger = logging.getLogger(__name__)


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
        semantic_post = (
            action.method == "POST"
            and action.semantic_transport == SEMANTIC_TRANSPORT_READ_POST
            and action.request_body is not None
            and bool(action.request_body.get("supported", True))
        )
        if action.method != "GET" and not semantic_post:
            return CatalogActionExecutionResult(
                outcome="error",
                error_message="Only governed READ actions are executable (GET or explicit SEMANTIC_READ_POST)",
            )

        try:
            path, query = _fill_path(action.path, dict(validated_arguments or {}))
        except ValueError as exc:
            return CatalogActionExecutionResult(
                outcome="error",
                error_message=str(exc),
            )

        headers = {"Authorization": self._authorization}
        try:
            if semantic_post:
                # Trusted catalog body binding: approved body fields go to the JSON
                # body; any remaining declared parameters stay on the query string.
                body_fields = action.body_fields
                json_body = {
                    key: value
                    for key, value in query.items()
                    if key in body_fields
                }
                query = {
                    key: value
                    for key, value in query.items()
                    if key not in body_fields
                }
                response = self._client.post(
                    path, json=json_body, params=query or None, headers=headers
                )
            else:
                response = self._client.get(path, params=query, headers=headers)
        except Exception as exc:
            logger.exception(
                "davi_catalog_asgi_invoke_failed action_id=%s stage=asgi_%s "
                "exception_class=%s",
                action_id,
                "post" if semantic_post else "get",
                type(exc).__name__,
            )
            return CatalogActionExecutionResult(
                outcome="error",
                error_message=f"Catalog ASGI invoke failed: {type(exc).__name__}",
            )

        return self._map_response(action_id, action.path, response)

    @staticmethod
    def _map_response(
        action_id: str, path_template: str, response: Any
    ) -> CatalogActionExecutionResult:
        status = int(getattr(response, "status_code", 500))
        try:
            body = response.json()
        except Exception:
            body = getattr(response, "text", None)

        if status >= 400:
            logger.warning(
                "davi_catalog_upstream_status action_id=%s stage=upstream "
                "status=%s path_template=%s",
                action_id,
                status,
                path_template,
            )

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
