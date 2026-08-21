"""Demanda — orquestração da carteira a entregar para o PCP.

A api-delpi entrega o dump TOTVS inteiro, sem filtro nem paginação. Todo o
recorte (filial, busca, status, janela de entrega), a ordenação, a página e os
KPIs são resolvidos aqui, sobre um cache curto por processo — assim navegar
entre páginas e filtros não repete a consulta pesada.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable

from production_control_app.application.services.demand_settings import (
    setting_int,
    setting_list,
    setting_str,
)
from production_control_app.core.security import PC_DEMAND_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.demand_coverage_service import (
    STATUS_AT_RISK,
    STATUS_COVERED_BY_ORDER,
    STATUS_COVERED_BY_STOCK,
    STATUS_LATE,
    DemandCoverageService,
    DemandLine,
)

_FAR_FUTURE = date(9999, 12, 31)


def _unwrap(payload: Any, key: str) -> list[Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    source = data if isinstance(data, dict) else payload
    items = source.get(key) if isinstance(source, dict) else None
    return items if isinstance(items, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _iso_date(value: Any) -> date | None:
    text = _text(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class DemandQuery:
    branch: str
    search: str = ""
    status: str = ""
    due_from: date | None = None
    due_to: date | None = None
    sort: str = ""
    direction: str = "asc"
    page: int = 1
    page_size: int = 0


class _DemandSnapshotCache:
    """Cache por filial com TTL — evita repetir o dump a cada filtro/página."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._entries: dict[str, tuple[float, list[DemandLine]]] = {}

    def get(self, key: str) -> list[DemandLine] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, lines = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return lines

    def set(self, key: str, lines: list[DemandLine]) -> None:
        self._entries[key] = (time.monotonic(), lines)

    def clear(self) -> None:
        self._entries.clear()


_SNAPSHOT_CACHE = _DemandSnapshotCache(setting_int("cacheTtlSeconds", 120))


