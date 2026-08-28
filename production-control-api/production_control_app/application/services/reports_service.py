"""Relatórios do Portal PCP — saldos e futuros recortes.

O dump de saldos na api-delpi é paginado e, no BFF, é remontado inteiro antes
do filtro de prefixo/busca. Sem cache, cada troca de página no MFE repetia
várias idas ao TOTVS — o mesmo padrão de Demanda/Materiais (snapshot + TTL).
"""

from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.core.security import PC_REPORTS_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.product_code_scope import product_code_matches_prefixes

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "reports.json"

_SORT_KEYS = frozenset(
    {
        "product_code_asc",
        "product_code_desc",
        "quantity_asc",
        "quantity_desc",
        "stock_value_asc",
        "stock_value_desc",
    }
)


@lru_cache(maxsize=1)
def _settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def _cache_ttl_seconds() -> int:
    try:
        return max(0, int(_settings().get("cacheTtlSeconds") or 120))
    except (TypeError, ValueError):
        return 120


def _text(value: Any) -> str:
    return str(value or "").strip()


def _float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _unwrap_data(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _unwrap_items(payload: Any) -> list[dict[str, Any]]:
    data = _unwrap_data(payload)
    raw = data.get("items")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _pagination_total(payload: Any) -> int | None:
    data = _unwrap_data(payload)
    pagination = data.get("pagination")
    if not isinstance(pagination, dict):
        return None
    try:
        return int(pagination.get("total") or 0)
    except (TypeError, ValueError):
        return None


def _product_code_prefixes_for_branch(cfg: dict[str, Any], branch: str) -> list[str]:
    """Prefixos do relatório de saldos — SC (01) só 9…; ES (02) 8… e 9…."""
    by_branch = cfg.get("productCodePrefixesByBranch")
    if isinstance(by_branch, dict):
        raw = by_branch.get(branch)
        if isinstance(raw, list):
            prefixes = [_text(item) for item in raw if _text(item)]
            if prefixes:
                return prefixes
    fallback = [
        _text(item)
        for item in (cfg.get("productCodePrefixes") or [])
        if _text(item)
    ]
    return fallback or ["8", "9"]


class _StockBalancesSnapshotCache:
    """Cache por filial+armazém — paginar/filtrar não reconsulta a api-delpi."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._entries: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def get(self, key: str) -> list[dict[str, Any]] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, items = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return items

    def set(self, key: str, items: list[dict[str, Any]]) -> None:
        self._entries[key] = (time.monotonic(), items)

    def clear(self) -> None:
        self._entries.clear()


_SNAPSHOT_CACHE = _StockBalancesSnapshotCache(_cache_ttl_seconds())


class ReportsService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
        cache: _StockBalancesSnapshotCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._cache = cache if cache is not None else _SNAPSHOT_CACHE

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_REPORTS_VIEW):
            raise PermissionError("Você não tem permissão para ver os relatórios do Portal PCP.")

    def list_catalog(self, user: object | None, *, branch: str) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        cfg = _settings()
        reports = cfg.get("reports") if isinstance(cfg.get("reports"), list) else []
        return {
            "branch": branch,
            "reports": [
                {
                    "id": _text(item.get("id")),
                    "label": _text(item.get("label")),
                    "description": _text(item.get("description")),
                    "icon": _text(item.get("icon")) or "file-spreadsheet",
                    "eyebrow": _text(item.get("eyebrow")) or None,
                }
                for item in reports
                if isinstance(item, dict) and _text(item.get("id"))
            ],
        }

    def stock_balances(
        self,
        user: object | None,
        *,
        branch: str,
        search: str = "",
        sort: str | None = None,
        page: int = 1,
        page_size: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        cfg = _settings()
        warehouse = _text(cfg.get("warehouse")) or "01"
        prefixes = _product_code_prefixes_for_branch(cfg, branch)
        only_positive = bool(cfg.get("onlyPositive", True))
        fetch_page_size = max(1, min(int(cfg.get("fetchPageSize") or 500), 500))
        max_pages = max(1, int(cfg.get("maxFetchPages") or 40))
        default_sort = _text(cfg.get("defaultSort")) or "product_code_asc"
        resolved_sort = _text(sort) or default_sort
        if resolved_sort not in _SORT_KEYS:
            resolved_sort = default_sort
        page = max(1, int(page or 1))
        max_page_size = max(1, int(cfg.get("maxPageSize") or 200))
        default_page_size = max(1, int(cfg.get("defaultPageSize") or 50))
        size = max(1, min(int(page_size or default_page_size), max_page_size))
        needle = search.strip().lower()

        try:
            raw_items = self._load_balances(
                branch=branch,
                warehouse=warehouse,
                only_positive=only_positive,
                page_size=fetch_page_size,
                max_pages=max_pages,
                refresh=refresh,
            )
        except DelpiGatewayError:
            raise

        scoped = [
            item
            for item in raw_items
            if product_code_matches_prefixes(_text(item.get("product_code")), prefixes)
        ]
        if needle:
            scoped = [
                item
                for item in scoped
                if needle in _text(item.get("product_code")).lower()
                or needle in _text(item.get("description")).lower()
            ]

        scoped.sort(key=lambda row: self._sort_key(row, resolved_sort), reverse=resolved_sort.endswith("_desc"))

        total = len(scoped)
        start = (page - 1) * size
        page_items = scoped[start : start + size]
        total_quantity = round(sum(_float(item.get("quantity")) for item in scoped), 6)
        total_stock_value = round(sum(_float(item.get("stock_value")) for item in scoped), 6)

        return {
            "branch": branch,
            "report_id": "stock-balances",
            "filters": {
                "warehouse": warehouse,
                "product_code_prefixes": prefixes,
                "only_positive": only_positive,
                "search": search.strip(),
                "sort": resolved_sort,
            },
            "summary": {
                "product_count": total,
                "total_quantity": total_quantity,
                "total_stock_value": total_stock_value,
            },
            "items": [
                {
                    "product_code": _text(item.get("product_code")),
                    "description": _text(item.get("description")),
                    "branch": _text(item.get("branch")) or branch,
                    "warehouse": _text(item.get("warehouse")) or warehouse,
                    "quantity": _float(item.get("quantity")),
                    "unit_cost": _float(item.get("unit_cost")),
                    "stock_value": _float(item.get("stock_value")),
                }
                for item in page_items
            ],
            "pagination": {
                "page": page,
                "page_size": size,
                "total": total,
                "total_pages": max(1, (total + size - 1) // size) if total else 1,
            },
        }

    def _load_balances(
        self,
        *,
        branch: str,
        warehouse: str,
        only_positive: bool,
        page_size: int,
        max_pages: int,
        refresh: bool,
    ) -> list[dict[str, Any]]:
        cache_key = f"{branch}|{warehouse}|{int(only_positive)}"
        if not refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        items = self._fetch_all_balances(
            branch=branch,
            warehouse=warehouse,
            only_positive=only_positive,
            page_size=page_size,
            max_pages=max_pages,
        )
        self._cache.set(cache_key, items)
        return items

    def _fetch_all_balances(
        self,
        *,
        branch: str,
        warehouse: str,
        only_positive: bool,
        page_size: int,
        max_pages: int,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        page = 1
        expected_total: int | None = None
        while page <= max_pages:
            payload = self._gateway.fetch_stock_balances_items(
                branch=branch,
                warehouse=warehouse,
                only_positive=only_positive,
                page=page,
                page_size=page_size,
                sort="product_code_asc",
            )
            batch = _unwrap_items(payload)
            if expected_total is None:
                expected_total = _pagination_total(payload)
            collected.extend(batch)
            if not batch:
                break
            if expected_total is not None and len(collected) >= expected_total:
                break
            if len(batch) < page_size:
                break
            page += 1
        return collected

    @staticmethod
    def _sort_key(row: dict[str, Any], sort: str) -> Any:
        if sort.startswith("quantity"):
            return _float(row.get("quantity"))
        if sort.startswith("stock_value"):
            return _float(row.get("stock_value"))
        return _text(row.get("product_code")).lower()
