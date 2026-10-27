"""Market Data gateway — S2S HTTP client for external-data-api (PROC-0076).

Mirrors the company-registry adapter: individual service credential in
``X-Delpi-Service-Authorization`` (never the end-user Bearer), bounded
timeout, typed errors with status/code/retry_after, pagination and
window chunking handled here so the application layer sees flat lists.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Callable
from urllib.parse import urljoin

import requests
from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
)
from delpi_auth.service_errors import ServiceAuthError

from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.delpi_s2s_gateway import get_s2s_token_provider

logger = logging.getLogger("supplies-api.market_data")

DEFAULT_BASE_URL = "http://external-data-api:8000"

# Producer-side caps mirrored here: daily FX windows are bounded by the
# producer contract (366 days per request); longer BFF ranges chunk.
FX_CHUNK_DAYS = 366
MAX_PAGES = 25
PAGE_LIMIT = 500

Transport = Callable[..., Any]


def _requests_transport(url: str, *, headers: dict, timeout: float, params=None) -> Any:
    return requests.get(url, headers=headers, timeout=timeout, params=params)


def _requests_put_transport(
    url: str, *, headers: dict, timeout: float, json_body=None
) -> Any:
    return requests.put(url, headers=headers, timeout=timeout, json=json_body)


class MarketDataGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        retry_after: int | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        super().__init__(message)


def _error_code(response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    if isinstance(payload, dict):
        code = payload.get("code")
        if isinstance(code, str) and code:
            return code
    return None


class MarketDataGateway:
    """Read-only access to persisted market data via S2S."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
        put_transport: Any | None = None,
        token_provider: Any | None = None,
    ) -> None:
        self._base_url = (
            base_url or getattr(Settings, "EXTERNAL_DATA_API_BASE_URL", "")
        ).rstrip("/") or DEFAULT_BASE_URL
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(
                getattr(Settings, "EXTERNAL_DATA_API_TIMEOUT_SECONDS", 10) or 10
            )
        )
        self._transport = transport or _requests_transport
        self._put_transport = put_transport or _requests_put_transport
        self._token_provider = token_provider

    # --- public surface ------------------------------------------------------

    def catalog(self) -> dict[str, Any]:
        return self._get("/v1/market-data/catalog")

    def ingestion_status(self) -> dict[str, Any]:
        return self._get("/v1/market-data/ingestion-status")

    def metal_observations(
        self, instrument_code: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """Full unpaginated list — pages are an implementation detail."""
        return self._paged(
            "/v1/market-data/metals/observations",
            {
                "instrument_code": instrument_code,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "limit": PAGE_LIMIT,
            },
        )

    def fx_observations(
        self, rate_kind: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """Daily FX — chunked to the producer's 366-day window."""
        items: list[dict[str, Any]] = []
        chunk_start = date_from
        while chunk_start <= date_to:
            chunk_end = min(
                date_to, chunk_start + timedelta(days=FX_CHUNK_DAYS - 1)
            )
            items.extend(
                self._paged(
                    "/v1/market-data/fx/observations",
                    {
                        "pair": "USD/BRL",
                        "rate_kind": rate_kind,
                        "date_from": chunk_start.isoformat(),
                        "date_to": chunk_end.isoformat(),
                        "limit": PAGE_LIMIT,
                    },
                )
            )
            chunk_start = chunk_end + timedelta(days=1)
        return items

    def comex_imports(
        self,
        ncm_code: str,
        date_from: date,
        date_to: date,
        *,
        country_code: str | None = None,
        state_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Monthly import observations at (month × country × state) grain."""
        params: dict[str, Any] = {
            "ncm_code": ncm_code,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "limit": PAGE_LIMIT,
        }
        if country_code:
            params["country_code"] = country_code
        if state_code:
            params["state_code"] = state_code
        return self._paged("/v1/market-data/comex/imports", params)

    def producer_price_observations(
        self, series_id: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        return self._paged(
            "/v1/market-data/producer-prices/observations",
            {
                "series_id": series_id,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "limit": PAGE_LIMIT,
            },
        )

    def put_ncm_allowlist(
        self, ncm_code: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        """Governance-synced allowlist write — single attempt, no retry."""
        return self._put(f"/v1/market-data/comex/ncm-allowlist/{ncm_code}", body)

    # --- internals -----------------------------------------------------------

    def _paged(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor = None
        for _ in range(MAX_PAGES):
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            payload = self._get(path, params=page_params)
            items.extend(payload.get("items") or [])
            cursor = (payload.get("page_info") or {}).get("next_cursor")
            if not cursor:
                return items
        logger.warning("market_data_page_cap_reached path=%s", path)
        return items

    def _service_token(self) -> str:
        provider = self._token_provider or get_s2s_token_provider()
        try:
            return provider.get_token()
        except ServiceAuthError as exc:
            logger.warning("market_data_s2s_token_unavailable code=%s", exc.code)
            raise MarketDataGatewayError(
                "external data s2s authentication unavailable",
                status_code=503,
                code="s2s_unavailable",
            ) from exc

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = urljoin(self._base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "application/json",
            SERVICE_AUTHORIZATION_HEADER: build_service_authorization(
                self._service_token()
            ),
        }
        try:
            from flask import g, has_request_context

            if has_request_context():
                request_id = getattr(g, "request_id", None)
                if request_id:
                    headers["X-Correlation-Id"] = str(request_id)
        except ImportError:
            pass

        try:
            response = self._transport(
                url, headers=headers, timeout=self._timeout, params=params
            )
        except requests.Timeout as exc:
            logger.warning("market_data_timeout path=%s", path)
            raise MarketDataGatewayError(
                "external-data-api timeout",
                status_code=504,
                code="upstream_timeout",
            ) from exc
        except requests.RequestException as exc:
            logger.warning("market_data_unreachable path=%s", path)
            raise MarketDataGatewayError(
                "external-data-api unreachable",
                status_code=503,
                code="upstream_unavailable",
            ) from exc

        return self._checked_payload(response)

    def _put(self, path: str, body: dict[str, Any]) -> Any:
        url = urljoin(self._base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "application/json",
            SERVICE_AUTHORIZATION_HEADER: build_service_authorization(
                self._service_token()
            ),
        }
        try:
            from flask import g, has_request_context

            if has_request_context():
                request_id = getattr(g, "request_id", None)
                if request_id:
                    headers["X-Correlation-Id"] = str(request_id)
        except ImportError:
            pass

        try:
            response = self._put_transport(
                url, headers=headers, timeout=self._timeout, json_body=body
            )
        except requests.Timeout as exc:
            logger.warning("market_data_timeout path=%s", path)
            raise MarketDataGatewayError(
                "external-data-api timeout",
                status_code=504,
                code="upstream_timeout",
            ) from exc
        except requests.RequestException as exc:
            logger.warning("market_data_unreachable path=%s", path)
            raise MarketDataGatewayError(
                "external-data-api unreachable",
                status_code=503,
                code="upstream_unavailable",
            ) from exc

        return self._checked_payload(response)

    def _checked_payload(self, response) -> Any:
        status = response.status_code
        if status == 429:
            retry_after = None
            try:
                retry_after = int(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = None
            raise MarketDataGatewayError(
                "external-data-api rate limited",
                status_code=429,
                code=_error_code(response) or "rate_limited",
                retry_after=retry_after or None,
            )
        if status >= 500:
            raise MarketDataGatewayError(
                "external-data-api server error",
                status_code=status,
                code=_error_code(response) or "upstream_error",
            )
        if status >= 400:
            raise MarketDataGatewayError(
                "external-data-api request rejected",
                status_code=status,
                code=_error_code(response) or "upstream_client_error",
            )

        try:
            return response.json()
        except ValueError as exc:
            raise MarketDataGatewayError(
                "external-data-api invalid payload",
                status_code=502,
                code="invalid_response",
            ) from exc
