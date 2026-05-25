from __future__ import annotations

from typing import Any

from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest
from si_app.application.dto.supplies.get_inventory_turnover_request import GetInventoryTurnoverRequest
from si_app.application.dto.supplies.get_otd_request import GetOTDRequest
from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest

from si_app.domain.ports.supplies.cpv_query_repository_port import CpvQueryRepositoryPort
from si_app.domain.ports.supplies.inventory_turnover_query_repository_port import InventoryTurnoverQueryRepositoryPort
from si_app.domain.ports.supplies.otd_query_repository_port import OtdQueryRepositoryPort
from si_app.domain.ports.supplies.stock_value_query_repository_port import StockValueQueryRepositoryPort

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _cache_key(branch: str | None, start: str | None, end: str | None, extra: str = "") -> tuple:
    return (branch or "", start or "", end or "", extra)


class _CachedFetch:
    """Mixin para cachear chamadas HTTP por parametros do request dentro da mesma instancia."""

    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict[str, Any]] = {}

    def _fetch_cached(self, key: tuple, fetcher: callable) -> dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]


class DelpiCpvGateway(_CachedFetch, CpvQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        super().__init__(client)

    def _fetch_cpv(self, request: GetCPVRequest) -> dict[str, Any]:
        key = _cache_key(request.branch, request.start_date, request.end_date, "cpv")
        return self._fetch_cached(key, lambda: self._client.get_cpv(
            params={"branch": request.branch, "start_date": request.start_date, "end_date": request.end_date},
            authorization=bearer_authorization_from_context(),
        ))

    def get_cpv_summary(self, request: GetCPVRequest) -> dict:
        data = self._fetch_cpv(request)
        summary = data.get("summary") or {}
        return {
            "cpv_total": summary.get("cpv_total", 0),
            "total_movements": summary.get("total_movements", 0),
            "total_quantity": summary.get("total_quantity", 0),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }

    def get_cpv_by_cfop(self, request: GetCPVRequest) -> list[dict]:
        return self._fetch_cpv(request).get("by_cfop") or []

    def get_cpv_by_tm(self, request: GetCPVRequest) -> list[dict]:
        return self._fetch_cpv(request).get("by_tm") or []

    def get_cpv_top_products(self, request: GetCPVRequest) -> list[dict]:
        return self._fetch_cpv(request).get("top_products") or []

    def get_cpv_top_documents(self, request: GetCPVRequest) -> list[dict]:
        return self._fetch_cpv(request).get("top_documents") or []


class DelpiOtdSuppliesGateway(_CachedFetch, OtdQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        super().__init__(client)

    def _fetch_otd(self, request: GetOTDRequest) -> dict[str, Any]:
        key = _cache_key(request.branch, request.start_date, request.end_date, "otd")
        return self._fetch_cached(key, lambda: self._client.get_supplies_otd(
            params={"branch": request.branch, "start_date": request.start_date, "end_date": request.end_date},
            authorization=bearer_authorization_from_context(),
        ))

    def get_otd_summary(self, request: GetOTDRequest) -> dict:
        data = self._fetch_otd(request)
        summary = data.get("summary") or {}
        return {
            "branch": data.get("branch", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
            "total_lines": summary.get("total_lines", 0),
            "on_time_lines": summary.get("on_time_lines", 0),
            "late_lines": summary.get("late_lines", 0),
            "otd_percentage": summary.get("otd_percentage", 0),
        }

    def get_otd_monthly_breakdown(self, request: GetOTDRequest) -> list[dict]:
        return self._fetch_otd(request).get("monthly_breakdown") or []

    def get_top_late_suppliers(self, request: GetOTDRequest) -> list[dict]:
        return self._fetch_otd(request).get("top_late_suppliers") or []

    def get_late_deliveries(self, request: GetOTDRequest) -> list[dict]:
        return self._fetch_otd(request).get("late_deliveries") or []


class DelpiStockValueGateway(_CachedFetch, StockValueQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        super().__init__(client)

    def _fetch_stock(self, request: GetStockValueRequest) -> dict[str, Any]:
        key = _cache_key(
            request.branch, request.start_date, request.end_date,
            f"stock-{getattr(request, 'location', '') or ''}",
        )
        return self._fetch_cached(key, lambda: self._client.get_stock_value(
            params={
                "branch": request.branch,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "location": getattr(request, "location", None),
            },
            authorization=bearer_authorization_from_context(),
        ))

    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
        data = self._fetch_stock(request)
        summary = data.get("summary") or {}
        return {
            "branch": data.get("branch", ""),
            "location": data.get("location", ""),
            "total_stock_value": summary.get("total_stock_value", 0),
            "total_stock_quantity": summary.get("total_stock_quantity", 0),
            "total_records": summary.get("total_records", 0),
            "total_products": summary.get("total_products", 0),
            "total_locations": summary.get("total_locations", 0),
        }

    def get_stock_value_by_branch(self, request: GetStockValueRequest) -> list[dict]:
        return self._fetch_stock(request).get("by_branch") or []

    def get_stock_value_by_location(self, request: GetStockValueRequest) -> list[dict]:
        return self._fetch_stock(request).get("by_location") or []

    def get_top_products_by_stock_value(self, request: GetStockValueRequest) -> list[dict]:
        return self._fetch_stock(request).get("top_products") or []


class DelpiInventoryTurnoverGateway(_CachedFetch, InventoryTurnoverQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        super().__init__(client)

    def get_cpv_context(self, request: GetInventoryTurnoverRequest) -> dict:
        data = self._client.get_inventory_turnover(
            params={
                "branch": request.branch,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "location": getattr(request, "location", None),
            },
            authorization=bearer_authorization_from_context(),
        )
        cpv_ctx = data.get("cpv_context") or {}
        return {
            "cpv_total": cpv_ctx.get("cpv_total", 0),
            "total_movements": cpv_ctx.get("total_movements", 0),
            "total_quantity": cpv_ctx.get("total_quantity", 0),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }