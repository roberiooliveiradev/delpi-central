"""Assembler — payloads summary/items/ranking PCP."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.pcp_orders_request import (
    PcpOrdersFilterRequest,
    PcpOrdersItemsRequest,
    PcpOrdersRankingRequest,
)
from app.application.services.production.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.services.production.pcp_order_item_mapper import PcpOrderItemMapper
from app.domain.services.production.production_operational_summary_semantics_service import (
    ProductionOperationalSummarySemanticsService,
)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 6)


class PcpOrdersResponseAssembler:
    @staticmethod
    def to_summary(
        row: dict[str, Any],
        request: PcpOrdersFilterRequest,
    ) -> dict[str, Any]:
        branch = request.period.branch
        summary = {
            "total_orders": _as_int(row.get("total_orders")),
            "open_orders": _as_int(row.get("open_orders")),
            "delayed_orders": _as_int(row.get("delayed_orders")),
            "mother_orders": _as_int(row.get("mother_orders")),
            "planned_qty_sum": _as_float(row.get("planned_qty_sum")),
            "produced_qty_sum": _as_float(row.get("produced_qty_sum")),
            "pending_qty_sum": _as_float(row.get("pending_qty_sum")),
            "avg_days_late": _as_float(row.get("avg_days_late")),
            "max_days_late": _as_int(row.get("max_days_late")),
            "branch": branch,
            "branch_filter_applied": branch is not None,
            "consolidated_across_branches": (
                ProductionOperationalSummarySemanticsService.consolidated_for_product_aggregation(
                    branch=branch
                )
            ),
        }
        return {
            "filters": {
                **request.period.periodo_dict(),
                "actual_end_start": request.actual_end_start,
                "actual_end_end": request.actual_end_end,
                "op_key": request.op_key,
                "product_code": request.product_code,
                "warehouse": request.warehouse,
                "mother_only": request.mother_only,
                "open_only": request.open_only,
                "delayed_only": request.delayed_only,
            },
            "summary": summary,
        }

    @staticmethod
    def to_items(
        rows: list[dict[str, Any]],
        *,
        total: int,
        request: PcpOrdersItemsRequest,
    ) -> dict[str, Any]:
        items = PcpOrderItemMapper.map_items(rows)
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=items,
            extra={
                "filters": {
                    **request.period.periodo_dict(),
                    "op_key": request.op_key,
                    "product_code": request.product_code,
                    "mother_only": request.mother_only,
                    "open_only": request.open_only,
                    "delayed_only": request.delayed_only,
                },
                "sort": request.sort,
            },
        )

    @staticmethod
    def to_ranking(
        rows: list[dict[str, Any]],
        request: PcpOrdersRankingRequest,
    ) -> dict[str, Any]:
        items = []
        for index, row in enumerate(rows, start=1):
            item = {
                "rank": index,
                "total_orders": _as_int(row.get("total_orders")),
                "order_qty_sum": _as_float(row.get("order_qty_sum")),
                "reported_qty_sum": _as_float(row.get("reported_qty_sum")),
                "balance_sum": _as_float(row.get("balance_sum")),
                "avg_days_late": _as_float(row.get("avg_days_late")),
                "max_days_late": _as_int(row.get("max_days_late")),
            }
            for key in (
                "product_code",
                "product_description",
                "warehouse",
                "op_key",
            ):
                if key in row and row.get(key) is not None:
                    item[key] = str(row.get(key) or "").strip()
            items.append(item)
        return {
            "filters": request.period.periodo_dict(),
            "rank_by": request.rank_by,
            "metric": request.metric,
            "limit": request.limit,
            "items": items,
        }
