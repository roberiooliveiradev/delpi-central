"""Cliente S2S → minha-delpi-ai-api (sugestão de rotas operacionais)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from delpi_auth.service_token import apply_internal_service_headers
from tv_app.config import Settings

logger = logging.getLogger(__name__)


class MinhaDelpiAiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._base_url = (
            base_url or Settings.MINHA_DELPI_AI_API_URL or "http://delpi-minha-delpi-ai-api:8000"
        ).rstrip("/")
        self._timeout = float(
            timeout_seconds
            if timeout_seconds is not None
            else Settings.MINHA_DELPI_AI_API_TIMEOUT_SECONDS
        )

    def suggest_operational_routes(
        self,
        *,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        apply_internal_service_headers(headers)
        url = f"{self._base_url}/chat/internal/operational-routes/suggest"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                url,
                headers=headers,
                json={"query": query, "limit": limit},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                return {}
            # Aceita envelope {data:{suggestions}} ou payload flat do use case.
            nested = payload.get("data")
            if isinstance(nested, dict) and "suggestions" in nested:
                return nested
            return payload
