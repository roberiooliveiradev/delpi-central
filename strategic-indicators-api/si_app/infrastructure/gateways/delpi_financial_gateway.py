from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.application.dto.financial.list_rol_by_branch_request import ListRolByBranchRequest
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    should_cache_rol_payload,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    get_cached_rol,
    rol_cache_key,
    set_cached_rol,
)
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from si_app.infrastructure.concurrency.context_thread import submit_in_request_context
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _std_financial_params(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str | None]:
    return {
        "branch": branch,
        "start_date": start_date,
        "end_date": end_date,
    }


class DelpiFinancialSheetsGateway:
    """EBITDA, custos fixos e PMR via planilhas na api-delpi."""

    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict] = {}

    def _fetch_cached(self, key: tuple, fetcher: callable) -> dict:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]

    def get_ebitda_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        key = ("ebitda", branch or "", start_date or "", end_date or "")
        return self._fetch_cached(
            key,
            lambda: self._client.get_ebitda_pct(
                params=_std_financial_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def get_fixed_cost_pct(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        key = ("fixed-cost", branch or "", start_date or "", end_date or "")
        return self._fetch_cached(
            key,
            lambda: self._client.get_fixed_cost_pct(
                params=_std_financial_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )

    def get_pmr(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        key = ("pmr", branch or "", start_date or "", end_date or "")
        return self._fetch_cached(
            key,
            lambda: self._client.get_pmr(
                params=_std_financial_params(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                ),
                authorization=bearer_authorization_from_context(),
            ),
        )


class DelpiFinancialGateway(FinancialQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_rol(self, request: GetRolRequest) -> dict:
        cache_key = rol_cache_key(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        cached = get_cached_rol(cache_key)
        if cached is not None:
            return cached

        payload = self._fetch_rol(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        if should_cache_rol_payload(payload):
            set_cached_rol(cache_key, payload)
        return payload

    def list_rol_by_branch(self, request: ListRolByBranchRequest) -> dict[str, dict]:
        result: dict[str, dict] = {}
        branches_to_fetch: list[str] = []

        for branch in request.branches:
            cache_key = rol_cache_key(
                branch=branch,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            cached = get_cached_rol(cache_key)
            if cached is not None:
                result[branch] = cached
            else:
                branches_to_fetch.append(branch)

        if not branches_to_fetch:
            return result

        if len(branches_to_fetch) == 1:
            branch = branches_to_fetch[0]
            payload = self._fetch_and_cache_rol(
                branch=branch,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            result[branch] = payload
            return result

        auth = bearer_authorization_from_context()
        max_workers = min(len(branches_to_fetch), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                submit_in_request_context(
                    executor,
                    lambda branch_code=branch_code: self._fetch_and_cache_rol(
                        branch=branch_code,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        authorization=auth,
                    ),
                ): branch_code
                for branch_code in branches_to_fetch
            }
            for future in as_completed(futures):
                branch_code = futures[future]
                result[branch_code] = future.result()

        return result

    def _fetch_and_cache_rol(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        authorization: str | None = None,
    ) -> dict:
        cache_key = rol_cache_key(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        cached = get_cached_rol(cache_key)
        if cached is not None:
            return cached

        payload = self._fetch_rol(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            authorization=authorization,
        )
        if should_cache_rol_payload(payload):
            set_cached_rol(cache_key, payload)
        return payload

    def _fetch_rol(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
        authorization: str | None = None,
    ) -> dict:
        return self._client.get_rol(
            params={
                "branch": branch,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=authorization or bearer_authorization_from_context(),
        )
