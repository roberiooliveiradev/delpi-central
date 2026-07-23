"""Use case — ranking de PIs apontados (últimos 6 meses por default) para programas de máquina."""

from __future__ import annotations

from datetime import datetime, timedelta
from math import ceil

from app.application.dto.production.list_machine_program_top_intermediates_request import (
    ListMachineProgramTopIntermediatesRequest,
)
from app.domain.ports.production.production_machine_programs_repository_port import (
    ProductionMachineProgramsRepositoryPort,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)

_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 100
# Ranking operacional: só os N mais produzidos (não listagem completa).
_TOP_LIMIT = 100
_DEFAULT_LOOKBACK_DAYS = 182  # ~6 meses


class ListProductionMachineProgramTopIntermediatesUseCase:
    def __init__(self, repository: ProductionMachineProgramsRepositoryPort):
        self._repository = repository

    def execute(self, request: ListMachineProgramTopIntermediatesRequest) -> dict:
        branch = str(request.branch or "").strip()
        if not branch:
            raise ValueError("Parâmetro branch (filial) é obrigatório.")

        period_start, period_end_exclusive = self._resolve_period(
            date_start=request.date_start,
            date_end=request.date_end,
        )

        page = max(1, int(request.page or 1))
        page_size = min(
            max(1, int(request.page_size or _DEFAULT_PAGE_SIZE)),
            _MAX_PAGE_SIZE,
        )
        search = (request.search or "").strip() or None
        offset = (page - 1) * page_size
        fetch_size = min(page_size, max(0, _TOP_LIMIT - offset))

        if fetch_size <= 0:
            _, raw_total = self._repository.fetch_top_intermediates(
                branch=branch,
                date_start=period_start,
                date_end_exclusive=period_end_exclusive,
                page=1,
                page_size=1,
                search=search,
            )
            items: list = []
            total = min(int(raw_total), _TOP_LIMIT)
        else:
            items, raw_total = self._repository.fetch_top_intermediates(
                branch=branch,
                date_start=period_start,
                date_end_exclusive=period_end_exclusive,
                page=page,
                page_size=fetch_size,
                search=search,
            )
            total = min(int(raw_total), _TOP_LIMIT)
            items = list(items)[:fetch_size]

        total_pages = ceil(total / page_size) if total > 0 else 0

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "summary": {
                "branch": branch,
                "branch_filter_applied": True,
                "consolidated_across_branches": False,
                "period_start": period_start,
                "period_end_exclusive": period_end_exclusive,
                "top_limit": _TOP_LIMIT,
                "is_complete": True,
            },
        }

    @staticmethod
    def _resolve_period(
        *,
        date_start: str | None,
        date_end: str | None,
    ) -> tuple[str, str]:
        if not date_start and not date_end:
            end = datetime.now().date()
            start = end - timedelta(days=_DEFAULT_LOOKBACK_DAYS)
            end_exclusive = (end + timedelta(days=1)).strftime("%Y%m%d")
            return start.strftime("%Y%m%d"), end_exclusive

        return ProtheusDateRangeService.resolve_closed_open_period(
            date_start=date_start,
            date_end=date_end,
        )
