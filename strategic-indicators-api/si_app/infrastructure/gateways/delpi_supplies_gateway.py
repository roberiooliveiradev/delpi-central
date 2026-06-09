from __future__ import annotations

from typing import Any, Callable

from si_app.infrastructure.gateways.http_params import std_http_params
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _cache_key(
    branch: str | None,
    start: str | None,
    end: str | None,
    extra: str = "",
) -> tuple:
    return (branch or "", start or "", end or "", extra)


class DelpiSuppliesGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict[str, Any]] = {}

    def _fetch_cached(self, key: tuple, fetcher: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]

    def fetch_cpv_raw(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        key = _cache_key(branch, start_date, end_date, "cpv")
        return self._fetch_cached(
            key,
            lambda: self._client.get_cpv(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def fetch_otd_raw(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        key = _cache_key(branch, start_date, end_date, "otd")
        return self._fetch_cached(
            key,
            lambda: self._client.get_supplies_otd(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def fetch_stock_value_raw(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        location: str | None = None,
    ) -> dict[str, Any]:
        key = _cache_key(
            branch,
            start_date,
            end_date,
            f"stock-{location or ''}",
        )
        return self._fetch_cached(
            key,
            lambda: self._client.get_stock_value(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    summary_only="true",
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def fetch_inventory_turnover_raw(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        location: str | None = None,
    ) -> dict[str, Any]:
        key = _cache_key(
            branch,
            start_date,
            end_date,
            f"inventory-turnover-{location or ''}",
        )
        return self._fetch_cached(
            key,
            lambda: self._client.get_inventory_turnover(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def fetch_negotiation_savings_summary(
        self,
        *,
        branch: str | None = None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        key = _cache_key(branch, start_date, end_date, "negotiation-savings")
        return self._fetch_cached(
            key,
            lambda: self._client.get_supplies_negotiation_savings_summary(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )
