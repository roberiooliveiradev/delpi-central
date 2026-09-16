"""Infrastructure adapter: ASGI/HTTP client for catalog-fixed GET only."""

from __future__ import annotations

from typing import Any

from app.domain.ports.davi_catalog_fixed_get_port import (
    CatalogFixedGetRequest,
    CatalogFixedGetResult,
)


class AsgiCatalogFixedGetAdapter:
    """Executes a pre-validated GET against a fixed path via injected ASGI client.

    Does not accept host/URL overrides. Composition injects the concrete client.
    """

    def __init__(self, client: Any):
        self._client = client

    def execute(
        self,
        request: CatalogFixedGetRequest,
        *,
        authorization: str,
    ) -> CatalogFixedGetResult:
        if request.method != "GET":
            return CatalogFixedGetResult(
                outcome="error",
                error_message="Only GET is supported",
            )
        headers = {"Authorization": authorization}
        response = self._client.get(
            request.path,
            params=request.query,
            headers=headers,
        )
        status = int(getattr(response, "status_code", 500))
        try:
            body = response.json()
        except Exception:
            body = getattr(response, "text", None)

        if status == 401:
            return CatalogFixedGetResult(outcome="unauthorized", payload=body)
        if status == 403:
            return CatalogFixedGetResult(outcome="forbidden", payload=body)
        if status >= 400:
            return CatalogFixedGetResult(
                outcome="error",
                payload=body,
                error_message=f"Upstream error status={status}",
            )
        return CatalogFixedGetResult(outcome="ok", payload=body)
