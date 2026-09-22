"""Relatórios do Portal PCP — saldos e ordens de produção.

O dump de saldos na api-delpi é paginado e, no BFF, é remontado inteiro antes
do filtro de prefixo/busca. Sem cache, cada troca de página no MFE repetia
várias idas ao TOTVS — o mesmo padrão de Demanda/Materiais (snapshot + TTL).

O relatório de OPs pagina na api-delpi (`/production/pcp-orders`) com
`open_only` + `unbounded_delivery` por padrão, para não perder entrega futura
no recorte de 12 meses. Janela de `C2_DATRF` (`actual_end_*`) só vale para
OPs encerradas (`open_only=false`).
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
from production_control_app.domain.services.product_code_scope import (
    product_code_excluded_by_prefixes,
    product_code_matches_prefixes,
)

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

_PRODUCTION_ORDER_SORT_KEYS = frozenset(
    {
        "delivery_desc",
        "delivery_asc",
        "issue_desc",
        "issue_asc",
        "delay_desc",
        "delay_asc",
        "qty_desc",
        "qty_asc",
        "op_asc",
        "op_desc",
    }
)
_DEFAULT_PRODUCTION_ORDER_SORT = "op_asc"


@lru_cache(maxsize=1)
def _settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def _cache_ttl_seconds() -> int:
    try:
        return max(0, int(_settings().get("cacheTtlSeconds") or 120))
    except (TypeError, ValueError):
        return 120


def _tri_state_bool(value: Any, *, default: bool | None) -> bool | None:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"yes", "true", "1", "sim", "s"}:
        return True
    if text in {"no", "false", "0", "nao", "não", "n"}:
        return False
    if text in {"all", "any", "*"}:
        return None
    return default


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
    if "data" in payload:
        data = payload.get("data")
        return data if isinstance(data, dict) else {}
    return payload


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


def _excluded_product_code_prefixes(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("excludedProductCodePrefixes")
    if not isinstance(raw, list):
        return []
    return [_text(item) for item in raw if _text(item)]


def _user_identity(user: object | None) -> tuple[str, str]:
    if user is None:
        raise PermissionError("Sessão inválida.")
    user_id = str(getattr(user, "id", None) or "").strip()
    email = str(getattr(user, "email", None) or "").strip()
    if not user_id or not email or "@" not in email:
        raise PermissionError(
            "Não foi possível identificar usuário/e-mail para o agendamento."
        )
    return user_id, email


def _hour_minute_from_cron(cron: str) -> tuple[int, int]:
    """Cron Reports: ``minute hour …`` (ex.: ``30 7 * * 1-5``)."""
    parts = str(cron or "").strip().split()
    if len(parts) < 2:
        return 7, 0
    try:
        minute = int(parts[0])
        hour = int(parts[1])
    except ValueError:
        return 7, 0
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return 7, 0
    return hour, minute


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
        excluded_prefixes = _excluded_product_code_prefixes(cfg)
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
            and not product_code_excluded_by_prefixes(
                _text(item.get("product_code")), excluded_prefixes
            )
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
                "excluded_product_code_prefixes": excluded_prefixes,
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

    def get_email_schedule(self, user: object | None, *, branch: str) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        user_id, _email = _user_identity(user)
        try:
            payload = self._gateway.get_personal_stock_balances_subscription(
                user_id=user_id,
                branch=branch,
            )
        except DelpiGatewayError:
            raise
        data = _unwrap_data(payload)
        if not data:
            return {
                "branch": branch,
                "configured": False,
                "enabled": False,
                "hour": 7,
                "minute": 0,
                "timezone": "America/Sao_Paulo",
                "scheduleKind": "weekdays",
                "nextRunAt": None,
                "definitionId": None,
            }
        schedule = data.get("schedule") if isinstance(data.get("schedule"), dict) else {}
        definition = data.get("definition") if isinstance(data.get("definition"), dict) else {}
        hour = schedule.get("hour")
        minute = schedule.get("minute")
        if hour is None or minute is None:
            cron = str(schedule.get("cronExpression") or "")
            hour, minute = _hour_minute_from_cron(cron)
        return {
            "branch": branch,
            "configured": bool(data.get("configured")),
            "enabled": bool(schedule.get("enabled", False)),
            "hour": int(hour if hour is not None else 7),
            "minute": int(minute if minute is not None else 0),
            "timezone": str(schedule.get("timezone") or "America/Sao_Paulo"),
            "scheduleKind": str(schedule.get("scheduleKind") or "weekdays"),
            "nextRunAt": schedule.get("nextRunAt"),
            "definitionId": definition.get("id"),
        }

    def upsert_email_schedule(
        self,
        user: object | None,
        *,
        branch: str,
        hour: int,
        minute: int,
        enabled: bool = True,
    ) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        user_id, email = _user_identity(user)
        try:
            payload = self._gateway.upsert_personal_stock_balances_subscription(
                user_id=user_id,
                email=email,
                branch=branch,
                hour=int(hour),
                minute=int(minute),
                enabled=bool(enabled),
            )
        except DelpiGatewayError:
            raise
        data = _unwrap_data(payload)
        schedule = data.get("schedule") if isinstance(data.get("schedule"), dict) else {}
        definition = data.get("definition") if isinstance(data.get("definition"), dict) else {}
        resolved_hour = schedule.get("hour")
        resolved_minute = schedule.get("minute")
        if resolved_hour is None or resolved_minute is None:
            cron = str(schedule.get("cronExpression") or "")
            resolved_hour, resolved_minute = _hour_minute_from_cron(cron)
        return {
            "branch": branch,
            "configured": True,
            "enabled": bool(schedule.get("enabled", enabled)),
            "hour": int(resolved_hour if resolved_hour is not None else hour),
            "minute": int(resolved_minute if resolved_minute is not None else minute),
            "timezone": str(schedule.get("timezone") or "America/Sao_Paulo"),
            "scheduleKind": str(schedule.get("scheduleKind") or "weekdays"),
            "nextRunAt": schedule.get("nextRunAt"),
            "definitionId": definition.get("id"),
        }

    def production_orders(
        self,
        user: object | None,
        *,
        branch: str,
        op_key: str = "",
        product_code: str = "",
        mother_only: Any = None,
        open_only: Any = True,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        self._authorize(user, branch=branch)
        cfg = _settings()
        resolved_sort = _text(sort) or _DEFAULT_PRODUCTION_ORDER_SORT
        if resolved_sort not in _PRODUCTION_ORDER_SORT_KEYS:
            resolved_sort = _DEFAULT_PRODUCTION_ORDER_SORT
        page = max(1, int(page or 1))
        max_page_size = max(1, min(int(cfg.get("maxPageSize") or 200), 200))
        default_page_size = max(1, int(cfg.get("defaultPageSize") or 50))
        size = max(1, min(int(page_size or default_page_size), max_page_size))
        resolved_open_only = _tri_state_bool(open_only, default=True)
        resolved_mother_only = _tri_state_bool(mother_only, default=None)
        has_delivery_window = bool(_text(delivery_start) or _text(delivery_end))
        unbounded_delivery = not has_delivery_window
        closed_only = resolved_open_only is False
        actual_end_start_resolved = _text(actual_end_start) if closed_only else None
        actual_end_end_resolved = _text(actual_end_end) if closed_only else None
        filters = {
            "branch": branch,
            "page": page,
            "page_size": size,
            "sort": resolved_sort,
            "open_only": resolved_open_only,
            "mother_only": resolved_mother_only,
            "unbounded_delivery": unbounded_delivery,
            "op_key": _text(op_key) or None,
            "product_code": _text(product_code) or None,
            "delivery_start": _text(delivery_start) or None,
            "delivery_end": _text(delivery_end) or None,
            "actual_end_start": actual_end_start_resolved,
            "actual_end_end": actual_end_end_resolved,
        }
        try:
            items_payload = self._gateway.fetch_pcp_orders_catalog(**filters)
            summary_payload = self._gateway.fetch_pcp_orders_catalog_summary(
                **{key: value for key, value in filters.items() if key not in {"page", "page_size", "sort"}}
            )
        except DelpiGatewayError:
            raise

        items_data = _unwrap_data(items_payload)
        summary_data = _unwrap_data(summary_payload)
        upstream_summary = (
            summary_data.get("summary") if isinstance(summary_data.get("summary"), dict) else {}
        )
        pagination = items_data.get("pagination") if isinstance(items_data.get("pagination"), dict) else {}
        total = int(pagination.get("total") or 0)
        size_out = int(pagination.get("page_size") or size)
        page_out = int(pagination.get("page") or page)
        return {
            "branch": branch,
            "report_id": "production-orders",
            "filters": {
                "op_key": _text(op_key),
                "product_code": _text(product_code),
                "mother_only": resolved_mother_only,
                "open_only": resolved_open_only,
                "unbounded_delivery": unbounded_delivery,
                "delivery_start": _text(delivery_start) or None,
                "delivery_end": _text(delivery_end) or None,
                "actual_end_start": actual_end_start_resolved,
                "actual_end_end": actual_end_end_resolved,
                "sort": resolved_sort,
            },
            "summary": {
                "order_count": int(upstream_summary.get("total_orders") or total),
                "open_count": int(upstream_summary.get("open_orders") or 0),
                "planned_qty_sum": _float(upstream_summary.get("planned_qty_sum")),
                "pending_qty_sum": _float(upstream_summary.get("pending_qty_sum")),
            },
            "items": [self._map_production_order(item, branch) for item in _unwrap_items(items_payload)],
            "pagination": {
                "page": page_out,
                "page_size": size_out,
                "total": total,
                "total_pages": max(1, (total + size_out - 1) // size_out) if total else 1,
            },
        }

    @staticmethod
    def _map_production_order(item: dict[str, Any], branch: str) -> dict[str, Any]:
        production_order = _text(item.get("production_order") or item.get("op_key"))
        return {
            "production_order": production_order,
            "op_key": _text(item.get("op_key")) or production_order,
            "product_code": _text(item.get("product_code")),
            "product_description": _text(
                item.get("product_description") or item.get("description")
            ),
            "issue_date": _text(item.get("issue_date")) or None,
            "planned_start_date": _text(item.get("planned_start_date")) or None,
            "due_date": _text(item.get("due_date")) or None,
            "finish_date": _text(item.get("finish_date")) or None,
            "planned_qty": _float(item.get("planned_qty")),
            "pending_qty": _float(item.get("pending_qty")),
            "observation": _text(item.get("observation")) or None,
            "is_open": bool(item.get("is_open")),
            "is_mother": bool(item.get("is_mother")),
            "branch": _text(item.get("branch")) or branch,
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
