"""Portal inventory stock balances — BFF over api-delpi stock-balances.

E10 rules:
- capability supplies.access
- unit scope only 01/02; empty/all → explicit 01+02 downstream
- always only_positive=false (zero + negative included)
- never omit branch or send branch=all upstream
- never recompute business fields; passthrough producer data
"""

from __future__ import annotations

from typing import Any

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.authorization_service import AuthorizationService
from app.application.services.overview_composition_service import (
    normalize_overview_branches,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

ALLOWED_SORT = frozenset(
    {
        "stock_value_desc",
        "stock_value_asc",
        "quantity_desc",
        "quantity_asc",
        "product_code_asc",
        "product_code_desc",
    }
)
DEFAULT_SORT = "stock_value_desc"
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

_ITEM_FIELDS = (
    "product_code",
    "description",
    "unit_of_measure",
    "branch",
    "warehouse",
    "warehouse_label",
    "quantity",
    "unit_cost",
    "stock_value",
)

_BY_WAREHOUSE_FIELDS = (
    "branch",
    "warehouse",
    "warehouse_label",
    "product_count",
    "total_quantity",
    "total_stock_value",
    "total_stock_value_vatu1",
)

_SUMMARY_FIELDS = (
    "branch",
    "warehouse",
    "product_count",
    "total_quantity",
    "total_stock_value",
    "total_stock_value_vatu1",
    "warehouse_count",
    "valuation",
)


def _parse_positive_int(raw: str | int | None, *, field: str, default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}") from exc
    if value < 1:
        raise ValueError(f"Invalid {field}")
    return value


def _ordered_operational(codes: list[str]) -> list[str]:
    """Deterministic 01 then 02 order for upstream params."""
    selected = set(codes)
    return [code for code in OPERATIONAL_UNITS if code in selected]


def _project(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {key: row.get(key) for key in fields}


class InventoryStockBalancesService:
    def __init__(
        self,
        *,
        delpi_reads: SuppliesDelpiReads | None = None,
        authorization: AuthorizationService | None = None,
    ) -> None:
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.authorization = authorization or AuthorizationService()

    def _authorize_and_normalize_branches(
        self,
        user: EffectiveUser,
        branches: list[str] | None,
    ) -> list[str]:
        allowed = self.authorization.allowed_units(user)
        if not allowed and not user.is_superadmin:
            raise AuthorizationError("Forbidden")
        effective = _ordered_operational(normalize_overview_branches(branches))
        for code in effective:
            self.authorization.require_unit(user, code)
        return effective

    def get_summary(
        self,
        user: EffectiveUser,
        *,
        branches: list[str] | None,
        warehouse: str | None,
    ) -> dict[str, Any]:
        effective = self._authorize_and_normalize_branches(user, branches)
        warehouse_code = (warehouse or "").strip() or None
        data = self.delpi_reads.get_stock_balances_summary(
            access_token=user.access_token or "",
            branches=effective,
            warehouse=warehouse_code,
            only_positive=False,
        )
        summary = data.get("summary") if isinstance(data, dict) else None
        by_warehouse = data.get("by_warehouse") if isinstance(data, dict) else None
        return {
            "summary": _project(summary, _SUMMARY_FIELDS)
            if isinstance(summary, dict)
            else {},
            "by_warehouse": [
                _project(row, _BY_WAREHOUSE_FIELDS)
                for row in (by_warehouse or [])
                if isinstance(row, dict)
            ],
            "applied_filters": {
                "branches": list(effective),
                "warehouse": warehouse_code,
            },
        }

    def list_items(
        self,
        user: EffectiveUser,
        *,
        branches: list[str] | None,
        warehouse: str | None,
        page: str | int | None,
        page_size: str | int | None,
        sort: str | None,
    ) -> dict[str, Any]:
        effective = self._authorize_and_normalize_branches(user, branches)
        warehouse_code = (warehouse or "").strip() or None

        page_number = _parse_positive_int(
            None if page is None else str(page),
            field="page",
            default=DEFAULT_PAGE,
        )
        size = _parse_positive_int(
            None if page_size is None else str(page_size),
            field="page_size",
            default=DEFAULT_PAGE_SIZE,
        )
        if size > MAX_PAGE_SIZE:
            raise ValueError("Invalid page_size")

        resolved_sort = (sort or DEFAULT_SORT).strip() or DEFAULT_SORT
        if resolved_sort not in ALLOWED_SORT:
            raise ValueError("Invalid sort")

        data = self.delpi_reads.get_stock_balances_items(
            access_token=user.access_token or "",
            branches=effective,
            warehouse=warehouse_code,
            only_positive=False,
            page=page_number,
            page_size=size,
            sort=resolved_sort,
        )
        if not isinstance(data, dict):
            data = {}
        items_raw = data.get("items") if isinstance(data.get("items"), list) else []
        items = [
            _project(row, _ITEM_FIELDS) for row in items_raw if isinstance(row, dict)
        ]
        total = int(data.get("total") or 0)
        page_size_out = int(data.get("page_size") or size)
        page_out = int(data.get("page") or page_number)
        total_pages = int(
            data.get("total_pages")
            or ((total + page_size_out - 1) // page_size_out if total else 0)
        )
        pagination = data.get("pagination")
        if not isinstance(pagination, dict):
            pagination = {
                "page": page_out,
                "page_size": page_size_out,
                "total": total,
                "total_pages": total_pages,
                "is_complete": page_out >= total_pages if total_pages else True,
            }
        return {
            "items": items,
            "page": page_out,
            "page_size": page_size_out,
            "total": total,
            "total_pages": total_pages,
            "sort": data.get("sort") or resolved_sort,
            "pagination": pagination,
            "applied_filters": {
                "branches": list(effective),
                "warehouse": warehouse_code,
                "page": page_out,
                "page_size": page_size_out,
                "sort": resolved_sort,
            },
        }
