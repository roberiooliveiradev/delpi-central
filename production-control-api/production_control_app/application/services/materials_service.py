"""Materiais — excesso e falta de SC1 para o PCP.

A api-delpi entrega o dump TOTVS (SC1 + cobertura + ESTSEG). A regra
(FIFO, só documento 100% desnecessário; falta após alocar SC1), o recorte
e a página ficam aqui.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any

from production_control_app.application.services.materials_settings import (
    setting_int,
    setting_list,
    setting_map,
    setting_str,
)
from production_control_app.core.security import PC_MATERIALS_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.materials_excess import (
    EliminableRequest,
    ShortageProduct,
    classify_fully_eliminable,
    classify_shortage_products,
)

_FAR_FUTURE = date(9999, 12, 31)
_VIEWS = frozenset({"excess", "shortage"})


def _unwrap(payload: Any, key: str) -> list[Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    source = data if isinstance(data, dict) else payload
    items = source.get(key) if isinstance(source, dict) else None
    return items if isinstance(items, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_view(view: str | None) -> str:
    requested = _text(view).lower()
    if requested in _VIEWS:
        return requested
    return setting_str("defaultView", "excess")


@dataclass(frozen=True, slots=True)
class MaterialsSnapshot:
    excess: tuple[EliminableRequest, ...]
    shortage: tuple[ShortageProduct, ...]


@dataclass(frozen=True, slots=True)
class MaterialsQuery:
    branch: str
    view: str
    search: str = ""
    sort: str = ""
    direction: str = "asc"
    page: int = 1
    page_size: int = 0


class _MaterialsSnapshotCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._entries: dict[str, tuple[float, MaterialsSnapshot]] = {}

    def get(self, key: str) -> MaterialsSnapshot | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, snapshot = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return snapshot

    def set(self, key: str, snapshot: MaterialsSnapshot) -> None:
        self._entries[key] = (time.monotonic(), snapshot)


_SNAPSHOT_CACHE = _MaterialsSnapshotCache(setting_int("cacheTtlSeconds", 120))


class MaterialsService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
        cache: _MaterialsSnapshotCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._cache = cache if cache is not None else _SNAPSHOT_CACHE

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MATERIALS_VIEW):
            raise PermissionError("Você não tem permissão para ver os materiais.")

    def _load_snapshot(self, branch: str, *, refresh: bool = False) -> MaterialsSnapshot:
        if not refresh:
            cached = self._cache.get(branch)
            if cached is not None:
                return cached
        try:
            payload = self._gateway.fetch_purchase_request_open_coverage(branch=branch)
            raw_items = _unwrap(payload, "items")
            raw_products = _unwrap(payload, "products")
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível carregar as solicitações de compra em aberto."
            ) from exc
        snapshot = MaterialsSnapshot(
            excess=tuple(classify_fully_eliminable(raw_items)),
            shortage=tuple(classify_shortage_products(raw_items, raw_products)),
        )
        self._cache.set(branch, snapshot)
        return snapshot

    def _matches_excess(self, row: EliminableRequest, query: MaterialsQuery) -> bool:
        needle = query.search.strip().upper()
        if not needle:
            return True
        haystack = " ".join(
            (
                row.request_number,
                row.request_item,
                row.product_code,
                row.product_description,
                row.supplier_name,
            )
        ).upper()
        return needle in haystack

    def _matches_shortage(self, row: ShortageProduct, query: MaterialsQuery) -> bool:
        needle = query.search.strip().upper()
        if not needle:
            return True
        haystack = " ".join((row.product_code, row.product_description)).upper()
        return needle in haystack

    def _excess_sort_key(self, field: str):
        if field == "request_number":
            return lambda row: (row.request_number, row.request_item)
        if field == "product_code":
            return lambda row: (row.product_code, row.required_date or _FAR_FUTURE)
        if field == "open_quantity":
            return lambda row: (row.open_quantity, row.required_date or _FAR_FUTURE)
        if field == "projected_balance":
            return lambda row: (row.projected_balance, row.product_code)
        return lambda row: (
            row.required_date or _FAR_FUTURE,
            row.request_number,
            row.request_item,
        )

    def _shortage_sort_key(self, field: str):
        if field == "product_code":
            return lambda row: (row.product_code,)
        if field == "safety_stock":
            return lambda row: (row.safety_stock, row.product_code)
        if field == "projected_balance":
            return lambda row: (row.projected_balance, row.product_code)
        if field == "open_sc1_quantity":
            return lambda row: (row.open_sc1_quantity, row.product_code)
        return lambda row: (row.shortage_quantity, row.product_code)

    def _issues(self, snapshot: MaterialsSnapshot) -> list[dict[str, Any]]:
        catalog = setting_map("issues")
        counts = {
            "excess": len({row.product_code for row in snapshot.excess}),
            "shortage": len({row.product_code for row in snapshot.shortage}),
        }
        cards: list[dict[str, Any]] = []
        for view_id in setting_list("views"):
            meta = catalog.get(view_id)
            if not isinstance(meta, dict):
                continue
            card: dict[str, Any] = {
                "id": view_id,
                "title": str(meta.get("title") or "").strip(),
                "description": str(meta.get("description") or "").strip(),
                "severity": str(meta.get("severity") or "").strip() or "attention",
            }
            if view_id in counts:
                card["product_count"] = counts[view_id]
            else:
                card["kind"] = str(meta.get("kind") or "consult").strip() or "consult"
            cards.append(card)
        return cards

    def list_materials(
        self,
        user: object | None,
        *,
        branch: str,
        view: str | None = None,
        search: str = "",
        sort: str | None = None,
        direction: str = "asc",
        page: int = 1,
        page_size: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        self._authorize(user, branch=code)
        resolved_view = _normalize_view(view)

        if resolved_view == "shortage":
            allowed_sorts = setting_list("shortageSortFields")
            default_sort = setting_str("shortageDefaultSort", "shortage_quantity")
        else:
            allowed_sorts = setting_list("sortFields")
            default_sort = setting_str("defaultSort", "required_date")

        requested_sort = _text(sort) or default_sort
        if requested_sort not in allowed_sorts:
            requested_sort = default_sort

        max_page_size = setting_int("maxPageSize", 200)
        resolved_size = page_size or setting_int("defaultPageSize", 50)
        resolved_size = max(1, min(int(resolved_size), max_page_size))
        resolved_page = max(int(page or 1), 1)

        query = MaterialsQuery(
            branch=code,
            view=resolved_view,
            search=_text(search),
            sort=requested_sort,
            direction="desc" if _text(direction).lower() == "desc" else "asc",
            page=resolved_page,
            page_size=resolved_size,
        )

        snapshot = self._load_snapshot(code, refresh=refresh)
        if query.view == "shortage":
            filtered = [row for row in snapshot.shortage if self._matches_shortage(row, query)]
            filtered.sort(
                key=self._shortage_sort_key(query.sort),
                reverse=query.direction == "desc",
            )
        else:
            filtered = [row for row in snapshot.excess if self._matches_excess(row, query)]
            filtered.sort(
                key=self._excess_sort_key(query.sort),
                reverse=query.direction == "desc",
            )

        total = len(filtered)
        total_pages = (total + query.page_size - 1) // query.page_size if total else 0
        start = (query.page - 1) * query.page_size
        page_items = filtered[start : start + query.page_size]

        return {
            "branch": code,
            "view": query.view,
            "issues": self._issues(snapshot),
            "didactic": setting_map("didactic"),
            "items": [row.to_dict() for row in page_items],
            "summary": {
                "excess_product_count": len({row.product_code for row in snapshot.excess}),
                "shortage_product_count": len({row.product_code for row in snapshot.shortage}),
                "row_count": total,
            },
            "filters": {
                "search": query.search,
                "sort": query.sort,
                "direction": query.direction,
                "view": query.view,
            },
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total": total,
                "total_pages": total_pages,
                "is_complete": query.page >= total_pages if total_pages else True,
            },
        }
