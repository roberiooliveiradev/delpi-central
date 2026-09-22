"""Assembler — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.shared_structure_intermediates_request import (
    SharedStructureIntermediatesRequest,
)
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.services.production.shared_structure_intermediate_mapper import (
    SharedStructureIntermediateMapper,
)


class SharedStructureIntermediatesResponseAssembler:
    @staticmethod
    def to_paged_list(
        rows: list[dict[str, Any]],
        *,
        summary_row: dict[str, Any] | None,
        request: SharedStructureIntermediatesRequest,
    ) -> dict[str, Any]:
        items = SharedStructureIntermediateMapper.map_items(rows)
        summary = SharedStructureIntermediateMapper.map_summary(summary_row)
        branch = request.branch
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=summary["shared_intermediate_count"],
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
