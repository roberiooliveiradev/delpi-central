"""IBGE SIDRA — IPP producer price index provider (PROC-0076 R2).

Queries the official SIDRA HTTP API for canonical series registered in
``producer_price_series`` (validated contract: table 6903, classification
842 CNAE 2.0, activity 46641 "24 METALURGIA", variables 10008 número-
índice dez/2018=100 and 1396 M/M-1 %). Values arrive as strings and are
parsed to ``Decimal`` — an index/variation is never converted to money.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from urllib.parse import urlparse

import requests

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("external-data-api.ipp")

Transport = Callable[..., Any]


def _requests_transport(url: str, *, headers: dict, timeout: float) -> Any:
    return requests.get(url, headers=headers, timeout=timeout)


class IbgeIppProvider:
    """Fetches monthly IPP observations for one cataloged SIDRA series."""

    provider_id = "ibge-ipp-sidra"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        allowed_hosts: frozenset[str] | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = (base_url or Settings.IBGE_SIDRA_BASE_URL).rstrip("/")
        self._allowed_hosts = allowed_hosts or Settings.IBGE_ALLOWED_HOSTS
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.IBGE_TIMEOUT_SECONDS
        )
        self._transport = transport or _requests_transport

    def _check_host(self) -> None:
        host = (urlparse(self._base_url).hostname or "").lower()
        if host not in self._allowed_hosts:
            raise InvalidResponseError(
                "ibge sidra host is not on the allowlist"
            )

    def fetch_series(
        self,
        *,
        table_code: str,
        classification_code: str,
        variable_code: str,
        activity_code: str,
        month_from: date,
        month_to: date,
    ) -> list[dict[str, Any]]:
        """Rows: {reference_month, value: Decimal, source_record_key}."""
        self._check_host()
        period = f"{month_from:%Y%m}-{month_to:%Y%m}"
        url = (
            f"{self._base_url}/values/t/{table_code}/n1/all"
            f"/v/{variable_code}/p/{period}"
            f"/c{classification_code}/{activity_code}?formato=json"
        )
        headers = {
            "Accept": "application/json",
            "User-Agent": Settings.EXTERNAL_DATA_USER_AGENT,
        }
        try:
            response = self._transport(
                url, headers=headers, timeout=self._timeout
            )
        except requests.Timeout as exc:
            raise ProviderTimeoutError("ibge sidra request timed out") from exc
        except requests.RequestException as exc:
            logger.warning("ibge_transport_failure")
            raise ProviderUnavailableError("ibge request failed") from exc

        status = getattr(response, "status_code", 0)
        if status == 429:
            retry_after = None
            try:
                retry_after = int(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = None
            raise RateLimitedError(
                "ibge rate limited", retry_after=retry_after or None
            )
        if status in (401, 403):
            raise ProviderUnavailableError("ibge access denied")
        if status >= 500:
            raise ProviderUnavailableError("ibge server error")
        if status != 200:
            raise ProviderUnavailableError(f"ibge unexpected status {status}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise InvalidResponseError("ibge non-JSON response") from exc
        return self._normalize(
            payload,
            variable_code=variable_code,
            activity_code=activity_code,
        )

    def _normalize(
        self,
        payload: Any,
        *,
        variable_code: str,
        activity_code: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            raise InvalidResponseError("ibge payload is not a list")
        rows: list[dict[str, Any]] = []
        for entry in payload:
            if not isinstance(entry, dict) or "V" not in entry:
                continue
            if entry.get("V") == "Valor":
                # The first element is the column dictionary, not a
                # value row — its literal ``V`` is the word "Valor".
                continue
            if str(entry.get("D2C")) != str(variable_code):
                raise InvalidResponseError(
                    "ibge payload variable mismatch"
                )
            if str(entry.get("D4C")) != str(activity_code):
                raise InvalidResponseError(
                    "ibge payload activity mismatch"
                )
            period_raw = str(entry.get("D3C") or "").strip()
            try:
                if len(period_raw) != 6:
                    raise ValueError
                reference_month = date(
                    int(period_raw[:4]), int(period_raw[4:6]), 1
                )
                value = Decimal(str(entry.get("V")).strip())
            except (ValueError, InvalidOperation) as exc:
                raise InvalidResponseError(
                    "ibge row has invalid period or value"
                ) from exc
            if not value.is_finite():
                raise InvalidResponseError("ibge value is not finite")
            rows.append(
                {
                    "reference_month": reference_month,
                    "value": value,
                    "source_record_key": (
                        f"sidra:{variable_code}:{activity_code}:{period_raw}"
                    ),
                }
            )
        rows.sort(key=lambda r: r["reference_month"])
        return rows


def build_ipp_provider(**overrides) -> IbgeIppProvider:
    return IbgeIppProvider(**overrides)