class DemandService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
        coverage: DemandCoverageService | None = None,
        today: date | None = None,
        cache: _DemandSnapshotCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._today = today
        self._coverage = coverage or DemandCoverageService(today=today)
        self._cache = cache if cache is not None else _SNAPSHOT_CACHE

    # ------------------------------------------------------------- helpers

    def _reference_date(self) -> date:
        return self._today or date.today()

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_DEMAND_VIEW):
            raise PermissionError("Você não tem permissão para ver a demanda.")

    def _load_lines(self, branch: str, *, refresh: bool = False) -> list[DemandLine]:
        if not refresh:
            cached = self._cache.get(branch)
            if cached is not None:
                return cached
        try:
            sales_orders = _unwrap(self._gateway.fetch_open_sales_orders(), "items")
            production_orders = _unwrap(self._gateway.fetch_open_production_orders(), "items")
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError("Não foi possível carregar a demanda em aberto.") from exc

        lines = self._coverage.build(
            open_sales_orders=sales_orders,
            open_production_orders=production_orders,
            branch=branch,
        )
        self._cache.set(branch, lines)
        return lines

    # ------------------------------------------------------------ filtering

    def _matches(self, line: DemandLine, query: DemandQuery) -> bool:
        if query.status and line.status != query.status:
            return False
        if query.due_from or query.due_to:
            if line.due_date is None:
                return False
            if query.due_from and line.due_date < query.due_from:
                return False
            if query.due_to and line.due_date > query.due_to:
                return False
        needle = query.search.strip().upper()
        if needle:
            haystack = " ".join(
                (
                    line.customer_name,
                    line.sales_order,
                    line.customer_order,
                    line.product_code,
                )
            ).upper()
            if needle not in haystack:
                return False
        return True

    def _sort_key(self, field: str):
        if field == "customer_name":
            return lambda line: (line.customer_name, line.sales_order, line.line_item)
        if field == "product_code":
            return lambda line: (line.product_code, line.due_date or _FAR_FUTURE)
        if field == "open_quantity":
            return lambda line: (line.open_quantity, line.due_date or _FAR_FUTURE)
        if field == "status":
            order = {
                STATUS_LATE: 0,
                STATUS_AT_RISK: 1,
                STATUS_COVERED_BY_ORDER: 2,
                STATUS_COVERED_BY_STOCK: 3,
            }
            return lambda line: (order.get(line.status, 9), line.due_date or _FAR_FUTURE)
        return lambda line: (line.due_date or _FAR_FUTURE, line.sales_order, line.line_item)

    # -------------------------------------------------------------- summary

    def _summary(self, lines: Iterable[DemandLine]) -> dict[str, Any]:
        today = self._reference_date()
        rows = list(lines)
        next_due = min(
            (line.due_date for line in rows if line.due_date and line.due_date >= today),
            default=None,
        )
        return {
            "line_count": len(rows),
            "open_quantity": round(sum(line.open_quantity for line in rows), 3),
            "late_line_count": sum(1 for line in rows if line.status == STATUS_LATE),
            "at_risk_line_count": sum(1 for line in rows if line.status == STATUS_AT_RISK),
            "uncovered_quantity": round(sum(line.uncovered_quantity for line in rows), 3),
            "customer_count": len({line.customer_code or line.customer_name for line in rows}),
            "product_count": len({line.product_code for line in rows}),
            "next_due_date": next_due.isoformat() if next_due else None,
        }

    def _horizon(self, lines: Iterable[DemandLine]) -> list[dict[str, Any]]:
        """Saldo agrupado por semana de entrega; o atraso vira o primeiro balde."""
        today = self._reference_date()
        buckets: dict[str, dict[str, Any]] = {}
        late_key = "late"
        for line in lines:
            if line.due_date is None:
                continue
            if line.due_date < today:
                key, label, start = late_key, "Atrasado", None
            else:
                monday = line.due_date - timedelta(days=line.due_date.weekday())
                key, label, start = monday.isoformat(), monday.isoformat(), monday
            bucket = buckets.setdefault(
                key,
                {
                    "key": key,
                    "label": label,
                    "start_date": start.isoformat() if start else None,
                    "open_quantity": 0.0,
                    "line_count": 0,
                    "late": start is None,
                },
            )
            bucket["open_quantity"] += line.open_quantity
            bucket["line_count"] += 1

        ordered = sorted(
            buckets.values(),
            key=lambda item: ("" if item["late"] else "1", item["start_date"] or ""),
        )
        limit = setting_int("horizonBuckets", 8)
        trimmed = ordered[: limit + 1] if limit else ordered
        for bucket in trimmed:
            bucket["open_quantity"] = round(bucket["open_quantity"], 3)
        return trimmed

    # --------------------------------------------------------------- public

    def list_demand(
        self,
        user: object | None,
        *,
        branch: str,
        search: str = "",
        status: str = "",
        due_from: str | None = None,
        due_to: str | None = None,
        sort: str | None = None,
        direction: str = "asc",
        page: int = 1,
        page_size: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        self._authorize(user, branch=code)

        allowed_statuses = setting_list("statuses")
        requested_status = _text(status)
        if requested_status and requested_status not in allowed_statuses:
            requested_status = ""

        allowed_sorts = setting_list("sortFields")
        requested_sort = _text(sort) or setting_str("defaultSort", "due_date")
        if requested_sort not in allowed_sorts:
            requested_sort = setting_str("defaultSort", "due_date")

        max_page_size = setting_int("maxPageSize", 200)
        resolved_size = page_size or setting_int("defaultPageSize", 50)
        resolved_size = max(1, min(int(resolved_size), max_page_size))
        resolved_page = max(int(page or 1), 1)

        query = DemandQuery(
            branch=code,
            search=_text(search),
            status=requested_status,
            due_from=_iso_date(due_from),
            due_to=_iso_date(due_to),
            sort=requested_sort,
            direction="desc" if _text(direction).lower() == "desc" else "asc",
            page=resolved_page,
            page_size=resolved_size,
        )

        all_lines = self._load_lines(code, refresh=refresh)
        filtered = [line for line in all_lines if self._matches(line, query)]
        filtered.sort(key=self._sort_key(query.sort), reverse=query.direction == "desc")

        total = len(filtered)
        total_pages = (total + query.page_size - 1) // query.page_size if total else 0
        start = (query.page - 1) * query.page_size
        page_items = filtered[start : start + query.page_size]
        today = self._reference_date()

        return {
            "branch": code,
            "items": [line.to_dict(today) for line in page_items],
            "summary": self._summary(filtered),
            "horizon": self._horizon(filtered),
            "filters": {
                "search": query.search,
                "status": query.status,
                "due_from": query.due_from.isoformat() if query.due_from else None,
                "due_to": query.due_to.isoformat() if query.due_to else None,
                "sort": query.sort,
                "direction": query.direction,
                "statuses": list(allowed_statuses),
            },
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total": total,
                "total_pages": total_pages,
                "is_complete": query.page >= total_pages if total_pages else True,
            },
        }
