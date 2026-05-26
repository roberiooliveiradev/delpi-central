from __future__ import annotations

import os
from typing import Any, Mapping, MutableMapping
from urllib.parse import urlencode

import httpx

from delpi_auth.service_token import apply_internal_service_headers


class TransformometroApiError(RuntimeError):
    pass


class TransformometroApiClient:
    """Cliente HTTP para integrações server-to-server com transformometro-api."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        raw = (
            base_url
            or os.getenv("TRANSFORMOMETRO_API_BASE_URL")
            or "http://transformometro-api:8000"
        )
        self._base_url = raw.rstrip("/")
        self._timeout = timeout_seconds

    def list_engineering_processes(
        self,
        *,
        params: Mapping[str, str | None] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/transformometro/integrations/engineering/transforma-mais/processes",
            params=params,
            authorization=authorization,
        )

    def get_engineering_summary(
        self,
        *,
        params: Mapping[str, str | None] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        return self._get(
            "/transformometro/integrations/engineering/transforma-mais/processes/summary",
            params=params,
            authorization=authorization,
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, str | None] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        query = ""
        if params:
            filtered = {k: v for k, v in params.items() if v is not None and v != ""}
            if filtered:
                query = f"?{urlencode(filtered)}"

        headers: MutableMapping[str, str] = {}
        if authorization:
            headers["Authorization"] = authorization

        apply_internal_service_headers(headers)

        url = f"{self._base_url}{path}{query}"
        try:
            response = httpx.get(url, headers=headers, timeout=self._timeout)
        except httpx.RequestError as exc:
            raise TransformometroApiError(f"Falha ao conectar em transformometro-api: {exc}") from exc

        if response.status_code >= 400:
            raise TransformometroApiError(
                f"transformometro-api HTTP {response.status_code}: {response.text[:500]}"
            )

        body = response.json()
        if not body.get("success"):
            raise TransformometroApiError(body.get("message") or "Resposta sem success=true")

        data = body.get("data")
        if not isinstance(data, dict):
            raise TransformometroApiError("Envelope inválido: data ausente")
        return data
