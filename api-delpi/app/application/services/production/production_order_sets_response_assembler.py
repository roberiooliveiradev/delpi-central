"""Assembler — payload dos conjuntos de ordens de produção incompletos."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.production_order_sets_request import (
    IncompleteOrderSetsRequest,
)
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.services.production.production_order_set_mapper import (
    ProductionOrderSetMapper,
)


class ProductionOrderSetsResponseAssembler:
    @staticmethod
    def to_incomplete_sets(
        rows: list[dict[str, Any]],
        *,
        summary_row: dict[str, Any] | None,
        request: IncompleteOrderSetsRequest,
    ) -> dict[str, Any]:
        items = ProductionOrderSetMapper.map_sets(rows)
        summary = ProductionOrderSetMapper.map_summary(summary_row)
        branch = request.branch
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=summary["incomplete_set_count"],
            items=items,
            extra={
                "filters": request.filters_dict(),
                "summary": {
                    **summary,
                    "branch": branch,
                    "branch_filter_applied": branch is not None,
                    "consolidated_across_branches": branch is None,
                },
            },
        )
