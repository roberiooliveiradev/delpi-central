"""BrasilAPI CNPJ v1 provider for external-data-api (X0 §6 freeze).

- Community third-party provider: ``provider_id=brasilapi-cnpj-v1``,
  ``source_type=THIRD_PARTY_API`` — never claimed as a government source.
- No retries, no bulk queries, no scraping: upstream 5xx/403/transport
  maps to fail-closed ``ProviderUnavailableError``, HTTP 429 is honoured
  via ``Retry-After`` instead of being retried.
- The raw payload is never persisted nor logged; the normalizer only
  reads allowlisted fields.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import requests

from app.application.contracts import (
    InvalidResponseError,
    InvalidTaxIdError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    TaxIdNotFoundError,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.normalization.brasilapi_cnpj_normalizer import (
    normalize_brasilapi_cnpj,
)

logger = logging.getLogger("external-data-api.brasilapi")

DEFAULT_BASE_URL = "https://brasilapi.com.br/api"

Transport = Callable[..., Any]


def _requests_transport(url: str, *, timeout: float) -> Any:
    return requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=timeout,
    )


class BrasilApiCnpjProvider:
    """``CnpjDataSource`` adapter for the public BrasilAPI CNPJ v1 endpoint."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._base_url = (
            base_url or getattr(Settings, "BRASILAPI_BASE_URL", "")
        ).rstrip("/") or DEFAULT_BASE_URL
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(getattr(Settings, "BRASILAPI_TIMEOUT_SECONDS", 6) or 6)
        )
        self._transport = transport or _requests_transport
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, tax_id: str, *, correlation_id: str) -> Mapping:
        url = f"{self._base_url}/cnpj/v1/{tax_id}"
        try:
            response = self._transport(url, timeout=self._timeout)
        except Exception as exc:
            if _is_timeout(exc):
                logger.warning("brasilapi_fetch_failed kind=timeout")
                raise ProviderTimeoutError(
                    "external provider timed out"
                ) from exc
            logger.warning("brasilapi_fetch_failed kind=transport")
            raise ProviderUnavailableError(
                "external provider unreachable"
            ) from exc

        return self._normalize_response(response, tax_id, correlation_id)

    # --- internals ---------------------------------------------------------

    def _normalize_response(
        self, response: Any, tax_id: str, correlation_id: str
    ) -> Mapping:
        status = getattr(response, "status_code", None)
        if status == 200:
            pass
        elif status == 400:
            raise InvalidTaxIdError("provider rejected the CNPJ")
        elif status == 404:
            raise TaxIdNotFoundError("CNPJ not found by provider")
        elif status == 403:
            raise ProviderUnavailableError("provider denied the request")
        elif status == 429:
            raise RateLimitedError(
                "provider rate limit reached",
                retry_after=_retry_after(response),
            )
        elif isinstance(status, int) and status >= 500:
            raise ProviderUnavailableError("external provider unavailable")
        else:
            raise InvalidResponseError(
                f"unexpected provider status {status}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise InvalidResponseError(
                "provider returned non-JSON payload"
            ) from exc

        retrieved_at = self._clock().isoformat()
        record = normalize_brasilapi_cnpj(
            payload,
            tax_id=tax_id,
            retrieved_at=retrieved_at,
            correlation_id=correlation_id,
        )
        return record.to_dict()


class UnavailableCnpjProvider:
    """Fail-closed provider — default until explicit activation."""

    def __init__(self, reason: str = "external CNPJ provider disabled") -> None:
        self._reason = reason

    def fetch(self, tax_id: str, *, correlation_id: str) -> Mapping:
        raise ProviderUnavailableError(self._reason)


def build_cnpj_provider() -> Any:
    """Resolve the configured CNPJ provider — unknown values fail closed."""
    provider = getattr(
        Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable"
    )
    if provider == "brasilapi":
        return BrasilApiCnpjProvider()
    if provider == "unavailable":
        return UnavailableCnpjProvider()
    return UnavailableCnpjProvider(
        f"unknown external CNPJ provider: {provider}"
    )


def _is_timeout(exc: Exception) -> bool:
    return isinstance(exc, (requests.Timeout,)) or "timed out" in str(exc).lower()


def _retry_after(response: Any) -> int | None:
    headers = getattr(response, "headers", None) or {}
    raw = None
    if isinstance(headers, Mapping):
        raw = headers.get("Retry-After") or headers.get("retry-after")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None
