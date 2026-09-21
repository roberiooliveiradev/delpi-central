"""Compose Portal late deliveries from api-delpi purchase-order-otd panel.

Period filters DT_DIGITACAO. Late/on_time stay in the producer (DIAS).
Consolidated 01+02 never calls the producer without branch.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Any, Callable

from app.application.security.supplies_permissions import OPERATIONAL_UNITS
from app.application.services.authorization_service import AuthorizationService
from app.application.services.overview_composition_service import (
    normalize_overview_branches,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

ALLOWED_STATUS = frozenset({"late", "on_time"})
ALLOWED_SORT = frozenset(
    {
        "status",
        "branch",
        "order_number",
        "order_item",
        "product_code",
        "product_description",
        "supplier_code",
        "supplier_name",
        "supplier_short_name",
        "expected_delivery_date",
        "receipt_entry_date",
        "quantity",
        "days_diff",
    }
)
DEFAULT_STATUS = "late"
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 1000
PRODUCER_FETCH_PAGE_SIZE = 1000
_MAX_FETCH_PAGES = 50

_LINE_FIELDS = (
    "branch",
    "supplier_code",
    "supplier_store",
    "supplier_name",
    "supplier_short_name",
    "document",
    "order_number",
    "order_item",
    "product_code",
    "product_description",
    "product_type",
    "quantity",
    "purchase_order_issue_date",
    "expected_delivery_date",
    "receipt_entry_date",
    "invoice_issue_date",
    "days_diff",
    "is_on_time",
    "status",
)


def current_month_bounds(today: date | None = None) -> tuple[str, str]:
    day = today or date.today()
    start = day.replace(day=1)
    end = day.replace(day=monthrange(day.year, day.month)[1])
    return start.isoformat(), end.isoformat()


def _parse_positive_int(raw: str | None, *, field: str, default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}") from exc
    if value < 1:
        raise ValueError(f"Invalid {field}")
    return value


def _sort_key_for(
    item: dict[str, Any],
    *,
    sort_by: str | None,
    sort_dir: str,
) -> tuple:
    descending = (sort_dir or "asc").lower() == "desc"

    def _cell(column: str) -> tuple[int, Any]:
        value = item.get(column)
        if value is None or value == "":
            return (1, "") if not descending else (0, "")
        if column in {"quantity", "days_diff", "is_on_time"}:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                numeric = 0.0
            return (0, numeric)
        return (0, str(value))

    primary = (sort_by or "").strip().lower()
    if primary and primary in ALLOWED_SORT:
        cell = _cell(primary)
        ordered = cell if not descending else (cell[0], _negate(cell[1]))
        tie = [
            _cell(column)
            for column in ("branch", "order_number", "order_item")
            if column != primary
        ]
        return (ordered, *tie)

    # Producer default: status DESC, expected_delivery_date DESC, branch, order_number, order_item
    return (
        _negate_cell(_cell("status")),
        _negate_cell(_cell("expected_delivery_date")),
        _cell("branch"),
        _cell("order_number"),
        _cell("order_item"),
    )


def _negate(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return -value
    if isinstance(value, str):
        return tuple(-ord(ch) for ch in value)
    return value


def _negate_cell(cell: tuple[int, Any]) -> tuple[int, Any]:
    return (cell[0], _negate(cell[1]))


def _project_line(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in _LINE_FIELDS}


def _merge_summaries(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    total_lines = 0
    on_time_lines = 0
    late_lines = 0
    for summary in summaries:
        total_lines += int(summary.get("total_lines") or 0)
        on_time_lines += int(summary.get("on_time_lines") or 0)
        late_lines += int(summary.get("late_lines") or 0)
    purchase_order_otd_pct = (
        round(on_time_lines * 100.0 / total_lines, 2) if total_lines > 0 else None
    )
    late_percentage = (
        round(late_lines * 100.0 / total_lines, 2) if total_lines > 0 else 0.0
    )
    return {
        "total_lines": total_lines,
        "on_time_lines": on_time_lines,
        "late_lines": late_lines,
        "purchase_order_otd_pct": purchase_order_otd_pct,
        "late_percentage": late_percentage,
    }


class LateDeliveriesCompositionService:
    def __init__(
        self,
        *,
        delpi_reads: SuppliesDelpiReads | None = None,
        authorization: AuthorizationService | None = None,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        self.delpi_reads = delpi_reads or SuppliesDelpiReads()
        self.authorization = authorization or AuthorizationService()
        self._today = today_provider or date.today

    def compose(
        self,
        user: EffectiveUser,
        *,
        branches: list[str] | None,
        status: str | None,
        start_date: str | None,
        end_date: str | None,
        page: str | int | None,
        page_size: str | int | None,
        sort_by: str | None,
        sort_dir: str | None,
    ) -> dict[str, Any]:
        allowed = self.authorization.allowed_units(user)
        if not allowed and not user.is_superadmin:
            raise AuthorizationError("Forbidden")

        effective = normalize_overview_branches(branches)
        for code in effective:
            self.authorization.require_unit(user, code)

        resolved_status = self._resolve_status(status)
        month_start, month_end = current_month_bounds(self._today())
        resolved_start = (start_date or "").strip() or month_start
        resolved_end = (end_date or "").strip() or month_end
        self._validate_dates(resolved_start, resolved_end)

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

        resolved_sort_by = (sort_by or "").strip() or None
        if resolved_sort_by and resolved_sort_by not in ALLOWED_SORT:
            raise ValueError("Invalid sort_by")
        resolved_sort_dir = (sort_dir or "asc").strip().lower() or "asc"
        if resolved_sort_dir not in {"asc", "desc"}:
            raise ValueError("Invalid sort_dir")
        if not resolved_sort_by:
            resolved_sort_dir = "asc"

        token = user.access_token or ""
        if len(effective) == 1:
            payload = self._compose_single(
                access_token=token,
                branch=effective[0],
                status=resolved_status,
                start_date=resolved_start,
                end_date=resolved_end,
                page=page_number,
                page_size=size,
                sort_by=resolved_sort_by,
                sort_dir=resolved_sort_dir if resolved_sort_by else None,
            )
        else:
            payload = self._compose_consolidated(
                access_token=token,
                branches=effective,
                status=resolved_status,
                start_date=resolved_start,
                end_date=resolved_end,
                page=page_number,
                page_size=size,
                sort_by=resolved_sort_by,
                sort_dir=resolved_sort_dir if resolved_sort_by else "asc",
            )

        payload["applied_filters"] = {
            "branches": effective,
            "status": resolved_status,
            "start_date": resolved_start,
            "end_date": resolved_end,
            "page": page_number,
            "page_size": size,
            "sort_by": resolved_sort_by,
            "sort_dir": resolved_sort_dir if resolved_sort_by else None,
        }
        return payload

    def _resolve_status(self, status: str | None) -> str:
        if status is None or str(status).strip() == "":
            return DEFAULT_STATUS
        normalized = str(status).strip().lower()
        if normalized not in ALLOWED_STATUS:
            raise ValueError("Invalid status")
        return normalized

    def _validate_dates(self, start_date: str, end_date: str) -> None:
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError as exc:
            raise ValueError("Invalid date") from exc
        if start > end:
            raise ValueError("Invalid date range")

    def _compose_single(
        self,
        *,
        access_token: str,
        branch: str,
        status: str,
        start_date: str,
        end_date: str,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str | None,
    ) -> dict[str, Any]:
        panel = self.delpi_reads.get_purchase_order_otd_panel(
            access_token=access_token,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        lines = panel.get("lines") if isinstance(panel.get("lines"), dict) else {}
        items = [
            _project_line(row)
            for row in (lines.get("items") or [])
            if isinstance(row, dict)
        ]
        total = int(lines.get("total") or 0)
        size = int(lines.get("page_size") or page_size) or page_size
        total_pages = int(lines.get("total_pages") or 0)
        if total_pages == 0 and size:
            total_pages = (total + size - 1) // size if total else 0
        summary = panel.get("summary") if isinstance(panel.get("summary"), dict) else {}
        return {
            "branch": branch,
            "start_date": start_date,
            "end_date": end_date,
            "product_type": panel.get("product_type") or "MP",
            "summary": {
                "total_lines": int(summary.get("total_lines") or 0),
                "on_time_lines": int(summary.get("on_time_lines") or 0),
                "late_lines": int(summary.get("late_lines") or 0),
                "purchase_order_otd_pct": summary.get("purchase_order_otd_pct"),
                "late_percentage": float(summary.get("late_percentage") or 0.0),
            },
            "items": items,
            "page": int(lines.get("page") or page),
            "page_size": size,
            "total": total,
            "total_pages": total_pages,
        }

    def _compose_consolidated(
        self,
        *,
        access_token: str,
        branches: list[str],
        status: str,
        start_date: str,
        end_date: str,
        page: int,
        page_size: int,
        sort_by: str | None,
        sort_dir: str,
    ) -> dict[str, Any]:
        if set(branches) - set(OPERATIONAL_UNITS):
            raise ValueError("Unknown branch")

        all_items: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        for branch in branches:
            # Explicit concrete branch on every producer call — never omit.
            items, summary = self._fetch_all_for_branch(
                access_token=access_token,
                branch=branch,
                status=status,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_dir=sort_dir if sort_by else None,
            )
            all_items.extend(items)
            summaries.append(summary)

        all_items.sort(
            key=lambda row: _sort_key_for(row, sort_by=sort_by, sort_dir=sort_dir)
        )
        total = len(all_items)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        offset = (page - 1) * page_size
        window = all_items[offset : offset + page_size]
        return {
            "branch": "consolidated",
            "start_date": start_date,
            "end_date": end_date,
            "product_type": "MP",
            "summary": _merge_summaries(summaries),
            "items": window,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    def _fetch_all_for_branch(
        self,
        *,
        access_token: str,
        branch: str,
        status: str,
        start_date: str,
        end_date: str,
        sort_by: str | None,
        sort_dir: str | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        summary: dict[str, Any] = {
            "total_lines": 0,
            "on_time_lines": 0,
            "late_lines": 0,
            "purchase_order_otd_pct": None,
            "late_percentage": 0.0,
        }
        page = 1
        total = None
        while page <= _MAX_FETCH_PAGES:
            panel = self.delpi_reads.get_purchase_order_otd_panel(
                access_token=access_token,
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                status=status,
                page=page,
                page_size=PRODUCER_FETCH_PAGE_SIZE,
                sort_by=sort_by,
                sort_dir=sort_dir,
            )
            if page == 1 and isinstance(panel.get("summary"), dict):
                summary = panel["summary"]
            lines = panel.get("lines") if isinstance(panel.get("lines"), dict) else {}
            batch = [
                _project_line(row)
                for row in (lines.get("items") or [])
                if isinstance(row, dict)
            ]
            if total is None:
                total = int(lines.get("total") or 0)
            collected.extend(batch)
            if not batch or len(collected) >= (total or 0):
                break
            page += 1
        else:
            raise DelpiApiGatewayError(
                "api-delpi panel page budget exceeded",
                status_code=502,
            )
        return collected, summary
