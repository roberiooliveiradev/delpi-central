from __future__ import annotations

from typing import Any, Callable

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _cache_key(*parts: str | None) -> tuple:
    return tuple(part or "" for part in parts)


class DelpiQualityGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict[str, Any]] = {}

    def _fetch_cached(self, key: tuple, fetcher: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]

    def get_ppm_summary(
        self,
        *,
        ppm_type: str,
        branch: str | None,
        date_start: str | None,
        date_end: str | None,
        product_prefix: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "branch": branch,
            "date_start": date_start,
            "date_end": date_end,
        }
        if product_prefix:
            params["product_prefix"] = product_prefix

        return self._client.get_ppm_summary(
            ppm_type,
            params=params,
            authorization=bearer_authorization_from_context(),
        )

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        data = self._client.list_quality_branches(
            params={"date_start": date_start, "date_end": date_end},
            authorization=bearer_authorization_from_context(),
        )
        branches = data.get("branches") or data.get("items") or []
        if isinstance(branches, list) and all(isinstance(b, str) for b in branches):
            return branches
        return [str(b) for b in branches if b]

    def get_kaizen_summary(
        self,
        *,
        branch: str | None,
        date_start: str | None,
        date_end: str | None,
        title: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        key = _cache_key(
            "kaizen",
            branch,
            date_start,
            date_end,
            title,
            status,
        )
        return self._fetch_cached(
            key,
            lambda: self._client.get_kaizen_summary(
                params={
                    "branch": branch,
                    "date_start": date_start,
                    "date_end": date_end,
                    "title": title,
                    "status": status,
                },
                authorization=bearer_authorization_from_context(),
            ),
        )

    def get_audit_5s_summary(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        key = _cache_key(
            "audit-5s",
            branch,
            start_date,
            end_date,
        )
        return self._fetch_cached(
            key,
            lambda: self._client.get_audit_5s_summary(
                params={
                    "branch": branch,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                authorization=bearer_authorization_from_context(),
            ),
        )
