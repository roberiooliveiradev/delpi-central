"""Lookup Protheus SYS_USR via api-delpi — adapter only, no local SQL."""

from __future__ import annotations

import logging
import os
from typing import Any, Mapping

import httpx
from delpi_api_client.envelope import format_error_message, parse_envelope
from delpi_auth.service_token import apply_internal_service_headers

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0


class TotvsLookupUnavailableError(RuntimeError):
    """api-delpi / TOTVS unavailable for SYS_USR lookup."""


class DelpiProtheusUsersGateway:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (
            base_url or os.getenv("DELPI_API_URL", "http://delpi-api-delpi:8000")
        ).rstrip("/")
        self._timeout = timeout or float(
            os.getenv("DELPI_API_TIMEOUT", str(_DEFAULT_TIMEOUT))
        )

    def get_protheus_user_by_email(self, email: str) -> dict[str, Any]:
        return self._get(
            "/supplies/protheus-users/by-email",
            params={"email": email},
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, str | None] | None = None,
    ) -> dict[str, Any]:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        headers: dict[str, str] = {"X-Delpi-Caller-App": "core-api"}
        apply_internal_service_headers(headers)

        try:
            with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
                resp = client.get(path, params=clean_params, headers=headers)
        except httpx.TimeoutException as exc:
            raise TotvsLookupUnavailableError(
                "Timeout ao consultar api-delpi (SYS_USR)."
            ) from exc
        except httpx.HTTPError as exc:
            raise TotvsLookupUnavailableError(
                f"Falha ao conectar na api-delpi ({self._base_url})."
            ) from exc

        body: Any
        try:
            body = resp.json()
        except Exception:
            body = None

        if resp.status_code in {502, 503, 504}:
            raise TotvsLookupUnavailableError(
                format_error_message(body, fallback="TOTVS/api-delpi indisponível.")
            )
        if resp.status_code >= 400:
            raise LookupError(
                format_error_message(body, fallback=resp.text[:500] or "Falha no lookup.")
            )

        data, _meta, _error = parse_envelope(body)
        return data if isinstance(data, dict) else (body if isinstance(body, dict) else {})
