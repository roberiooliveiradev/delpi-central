"""DTOs — ordens de produção PCP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.domain.production.pcp_orders_view_scope import (
    DEFAULT_ITEMS_SORT,
    DEFAULT_MONTHS_WINDOW,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RANKING_LIMIT,
    ITEMS_SORT_VALUES,
    MAX_MONTHS_WINDOW,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
    METRIC_ORDER_QTY,
    METRIC_VALUES,
    RANK_BY_VALUES,
    VALID_PCP_ORDERS_BRANCHES,
)


def _parse_iso_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _default_period_start(end: date, months_window: int = DEFAULT_MONTHS_WINDOW) -> date:
    offset = months_window - 1
    total = end.year * 12 + end.month - 1 - offset
    year = total // 12
    month = total % 12 + 1
    return date(year, month, 1)


def _months_inclusive(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _as_bool(value: bool | str | None) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "sim", "s"}:
        return True
    if text in {"0", "false", "no", "nao", "não", "n"}:
        return False
    raise ValueError(f"Valor booleano inválido: {value!r}")


@dataclass(frozen=True, slots=True)
class PcpOrdersPeriod:
    delivery_start: date
    delivery_end: date
    branch: str | None

    @classmethod
    def resolve(
        cls,
        *,
        branch: str | None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
    ) -> PcpOrdersPeriod:
        normalized_branch = str(branch or "").strip() or None
        if (
            normalized_branch is not None
            and normalized_branch not in VALID_PCP_ORDERS_BRANCHES
        ):
            raise ValueError('branch inválida. Use "01" ou "02".')

        parsed_start = _parse_iso_date(delivery_start)
        parsed_end = _parse_iso_date(delivery_end)
        if delivery_start and parsed_start is None:
            raise ValueError("delivery_start inválida. Use o formato YYYY-MM-DD.")
        if delivery_end and parsed_end is None:
            raise ValueError("delivery_end inválida. Use o formato YYYY-MM-DD.")

        if parsed_start is None and parsed_end is None:
            end = date.today()
            start = _default_period_start(end)
        elif parsed_start is None:
            end = parsed_end  # type: ignore[assignment]
            start = _default_period_start(end)
        elif parsed_end is None:
            start = parsed_start
            end = date.today()
        else:
            start, end = parsed_start, parsed_end

        if start > end:
            raise ValueError("delivery_start não pode ser posterior a delivery_end.")
        if _months_inclusive(start, end) > MAX_MONTHS_WINDOW:
            raise ValueError(
                f"Período máximo permitido: {MAX_MONTHS_WINDOW} meses."
            )
        return cls(delivery_start=start, delivery_end=end, branch=normalized_branch)

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            "delivery_start": self.delivery_start.isoformat(),
            "delivery_end": self.delivery_end.isoformat(),
            "branch": self.branch,
        }

    def periodo_dict(self) -> dict[str, str | None]:
        return {
            "delivery_start": self.delivery_start.isoformat(),
            "delivery_end": self.delivery_end.isoformat(),
            "branch": self.branch,
        }


@dataclass(frozen=True, slots=True)
class PcpOrdersFilterRequest:
    period: PcpOrdersPeriod
    actual_end_start: str | None = None
    actual_end_end: str | None = None
    op_key: str | None = None
    product_code: str | None = None
    warehouse: str | None = None
    mother_only: bool | None = None
    open_only: bool | None = None
    delayed_only: bool | None = None

    @classmethod
    def from_params(
        cls,
        *,
        period: PcpOrdersPeriod,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
        op_key: str | None = None,
        product_code: str | None = None,
        warehouse: str | None = None,
        mother_only: bool | str | None = None,
        open_only: bool | str | None = None,
        delayed_only: bool | str | None = None,
    ) -> PcpOrdersFilterRequest:
        ae_start = _parse_iso_date(actual_end_start)
        ae_end = _parse_iso_date(actual_end_end)
        if actual_end_start and ae_start is None:
            raise ValueError("actual_end_start inválida. Use o formato YYYY-MM-DD.")
        if actual_end_end and ae_end is None:
            raise ValueError("actual_end_end inválida. Use o formato YYYY-MM-DD.")
        if ae_start and ae_end and ae_start > ae_end:
            raise ValueError(
                "actual_end_start não pode ser posterior a actual_end_end."
            )
        return cls(
            period=period,
            actual_end_start=ae_start.isoformat() if ae_start else None,
            actual_end_end=ae_end.isoformat() if ae_end else None,
            op_key=(str(op_key).strip() or None) if op_key is not None else None,
            product_code=(str(product_code).strip() or None)
            if product_code is not None
            else None,
            warehouse=(str(warehouse).strip() or None)
            if warehouse is not None
            else None,
            mother_only=_as_bool(mother_only),
            open_only=_as_bool(open_only),
            delayed_only=_as_bool(delayed_only),
        )

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            **self.period.filter_kwargs(),
            "actual_end_start": self.actual_end_start,
            "actual_end_end": self.actual_end_end,
            "op_key": self.op_key,
            "product_code": self.product_code,
            "warehouse": self.warehouse,
            "mother_only": self.mother_only,
            "open_only": self.open_only,
            "delayed_only": self.delayed_only,
        }


@dataclass(frozen=True, slots=True)
class PcpOrdersItemsRequest(PcpOrdersFilterRequest):
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    sort: str = DEFAULT_ITEMS_SORT

    @classmethod
    def from_params(  # type: ignore[override]
        cls,
        *,
        period: PcpOrdersPeriod,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
        op_key: str | None = None,
        product_code: str | None = None,
        warehouse: str | None = None,
        mother_only: bool | str | None = None,
        open_only: bool | str | None = None,
        delayed_only: bool | str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort: str | None = None,
    ) -> PcpOrdersItemsRequest:
        base = PcpOrdersFilterRequest.from_params(
            period=period,
            actual_end_start=actual_end_start,
            actual_end_end=actual_end_end,
            op_key=op_key,
            product_code=product_code,
            warehouse=warehouse,
            mother_only=mother_only,
            open_only=open_only,
            delayed_only=delayed_only,
        )
        resolved_sort = (sort or DEFAULT_ITEMS_SORT).strip()
        if resolved_sort not in ITEMS_SORT_VALUES:
            raise ValueError(
                f"sort inválido. Use um de: {', '.join(ITEMS_SORT_VALUES)}."
            )
        resolved_page = max(1, int(page or 1))
        resolved_size = min(max(1, int(page_size or DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
        return cls(
            period=base.period,
            actual_end_start=base.actual_end_start,
            actual_end_end=base.actual_end_end,
            op_key=base.op_key,
            product_code=base.product_code,
            warehouse=base.warehouse,
            mother_only=base.mother_only,
            open_only=base.open_only,
            delayed_only=base.delayed_only,
            page=resolved_page,
            page_size=resolved_size,
            sort=resolved_sort,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class PcpOrdersRankingRequest(PcpOrdersFilterRequest):
    rank_by: str = "product"
    metric: str = METRIC_ORDER_QTY
    limit: int = DEFAULT_RANKING_LIMIT

    @classmethod
    def from_params(  # type: ignore[override]
        cls,
        *,
        period: PcpOrdersPeriod,
        rank_by: str,
        metric: str | None = None,
        limit: int | None = None,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
        op_key: str | None = None,
        product_code: str | None = None,
        warehouse: str | None = None,
        mother_only: bool | str | None = None,
        open_only: bool | str | None = None,
        delayed_only: bool | str | None = None,
    ) -> PcpOrdersRankingRequest:
        base = PcpOrdersFilterRequest.from_params(
            period=period,
            actual_end_start=actual_end_start,
            actual_end_end=actual_end_end,
            op_key=op_key,
            product_code=product_code,
            warehouse=warehouse,
            mother_only=mother_only,
            open_only=open_only,
            delayed_only=delayed_only,
        )
        resolved_rank = str(rank_by or "").strip()
        if resolved_rank not in RANK_BY_VALUES:
            raise ValueError(
                f"rank_by inválido. Use um de: {', '.join(RANK_BY_VALUES)}."
            )
        resolved_metric = str(metric or METRIC_ORDER_QTY).strip()
        if resolved_metric not in METRIC_VALUES:
            raise ValueError(
                f"metric inválida. Use um de: {', '.join(METRIC_VALUES)}."
            )
        resolved_limit = min(
            max(1, int(limit or DEFAULT_RANKING_LIMIT)), MAX_RANKING_LIMIT
        )
        return cls(
            period=base.period,
            actual_end_start=base.actual_end_start,
            actual_end_end=base.actual_end_end,
            op_key=base.op_key,
            product_code=base.product_code,
            warehouse=base.warehouse,
            mother_only=base.mother_only,
            open_only=base.open_only,
            delayed_only=base.delayed_only,
            rank_by=resolved_rank,
            metric=resolved_metric,
            limit=resolved_limit,
        )
