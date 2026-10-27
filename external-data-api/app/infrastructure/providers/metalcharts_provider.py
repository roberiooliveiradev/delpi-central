"""MetalCharts REST provider (PROC-0076 R5).

Thin, fail-closed adapter over ``https://api.metalcharts.org``:

- Bearer authentication via ``METALCHARTS_API_KEY`` — the key never
  leaves the backend, never reaches logs and is never returned in
  payloads.
- Host is allowlisted (SSRF guard) and HTTPS is mandatory.
- Free-plan weights are exposed per call so the ingestion layer can
  charge the monthly/per-minute allowance ledger BEFORE issuing a
  request: spot ``/v1/prices`` = 1, history ``/v1/history/{symbol}``
  = 2, instruments ``/v1/instruments`` = 1.
- Units are preserved verbatim — COMEX copper (``HG``) is verified as
  USD per pound, not per tonne and not per troy ounce. The adapter
  never converts units itself.

The history response shape is not yet verified against a live key
(S1 homologation is pending), so the normalizer accepts the documented
variants (``data`` as bar list or dict holding ``bars``/``points``/
``candles``) and raises ``InvalidResponseError`` — never guesses —
when a payload deviates.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit

import requests

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.domain.market_data import PROVIDER_METALCHARTS
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("external-data-api.metalcharts")

Transport = Callable[..., Any]

WEIGHT_SPOT = 1
WEIGHT_HISTORY = 2
WEIGHT_INSTRUMENTS = 1

_VALID_INTERVALS = frozenset(
    {"15m", "30m", "45m", "1h", "2h", "4h", "8h", "1d", "1w", "1M"}
)
_BAR_LIST_KEYS = ("bars", "points", "candles")
_BAR_DATE_KEYS = ("date", "time", "timestamp", "t", "datetime")
_BAR_CLOSE_KEYS = ("close", "c")


def _requests_transport(url: str, *, headers: dict, timeout: float) -> Any:
    return requests.get(url, headers=headers, timeout=timeout)


def params_hash(*parts: str) -> str:
    """Stable dedup key for the per-minute allowance ledger."""
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


class MetalChartsProvider:
    """Spot + daily-history client honoring the Free-plan contract."""

    provider_id = PROVIDER_METALCHARTS

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
        allowed_hosts: Iterable[str] | None = None,
    ) -> None:
        self._base_url = (
            base_url or Settings.METALCHARTS_BASE_URL
        ).rstrip("/")
        hosts = frozenset(
            allowed_hosts
            if allowed_hosts is not None
            else Settings.METALCHARTS_ALLOWED_HOSTS
        )
        parsed = urlsplit(self._base_url)
        if parsed.scheme != "https" or parsed.hostname not in hosts:
            raise ProviderUnavailableError(
                "metalcharts base url is not in the allowed hosts"
            )
        self._api_key = (
            api_key if api_key is not None else Settings.METALCHARTS_API_KEY
        )
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.METALCHARTS_TIMEOUT_SECONDS
        )
        self._transport = transport or _requests_transport

    def configured(self) -> bool:
        return bool(self._api_key)

    # --- endpoints -----------------------------------------------------------

    def fetch_spot(self) -> dict[str, dict[str, Any]]:
        """GET /v1/prices — every tracked metal in one call (1 weight).

        Returns ``{symbol: {"price", "bid", "ask", "timestamp",
        "exchange", "market_type", "stale", "currency", "unit"}}`` —
        native fields preserved verbatim, no unit conversion."""
        body = self._get("/v1/prices")
        data = body.get("data")
        if not isinstance(data, dict):
            raise InvalidResponseError("metalcharts prices payload malformed")
        out: dict[str, dict[str, Any]] = {}
        for symbol, entry in data.items():
            if not isinstance(entry, dict):
                continue
            price = self._decimal(entry.get("price"))
            out[symbol] = {
                "price": price,
                "bid": self._decimal(entry.get("bid")),
                "ask": self._decimal(entry.get("ask")),
                "timestamp": entry.get("timestamp"),
                "exchange": entry.get("exchange"),
                "market_type": entry.get("marketType"),
                "stale": bool(entry.get("stale", False)),
                "currency": entry.get("currency"),
                "unit": entry.get("unit"),
            }
        return out

    def fetch_history(
        self,
        symbol: str,
        date_from: date,
        date_to: date,
        *,
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        """GET /v1/history/{symbol} — OHLCV bars (2 weight).

        Free plan exposes 30 days of daily bars; deeper windows depend
        on the plan. Returns ``[{"observation_date", "open", "high",
        "low", "close", "volume"}]`` ascending — unparseable payloads
        are rejected, never coerced."""
        symbol = (symbol or "").strip().upper()
        if not symbol:
            raise InvalidResponseError("metalcharts symbol is required")
        if interval not in _VALID_INTERVALS:
            raise InvalidResponseError(
                f"metalcharts interval not supported: {interval}"
            )
        body = self._get(
            f"/v1/history/{symbol}",
            params={
                "start": date_from.isoformat(),
                "end": date_to.isoformat(),
                "interval": interval,
            },
        )
        bars = self._extract_bars(body, symbol)
        out: list[dict[str, Any]] = []
        for bar in bars:
            if not isinstance(bar, dict):
                continue
            obs_date = self._bar_date(bar)
            close = self._first_decimal(bar, _BAR_CLOSE_KEYS)
            if obs_date is None or close is None:
                # Incomplete bar — skipped, never fabricated.
                continue
            out.append(
                {
                    "observation_date": obs_date,
                    "open": self._first_decimal(bar, ("open", "o")),
                    "high": self._first_decimal(bar, ("high", "h")),
                    "low": self._first_decimal(bar, ("low", "l")),
                    "close": close,
                    "volume": bar.get("volume", bar.get("v")),
                }
            )
        out.sort(key=lambda r: r["observation_date"])
        return out

    def fetch_instruments(self) -> dict[str, Any]:
        """GET /v1/instruments — symbol catalogue (1 weight). Used by
        S1 homologation tooling, not by the request path."""
        body = self._get("/v1/instruments")
        data = body.get("data")
        if data is None or not isinstance(data, (dict, list)):
            raise InvalidResponseError(
                "metalcharts instruments payload malformed"
            )
        return {"data": data}

    # --- internals -----------------------------------------------------------

    def _get(self, path: str, *, params: dict[str, str] | None = None):
        if not self._api_key:
            raise ProviderUnavailableError(
                "metalcharts api key is not configured"
            )
        url = f"{self._base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        try:
            response = self._transport(
                url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Accept": "application/json",
                    "User-Agent": Settings.EXTERNAL_DATA_USER_AGENT,
                },
                timeout=self._timeout,
            )
        except requests.Timeout as exc:
            raise ProviderTimeoutError("metalcharts request timed out") from exc
        except requests.RequestException as exc:
            logger.warning("metalcharts_transport_failure path=%s", path)
            raise ProviderUnavailableError(
                "metalcharts request failed"
            ) from exc

        status = getattr(response, "status_code", 0)
        if status == 429:
            retry_after = None
            try:
                retry_after = int(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = None
            raise RateLimitedError(
                "metalcharts rate limited", retry_after=retry_after or None
            )
        if status in (401, 403):
            logger.warning(
                "metalcharts_access_denied path=%s status=%s", path, status
            )
            raise ProviderUnavailableError(
                "metalcharts key rejected or plan does not authorize endpoint"
            )
        if status >= 500:
            raise ProviderUnavailableError("metalcharts server error")
        if status != 200:
            raise ProviderUnavailableError(
                f"metalcharts unexpected status {status}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise InvalidResponseError(
                "metalcharts non-JSON response"
            ) from exc
        if not isinstance(body, dict) or body.get("success") is not True:
            raise InvalidResponseError(
                "metalcharts envelope not successful"
            )
        return body

    @staticmethod
    def _extract_bars(body: dict[str, Any], symbol: str) -> list[Any]:
        data = body.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in _BAR_LIST_KEYS:
                candidate = data.get(key)
                if isinstance(candidate, list):
                    return candidate
            # Some payloads nest under the requested symbol.
            nested = data.get(symbol)
            if isinstance(nested, dict):
                for key in _BAR_LIST_KEYS:
                    candidate = nested.get(key)
                    if isinstance(candidate, list):
                        return candidate
            if isinstance(nested, list):
                return nested
        raise InvalidResponseError(
            "metalcharts history payload has no bar list"
        )

    @staticmethod
    def _bar_date(bar: dict[str, Any]) -> date | None:
        for key in _BAR_DATE_KEYS:
            raw = bar.get(key)
            if raw is None:
                continue
            text = str(raw).strip()
            try:
                # Accept ISO date or ISO datetime (UTC-suffixed).
                return date.fromisoformat(text[:10])
            except ValueError:
                continue
        return None

    @staticmethod
    def _decimal(raw: Any) -> Decimal | None:
        if raw is None:
            return None
        try:
            value = Decimal(str(raw))
        except InvalidOperation:
            return None
        return value if value > 0 else None

    @classmethod
    def _first_decimal(
        cls, bar: dict[str, Any], keys
    ) -> Decimal | None:
        for key in keys:
            value = cls._decimal(bar.get(key))
            if value is not None:
                return value
        return None


def build_metalcharts_provider(**overrides) -> MetalChartsProvider:
    return MetalChartsProvider(**overrides)
