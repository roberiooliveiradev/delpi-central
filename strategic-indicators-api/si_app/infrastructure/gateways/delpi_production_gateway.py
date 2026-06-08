from __future__ import annotations

import os
from typing import Any, Callable

from si_app.infrastructure.gateways.http_params import opt_float, std_http_params
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient, DelpiApiError

_DEFAULT_BRANCHES = ["01", "02"]


def _known_branches() -> list[str]:
    env = os.getenv("DELPI_KNOWN_BRANCHES", "")
    if env.strip():
        return [b.strip() for b in env.split(",") if b.strip()]
    return list(_DEFAULT_BRANCHES)


class DelpiProductionSheetsGateway:
    """MO, custo de produção e depreciação via planilhas na api-delpi."""

    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict] = {}

    def _fetch_cached(self, key: tuple, fetcher: Callable[[], dict]) -> dict:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]

    def get_direct_labor_cost_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        key = ("direct-labor", branch or "", start_date or "", end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_direct_labor_cost_pct(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return opt_float(data.get("direct_labor_cost_pct"))

    def get_production_cost_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        key = ("production-cost", branch or "", start_date or "", end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_production_cost_pct(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return opt_float(data.get("production_cost_pct"))

    def get_depreciation_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        key = ("depreciation", branch or "", start_date or "", end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_depreciation_pct(
                params=std_http_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return opt_float(data.get("depreciation_pct"))


class DelpiProductionGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_oee_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        data = self._client.get_overall_equipment_effectiveness(
            params=std_http_params(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            ),
            authorization=bearer_authorization_from_context(),
        )
        return opt_float(data.get("overall_equipment_effectiveness_pct"))

    def list_oee_by_branch(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        auth = bearer_authorization_from_context()
        results: list[dict[str, Any]] = []
        for branch in _known_branches():
            try:
                data = self._client.get_overall_equipment_effectiveness(
                    params=std_http_params(
                        branch=branch,
                        start_date=start_date,
                        end_date=end_date,
                    ),
                    authorization=auth,
                )
                oee_pct = opt_float(data.get("overall_equipment_effectiveness_pct"))
                if oee_pct is not None:
                    results.append({"branch": branch, "oee_pct": oee_pct})
            except DelpiApiError:
                continue
        return results

    def get_on_time_delivery_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        data = self._client.get_on_time_delivery(
            params=std_http_params(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            ),
            authorization=bearer_authorization_from_context(),
        )
        return opt_float(data.get("on_time_delivery_pct"))

    def list_on_time_delivery_by_branch(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict[str, Any]]:
        auth = bearer_authorization_from_context()
        results: list[dict[str, Any]] = []
        for branch in _known_branches():
            try:
                data = self._client.get_on_time_delivery(
                    params=std_http_params(
                        branch=branch,
                        start_date=start_date,
                        end_date=end_date,
                    ),
                    authorization=auth,
                )
                pct = opt_float(data.get("on_time_delivery_pct"))
                if pct is not None:
                    results.append({"branch": branch, "on_time_delivery_pct": pct})
            except DelpiApiError:
                continue
        return results
