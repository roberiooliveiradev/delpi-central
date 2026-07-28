from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.lmp.lmp_dashboard_summary_response import (
    LMPDashboardSummaryResponse,
)
from app.application.services.lmp.lmp_dashboard_summary_cache import (
    get_or_set_cached_lmp_dashboard_summary,
    lmp_dashboard_summary_cache_key,
)
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    ListLMPDashboardUseCase,
)
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class GetLMPDashboardSummaryUseCase:
    """Legado alinhado ao loader `kpi` de `ListLMPDashboardUseCase` (paridade % prazo)."""

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository
        self._list_dashboard = ListLMPDashboardUseCase(repository)

    def execute(
        self,
        request: ListLMPRequest,
        *,
        include_avg_lead_time: bool = True,
    ) -> LMPDashboardSummaryResponse:
        listing_type = request.listing_type or "lmp"
        cache_key = lmp_dashboard_summary_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            include_avg_lead_time=include_avg_lead_time,
            include_qtd_pi=True,
        )

        def compute() -> LMPDashboardSummaryResponse:
            summary_request = ListLMPRequest(
                date_start=request.date_start,
                date_end=request.date_end,
                branch=request.branch,
                listing_type=listing_type,
            )
            summary = self._list_dashboard.execute_summary(
                summary_request,
                status_filter="Todos",
                summary_mode="kpi",
            )
            return LMPDashboardSummaryResponse(
                total_lmps=int(summary.get("total_lmps") or 0),
                percent_dentro_prazo=float(summary.get("percent_dentro_prazo") or 0.0),
                avg_lead_time=(
                    float(summary.get("avg_lead_time") or 0.0)
                    if include_avg_lead_time
                    else 0.0
                ),
            )

        return get_or_set_cached_lmp_dashboard_summary(cache_key, compute)
